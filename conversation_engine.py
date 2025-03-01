"""
AI Sales Assistant Conversation Engine
This module handles the conversation flow and response generation for the tourism sales assistant.
It integrates ChatGPT (via LangChain Community) and LlamaIndex.
Before running, create a file named .env in the same directory with the following content:
   OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
"""

from dotenv import load_dotenv
load_dotenv()  # This loads environment variables from .env

import re
import json
import logging
import random
import os
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
import time
import backoff
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests.exceptions
import openai

# Updated import statements from langchain-community
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# Import your database schema definitions
from database_schema import PriceDatabase, TourPackage, TourVariant, PriceOption, TransferOption

# Define available models in order of preference
OPENAI_MODELS = ["gpt-4.5", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if OpenAI API key is available and log it securely
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OpenAI API key not found! Make sure OPENAI_API_KEY is set in your .env file.")
else:
    masked_key = f"{api_key[:4]}...{api_key[-4:]}"
    logger.info(f"OpenAI API key loaded: {masked_key}")

# ---------------------------
# Conversation State Machine
# ---------------------------
class ConversationState(Enum):
    GREETING = "greeting"
    GATHERING_INFO = "gathering_info"
    RECOMMENDING = "recommending"
    PRESENTING_DETAILS = "presenting_details"
    HANDLING_OBJECTION = "handling_objection"
    BOOKING = "booking"
    UPSELLING = "upselling"
    CLOSING = "closing"

# ---------------------------
# Customer Profile
# ---------------------------
class CustomerProfile:
    def __init__(self):
        # Basic profile attributes
        self.emirate: Optional[str] = None
        self.group_size: Optional[int] = None
        self.children_count: int = 0
        self.children_ages: List[int] = []
        self.budget_preference: Optional[str] = None  # low, medium, high
        self.interests: List[str] = []
        self.selected_tour: Optional[str] = None
        self.selected_variant: Optional[str] = None
        self.name: Optional[str] = None
        self.language: str = "ru"  # Default language is Russian
        
        # Enhanced profile attributes
        self.age_group: Optional[str] = None  # e.g., "Young Adults (18-35)"
        self.travel_group_type: Optional[str] = None  # e.g., "Family", "Couple", "Solo"
        self.previous_bookings: List[Dict] = []
        self.interaction_history: List[Dict] = []
        self.engagement_score: float = 0.0
        self.objections_raised: List[str] = []
        self.price_sensitivity: Optional[str] = None  # e.g., "high", "medium", "low"
        self.last_interaction_time: Optional[datetime] = datetime.now()
        
        # Additional travel details
        self.travel_dates: Optional[Dict[str, datetime]] = None  # arrival and departure dates
        self.trip_duration: Optional[int] = None  # number of days in UAE

    def to_dict(self) -> Dict[str, Any]:
        return {
            # Basic attributes
            "emirate": self.emirate,
            "group_size": self.group_size,
            "children_count": self.children_count,
            "children_ages": self.children_ages,
            "budget_preference": self.budget_preference,
            "interests": self.interests,
            "selected_tour": self.selected_tour,
            "selected_variant": self.selected_variant,
            "name": self.name,
            "language": self.language,
            
            # Enhanced attributes
            "age_group": self.age_group,
            "travel_group_type": self.travel_group_type,
            "previous_bookings": self.previous_bookings,
            "engagement_score": self.engagement_score,
            "objections_raised": self.objections_raised,
            "price_sensitivity": self.price_sensitivity,
            "last_interaction_time": self.last_interaction_time.isoformat() if self.last_interaction_time else None,
            
            # Additional travel details
            "travel_dates": {k: v.isoformat() for k, v in self.travel_dates.items()} if self.travel_dates else None,
            "trip_duration": self.trip_duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerProfile':
        profile = cls()
        # Basic attributes
        profile.emirate = data.get("emirate")
        profile.group_size = data.get("group_size")
        profile.children_count = data.get("children_count", 0)
        profile.children_ages = data.get("children_ages", [])
        profile.budget_preference = data.get("budget_preference")
        profile.interests = data.get("interests", [])
        profile.selected_tour = data.get("selected_tour")
        profile.selected_variant = data.get("selected_variant")
        profile.name = data.get("name")
        profile.language = data.get("language", "ru")
        
        # Enhanced attributes
        profile.age_group = data.get("age_group")
        profile.travel_group_type = data.get("travel_group_type")
        profile.previous_bookings = data.get("previous_bookings", [])
        profile.engagement_score = data.get("engagement_score", 0.0)
        profile.objections_raised = data.get("objections_raised", [])
        profile.price_sensitivity = data.get("price_sensitivity")
        
        # Convert ISO date string back to datetime if available
        if data.get("last_interaction_time"):
            try:
                profile.last_interaction_time = datetime.fromisoformat(data["last_interaction_time"])
            except (ValueError, TypeError):
                profile.last_interaction_time = datetime.now()
        else:
            profile.last_interaction_time = datetime.now()
        
        # Additional travel details
        if data.get("travel_dates"):
            try:
                profile.travel_dates = {k: datetime.fromisoformat(v) for k, v in data["travel_dates"].items()}
            except (ValueError, TypeError):
                profile.travel_dates = None
        profile.trip_duration = data.get("trip_duration")
            
        return profile
    
    def add_interaction(self, interaction_type: str, details: Dict[str, Any]) -> None:
        """Record a new interaction to build customer history"""
        self.interaction_history.append({
            "type": interaction_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })
        self.last_interaction_time = datetime.now()
        self._update_engagement_score()
    
    def _update_engagement_score(self) -> None:
        """
        Calculate customer engagement score based on profile completeness
        and interaction history
        """
        # Base score from profile completeness
        profile_score = 0.0
        if self.emirate: profile_score += 1.0
        if self.group_size: profile_score += 1.0
        if self.interests: profile_score += min(len(self.interests) * 0.5, 2.0)
        if self.selected_tour: profile_score += 2.0
        
        # Recent activity score (interactions in the last 48 hours)
        recent_activity = 0.0
        two_days_ago = datetime.now() - timedelta(days=2)
        for interaction in self.interaction_history:
            try:
                interaction_time = datetime.fromisoformat(interaction["timestamp"])
                if interaction_time > two_days_ago:
                    recent_activity += 0.5
            except (ValueError, KeyError):
                pass
        
        # Cap recent activity score at 5.0
        recent_activity = min(recent_activity, 5.0)
        
        # Combined score (profile + recent activity)
        self.engagement_score = min(profile_score + recent_activity, 10.0)
    
    def infer_price_sensitivity(self) -> str:
        """Infer price sensitivity based on objections and interactions"""
        if "price_high" in self.objections_raised:
            return "high"
        elif self.budget_preference == "low":
            return "high"
        elif self.budget_preference == "high":
            return "low"
        elif self.selected_variant and "vip" in self.selected_variant:
            return "low"
        elif self.selected_variant and "premium" in self.selected_variant:
            return "medium"
        else:
            return "medium"  # Default to medium sensitivity

# ---------------------------
# Conversation Context
# ---------------------------
class ConversationContext:
    def __init__(self):
        self.state: ConversationState = ConversationState.GREETING
        self.customer: CustomerProfile = CustomerProfile()
        self.prev_messages: List[Dict[str, str]] = []
        self.last_recommendations: List[str] = []
        self.pending_questions: List[str] = []
        self.session_id: Optional[str] = None
    
    def add_message(self, role: str, content: str) -> None:
        self.prev_messages.append({"role": role, "content": content})
        
        # Record this interaction if it's from the user
        if role == "user" and content:
            self.customer.add_interaction("message", {"content": content})
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "customer": self.customer.to_dict(),
            "prev_messages": self.prev_messages,
            "last_recommendations": self.last_recommendations,
            "pending_questions": self.pending_questions,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        context = cls()
        context.state = ConversationState(data.get("state", ConversationState.GREETING.value))
        context.customer = CustomerProfile.from_dict(data.get("customer", {}))
        context.prev_messages = data.get("prev_messages", [])
        context.last_recommendations = data.get("last_recommendations", [])
        context.pending_questions = data.get("pending_questions", [])
        context.session_id = data.get("session_id")
        return context

# ---------------------------
# Response Generator
# ---------------------------
class ResponseGenerator:
    """
    Generates responses based on conversation context.
    It can use ChatGPT (via LangChain Community) and/or LlamaIndex for a more natural response.
    """
    def __init__(self, price_db: PriceDatabase, use_chatgpt: bool = False, use_llama_index: bool = False):
        self.price_db = price_db
        self.templates = self._load_templates()
        self.use_chatgpt = use_chatgpt
        self.use_llama_index = use_llama_index
        
        # Initialize enhanced components
        self.objection_handler = self._initialize_objection_handler()
        self.urgency_generator = self._initialize_urgency_generator()
        self.popular_excursions = self._initialize_popular_excursions()

        # Store the models we've tried and failed with
        self.failed_models = set()
        # Store the working model
        self.working_model = None

        if self.use_chatgpt:
            self._initialize_llm()

        if self.use_llama_index:
            # Comment out LlamaIndex functionality for now
            pass  # Skip LlamaIndex integration
    
    def _initialize_llm(self):
        """Initialize the LLM with fallback options"""
        # First, explicitly try GPT-4o as our preferred model
        try:
            logger.info("Attempting to initialize ChatOpenAI with preferred model: gpt-4o")
            self.llm = ChatOpenAI(
                model_name="gpt-4o",
                temperature=0.75,  # Slightly increased for more creative responses
                max_tokens=1000,   # Increased for more comprehensive responses
                request_timeout=40, # Increased timeout for more complex reasoning
                max_retries=2
            )
            
            # Test the model with a simple request
            try:
                logger.info(f"Testing connection to gpt-4o...")
                start_time = time.time()
                test_response = self.llm.invoke([
                    HumanMessage(content="Ответь коротко на русском: Что такое TripUAE?")
                ])
                elapsed = time.time() - start_time
                logger.info(f"✓ Model gpt-4o working (response time: {elapsed:.2f}s)")
                logger.info(f"Sample response: {test_response.content[:50]}...")
                self.working_model = "gpt-4o"
                return True
            except Exception as connection_error:
                logger.error(f"Failed to connect to preferred model gpt-4o: {str(connection_error)}")
                # Continue to fallback logic
        except Exception as e:
            logger.error(f"Failed to initialize preferred model gpt-4o: {str(e)}")
            # Continue to fallback logic
        
        # Fall back to other models in order of preference
        for model in OPENAI_MODELS[1:]:  # Skip gpt-4o as we already tried it
            if model in self.failed_models:
                continue
            
            try:
                logger.info(f"Attempting to initialize ChatOpenAI with model: {model}")
                self.llm = ChatOpenAI(
                    model_name=model,
                    temperature=0.7,
                    max_tokens=800,
                    request_timeout=30,  # Reduced timeout
                    max_retries=2       # Reduced retries as we handle them manually
                )
                
                # Test the model with a simple request
                try:
                    logger.info(f"Testing connection to {model}...")
                    start_time = time.time()
                    test_response = self.llm.invoke([HumanMessage(content="Hello")])
                    elapsed = time.time() - start_time
                    logger.info(f"✓ Model {model} working (response time: {elapsed:.2f}s)")
                    self.working_model = model
                    return True
                except Exception as connection_error:
                    logger.error(f"Failed to connect to {model}: {str(connection_error)}")
                    self.failed_models.add(model)
                    continue
                    
            except Exception as e:
                logger.error(f"Failed to initialize {model}: {str(e)}")
                self.failed_models.add(model)
                continue
        
        # If we get here, all models failed
        self.use_chatgpt = False
        logger.error("All OpenAI models failed to initialize. Falling back to template-based responses.")
        return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, 
                                       openai.APIError, 
                                       openai.APIConnectionError,
                                       openai.APITimeoutError)),
        reraise=True
    )
    def _generate_chatgpt_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response using ChatGPT with improved error handling and retry logic.
        """
        try:
            if not self.use_chatgpt or not hasattr(self, 'llm') or self.llm is None:
                logger.warning("ChatGPT not available or not initialized, using template-based response")
                return "Извините, в данный момент я не могу использовать ИИ для ответа. Пожалуйста, уточните, какая экскурсия вас интересует? (TUAE)"
            
            # Convert messages to langchain format
            lc_messages = []
            for msg in messages[-10:]:  # Limit to last 10 messages to reduce token count
                if msg["role"] == "user":
                    lc_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    lc_messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    # Handle system messages
                    lc_messages.append({"role": "system", "content": msg["content"]})
            
            # Generate response with timeout handling
            try:
                logger.info(f"Generating response using model: {self.working_model}")
                
                # Add performance logging
                start_time = time.time()
                response = self.llm.invoke(lc_messages)
                elapsed = time.time() - start_time
                
                # Log performance metrics
                token_count = len(' '.join([msg.content for msg in lc_messages if hasattr(msg, 'content')]).split())
                logger.info(f"Response generated in {elapsed:.2f}s (approx {token_count} tokens)")
                
                # Quality check logging
                response_length = len(response.content)
                logger.info(f"Response quality metrics: Length={response_length} chars, Model={self.working_model}")
                
                return response.content
                
            except Exception as e:
                logger.error(f"Error during response generation: {str(e)}")
                raise
            
        except openai.RateLimitError:
            logger.warning("OpenAI rate limit hit, using fallback response")
            return "Извините, сейчас я немного перегружена запросами. Пожалуйста, повторите вопрос через минуту или уточните, какая конкретно экскурсия вас интересует? (TUAE)"
        
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API connection error: {str(e)}")
            # Try to reinitialize with a different model
            if self.working_model:
                self.failed_models.add(self.working_model)
                if self._initialize_llm():
                    # If reinitialization succeeded, try again with the new model
                    return self._generate_chatgpt_response(messages)
            
            return "Извините, у меня временные проблемы с подключением. Пожалуйста, спросите меня позже или напишите конкретный вопрос об экскурсиях. (TUAE)"
            
        except Exception as e:
            logger.error(f"Error generating ChatGPT response: {str(e)}")
            return "Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, уточните, какая экскурсия вас интересует или какую информацию вы хотели бы получить? (TUAE)"
    
    def generate_response(self, context: ConversationContext, user_message: str) -> str:
        """
        Main method to generate responses with improved error handling.
        """
        try:
            # If ChatGPT is enabled but not initialized or failing, try to initialize it again
            if self.use_chatgpt and not hasattr(self, 'working_model'):
                self._initialize_llm()

            # Try to use ChatGPT for more natural responses if configured and working
            if self.use_chatgpt and hasattr(self, 'working_model') and self.working_model and user_message:
                # Prepare messages for ChatGPT
                messages = []
                
                # Add system prompt with instructions
                system_prompt = (
                    "Вы — Мария, менеджер туристической компании TripUAE. Ваша задача — помогать клиентам выбирать "
                    "и бронировать экскурсии в ОАЭ. Общайтесь дружелюбно и профессионально, используйте точные цены "
                    "из контекста разговора. Всегда предлагайте конкретные экскурсии, добавляйте элементы срочности "
                    "и завершайте ответ вопросом, стимулирующим бронирование."
                )
                messages.append({"role": "system", "content": system_prompt})
                
                # Add previous messages for context (limit to last 5 for efficiency)
                for msg in context.prev_messages[-5:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                
                # Add current user message
                messages.append({"role": "user", "content": user_message})
                
                try:
                    # Try to get response from ChatGPT
                    return self._generate_chatgpt_response(messages)
                except Exception as e:
                    logger.error(f"Error with ChatGPT response, falling back to template: {str(e)}")
                    # Fall back to template-based response on error
            
            # If ChatGPT is not used or failed, use template-based response generation
            # Generate basic response based on conversation state
            # ...existing code...

    def _initialize_popular_excursions(self):
        """Initialize the list of popular excursions to offer to undecided customers"""
        # ...existing code...

    def _initialize_objection_handler(self):
        """Initialize the objection handler with standard responses."""
        # ...existing code...
    
    def _initialize_urgency_generator(self):
        """Initialize the urgency generator with templates."""
        # ...existing code...

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        # ...existing code...

    def _handle_greeting(self, context: ConversationContext) -> str:
        """
        Sales-focused greeting that establishes Maria's identity and builds rapport
        before moving toward sales objectives.
        """
        # Get current time for personalized greeting
        current_hour = datetime.now().hour
        time_greeting = "Доброе утро" if 5 <= current_hour < 12 else "Добрый день" if 12 <= current_hour < 18 else "Добрый вечер"
        
        # Check if this appears to be a return visitor based on profile completeness or conversation history
        is_return_visitor = (
            context.customer.emirate is not None or 
            context.customer.group_size is not None or
            context.customer.interests or
            len(context.prev_messages) > 2
        )
        
        # Build a personalized greeting 
        if is_return_visitor:
            # Personalized greeting for return visitors
            if context.customer.name:
                return (
                    f"{time_greeting}, {context.customer.name}! Это Мария из компании TripUAE. 😊\n\n"
                    "Я очень рада снова вас видеть! У нас появились новые экскурсионные программы и специальные предложения "
                    f"на {self._get_current_month_name()} — скидки до 15% при раннем бронировании.\n\n"
                    f"Чем я могу помочь вам сегодня? Возможно, вас интересуют наши популярные экскурсии: "
                    f"сафари по пустыне (от 550 AED), VIP-тур по Дубаю (от 680 AED) или круиз с ужином (от 495 AED)?"
                )
            else:
                # Return visitor without name
                return (
                    f"{time_greeting}! Это Мария, ваш персональный консультант из TripUAE. 😊\n\n"
                    "Рада снова вас видеть! В этом месяце у нас действуют специальные акции со скидками до 15% и новые "
                    "экскурсионные программы, которые я с удовольствием вам представлю.\n\n"
                    "Что вас интересует в первую очередь: экскурсии по Дубаю, приключения в пустыне или, возможно, "
                    "билеты в парки развлечений? На многие популярные даты осталось всего несколько свободных мест."
                )
        else:
            # First-time visitor greeting - always introduce Maria properly
            return (
                f"{time_greeting}! Меня зовут Мария, я менеджер компании TripUAE. 😊\n\n"
                "Мы организуем незабываемые экскурсии по всем Эмиратам с профессиональными русскоговорящими гидами. "
                "В этом месяце действуют специальные предложения со скидкой до 15% при раннем бронировании.\n\n"
                "Какой формат отдыха вас привлекает больше всего: экскурсии по Дубаю (от 680 AED), сафари в пустыне (от 550 AED) "
                "или морские прогулки (от 495 AED)? Я помогу забронировать места до того, как они закончатся."
            )
    
    def _get_current_month_name(self) -> str:
        """Returns the current month name in Russian"""
        month_names = [
            "январь", "февраль", "март", "апрель", "май", "июнь",
            "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
        ]
        return month_names[datetime.now().month - 1]
    
    def _handle_gathering_info(self, context: ConversationContext, user_message: str) -> str:
        """
        Handle information gathering phase by asking targeted questions and 
        extracting user details.
        """
        # First, try to extract information from the user's message
        self._extract_information(context, user_message)
        
        # Determine what information is still missing and needs to be asked
        missing_info = self._determine_missing_info(context.customer)
        
        if not missing_info:
            # If we have all necessary info, move to recommendation state
            context.state = ConversationState.RECOMMENDING
            return self._handle_recommending(context)
        
        # Otherwise, ask for the highest priority missing information
        if "emirate" in missing_info:
            return self.templates["gather_info"]["emirate"]
        elif "travel_dates" in missing_info:
            return self.templates["gather_info"]["travel_dates"]
        elif "group_size" in missing_info:
            return self.templates["gather_info"]["group_size"]
        elif "children" in missing_info:
            return self.templates["gather_info"]["children"]
        elif "trip_duration" in missing_info:
            return self.templates["gather_info"]["trip_duration"]
        elif "interests" in missing_info:
            return self.templates["gather_info"]["interests"]
        else:
            # If nothing specific is missing but we're still in gathering state,
            # ask about interests to make better recommendations
            return self.templates["gather_info"]["interests"]
    
    def _determine_missing_info(self, customer: CustomerProfile) -> List[str]:
        """Determine what information is still missing from the customer profile"""
        missing_info = []
        
        if not customer.emirate:
            missing_info.append("emirate")
        
        if not customer.travel_dates or "arrival" not in customer.travel_dates:
            missing_info.append("travel_dates")
        
        if not customer.group_size:
            missing_info.append("group_size")
        
        # Only ask about children if we know there are adults
        if customer.group_size and customer.group_size > 0 and customer.children_count == 0 and not customer.children_ages:
            missing_info.append("children")
            
        if not customer.trip_duration:
            missing_info.append("trip_duration")
            
        if not customer.interests:
            missing_info.append("interests")
            
        return missing_info
    
    def _extract_information(self, context: ConversationContext, user_message: str) -> None:
        """Extract various pieces of information from the user message"""
        msg_lower = user_message.lower()
        
        # Extract emirate information
        emirate = self._extract_emirate(msg_lower)
        if emirate:
            context.customer.emirate = emirate
            
        # Extract group size
        group_size, children_count = self._extract_group_size(msg_lower)
        if group_size is not None:
            context.customer.group_size = group_size
        if children_count is not None:
            context.customer.children_count = children_count
            
        # Extract children ages
        children_ages = self._extract_children_ages(msg_lower)
        if children_ages:
            context.customer.children_ages = children_ages
            
        # Extract interests
        interests = self._extract_interests(msg_lower)
        if interests:
            # Add new interests to existing ones
            existing_interests = set(context.customer.interests)
            for interest in interests:
                existing_interests.add(interest)
            context.customer.interests = list(existing_interests)
            
        # Extract travel dates
        travel_dates = self._extract_travel_dates(msg_lower)
        if travel_dates:
            if not context.customer.travel_dates:
                context.customer.travel_dates = {}
            for key, date in travel_dates.items():
                context.customer.travel_dates[key] = date
                
        # Check if user has selected a tour
        selected_tour = self._check_tour_selection(msg_lower)
        if selected_tour:
            context.customer.selected_tour = selected_tour
        
        # Extract budget preference
        budget = self._extract_budget_preference(msg_lower)
        if budget:
            context.customer.budget_preference = budget
    
    def _extract_emirate(self, text: str) -> Optional[str]:
        """Extract emirate information from the user message"""
        # Define key phrases for different emirates
        dubai_patterns = [r"дубай", r"dubai", r"дубае"]
        abu_dhabi_patterns = [r"абу", r"даби", r"abu dhabi", r"абу-даби"]
        sharjah_patterns = [r"шарджа", r"шардж", r"sharjah"]
        ras_al_khaimah_patterns = [r"рас-эль-хайма", r"рас аль", r"ras al khaimah", r"рак", r"rak"]
        fujairah_patterns = [r"фуджейра", r"фуджа", r"fujairah"]
        ajman_patterns = [r"аджман", r"ajman"]
        
        # Check for matches
        if any(re.search(pattern, text) for pattern in dubai_patterns):
            return "dubai"
        elif any(re.search(pattern, text) for pattern in abu_dhabi_patterns):
            return "abu_dhabi"
        elif any(re.search(pattern, text) for pattern in sharjah_patterns):
            return "sharjah"
        elif any(re.search(pattern, text) for pattern in ras_al_khaimah_patterns):
            return "rak"
        elif any(re.search(pattern, text) for pattern in fujairah_patterns):
            return "fujairah"
        elif any(re.search(pattern, text) for pattern in ajman_patterns):
            return "ajman"
            
        return None
    
    def _extract_group_size(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract information about group size and children from the user message"""
        # Initialize group size and children count
        group_size = None
        children_count = None
        
        # Patterns for numbers in Russian and English
        number_pattern = r"(\d+|один|два|три|четыре|пять|шесть|семь|восемь|девять|десять|one|two|three|four|five|six|seven|eight|nine|ten)"
        
        # Match patterns for group size
        group_patterns = [
            rf"(всего|нас|группа|человек|взрослых|adults|people|group).+{number_pattern}",
            rf"{number_pattern}.+(человек|взрослых|adults|people)"
        ]
        
        # Match patterns for children
        child_patterns = [
            rf"(детей|ребенок|ребёнок|ребенка|дети|child|children).+{number_pattern}",
            rf"{number_pattern}.+(детей|ребенок|ребёнок|ребенка|дети|child|children)"
        ]
        
        # Process group size
        for pattern in group_patterns:
            matches = re.search(pattern, text)
            if matches:
                number_string = matches.group(2) if len(matches.groups()) > 1 else matches.group(1)
                group_size = self._convert_word_to_number(number_string)
                break
        
        # Process children count
        for pattern in child_patterns:
            matches = re.search(pattern, text)
            if matches:
                number_string = matches.group(2) if len(matches.groups()) > 1 else matches.group(1)
                children_count = self._convert_word_to_number(number_string)
                break
        
        # If we have children but no group size, assume at least 1 adult
        if group_size is None and children_count is not None:
            group_size = 1 + children_count
        
        return group_size, children_count
    
    def _extract_children_ages(self, text: str) -> List[int]:
        """Extract ages of children from the user message"""
        children_ages = []
        
        # Pattern to match ages
        age_pattern = r"(\d+)\s*(год|года|лет|годик|годика|годиков|year|years)"
        
        # Find all ages mentioned
        matches = re.finditer(age_pattern, text)
        for match in matches:
            try:
                age = int(match.group(1))
                if 0 <= age <= 17:  # Only consider ages 0-17 as children
                    children_ages.append(age)
            except ValueError:
                continue
                
        return children_ages
    
    def _extract_interests(self, text: str) -> List[str]:
        """Extract customer interests from the user message"""
        interests = []
        
        # Define interest categories with related keywords
        interest_keywords = {
            "beach": [r"пляж", r"море", r"океан", r"пляжный", r"beach", r"sea", r"ocean"],
            "desert": [r"пустын", r"сафари", r"джип", r"верблюд", r"desert", r"safari", r"dune", r"camel"],
            "culture": [r"музей", r"культур", r"истор", r"мечеть", r"museum", r"culture", r"history", r"mosque"],
            "adventure": [r"приключен", r"экстрим", r"адренал", r"adventure", r"extreme", r"adrenaline"],
            "luxury": [r"люкс", r"vip", r"премиум", r"роскош", r"luxury", r"premium"],
            "shopping": [r"шопинг", r"магазин", r"shopping", r"mall", r"shop"],
            "family": [r"семейн", r"дети", r"детск", r"ребен", r"family", r"kids", r"children"],
            "nightlife": [r"ночная жизнь", r"клуб", r"диско", r"nightlife", r"club"],
            "cruise": [r"круиз", r"яхт", r"лодк", r"cruise", r"yacht", r"boat"],
            "theme_park": [r"парк развлечен", r"аттракцион", r"theme park", r"attraction", r"ferrari world", r"aquapark"]
        }
        
        # Check for specific tour mentions
        tour_mentions = {
            "burj_khalifa": [r"бурдж[ -]халифа", r"burj[- ]khalifa", r"башня", r"небоскреб", r"skyscraper"],
            "desert_safari": [r"сафари", r"safari", r"пустын", r"desert", r"джип[ -]сафари", r"jeep safari"],
            "dubai_tour": [r"тур по дубаю", r"обзорный", r"экскурсия по дубаю", r"dubai tour", r"city tour"],
            "abu_dhabi_tour": [r"абу[ -]даби", r"мечеть", r"шейх[ -]зайд", r"sheikh zayed", r"абу даби"],
            "marina_cruise": [r"круиз", r"марина", r"яхт", r"cruise", r"yacht", r"dubai marina"],
            "miracle_garden": [r"сад", r"garden", r"miracle garden"],
            "palm_jumeirah": [r"пальм", r"джумейр", r"palm jumeirah", r"atlantis"],
            "global_village": [r"глобал[ -]вилладж", r"global village"]
        }
        
        # Check for interests
        for interest, keywords in interest_keywords.items():
            if any(re.search(keyword, text) for keyword in keywords):
                interests.append(interest)
                
        # Check for specific tours
        for tour, keywords in tour_mentions.items():
            if any(re.search(keyword, text) for keyword in keywords):
                interests.append(tour)
                
        return interests
    
    def _extract_travel_dates(self, text: str) -> Dict[str, datetime]:
        """Extract travel dates from the user message"""
        travel_dates = {}
        
        # Pattern to match dates in different formats
        date_patterns = [
            # DD.MM or DD.MM.YYYY
            (r"(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?", "%d.%m.%Y"),
            # DD/MM or DD/MM/YYYY
            (r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", "%d/%m/%Y"),
            # Month names in Russian
            (r"(\d{1,2}) (января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)(?: (\d{2,4}))?", "%d %B %Y"),
            # Month names in English
            (r"(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December)(?: (\d{2,4}))?", "%d %B %Y", "en")
        ]
        
        # Keywords for arrival and departure
        arrival_keywords = [r"приезд", r"прилет", r"приехать", r"прибыть", r"arrival", r"arrive", r"check[ -]in"]
        departure_keywords = [r"отъезд", r"вылет", r"уехать", r"отбыть", r"departure", r"leave", r"check[ -]out"]
        
        # Process the text for dates
        for pattern, format_str, *lang in date_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                try:
                    # Process date parts
                    day = int(match.group(1))
                    
                    # Handle month
                    if len(match.groups()) >= 2 and match.group(2):
                        if match.group(2).isdigit():
                            month = int(match.group(2))
                        else:
                            # Convert month name to number
                            month_name = match.group(2)
                            month_names = {
                                "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
                                "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
                                "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                                "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
                            }
                            month = month_names.get(month_name.lower(), 1)
                    else:
                        month = 1  # Default to January
                    
                    # Handle year
                    current_year = datetime.now().year
                    if len(match.groups()) >= 3 and match.group(3):
                        year = int(match.group(3))
                        if year < 100:  # Handle 2-digit years
                            year += 2000 if year < 30 else 1900
                    else:
                        # If no year provided, assume current or next year depending on month
                        current_month = datetime.now().month
                        if month < current_month:
                            year = current_year + 1
                        else:
                            year = current_year
                    
                    # Create date object
                    date_obj = datetime(year, month, day)
                    
                    # Determine if it's arrival or departure
                    context_start = max(0, match.start() - 20)
                    context_end = min(len(text), match.end() + 20)
                    context_text = text[context_start:context_end].lower()
                    
                    if any(re.search(keyword, context_text) for keyword in arrival_keywords):
                        travel_dates["arrival"] = date_obj
                    elif any(re.search(keyword, context_text) for keyword in departure_keywords):
                        travel_dates["departure"] = date_obj
                    else:
                        # If no clear indicator, assume it's arrival if we don't have one yet
                        if "arrival" not in travel_dates:
                            travel_dates["arrival"] = date_obj
                        # Otherwise, if we have arrival but no departure, assume it's departure
                        elif "departure" not in travel_dates:
                            travel_dates["departure"] = date_obj
                
                except (ValueError, IndexError):
                    continue
        
        # Calculate trip duration if we have both arrival and departure
        if "arrival" in travel_dates and "departure" in travel_dates:
            try:
                duration = (travel_dates["departure"] - travel_dates["arrival"]).days
                if duration > 0:
                    travel_dates["trip_duration"] = duration
            except Exception:
                pass
                
        return travel_dates
    
    def _extract_budget_preference(self, text: str) -> Optional[str]:
        """Extract budget preference from the user message"""
        # Keywords for different budget levels
        budget_keywords = {
            "low": [r"бюджет", r"экономия", r"недорого", r"дешев", r"низк", r"budget", r"cheap", r"economy", r"saving"],
            "medium": [r"средн", r"стандарт", r"medium", r"standard", r"normal"],
            "high": [r"дорого", r"vip", r"люкс", r"премиум", r"престиж", r"роскош", r"high", r"luxury", r"premium", r"expensive"]
        }
        
        # Check for budget indicators
        for budget, keywords in budget_keywords.items():
            if any(re.search(keyword, text) for keyword in keywords):
                return budget
                
        return None
    
    def _convert_word_to_number(self, word: str) -> int:
        """Convert a numeric word (in Russian or English) to a number"""
        word = word.lower()
        word_to_number = {
            "один": 1, "одного": 1, "одному": 1, "одним": 1, "одном": 1,
            "два": 2, "две": 2, "двух": 2, "двое": 2,
            "три": 3, "трех": 3, "трём": 3, "троих": 3,
            "четыре": 4, "четырех": 4, "четверых": 4,
            "пять": 5, "пяти": 5, "пятеро": 5,
            "шесть": 6, "шести": 6, "шестеро": 6,
            "семь": 7, "семи": 7, "семеро": 7,
            "восемь": 8, "восьми": 8, "восьмеро": 8,
            "девять": 9, "девяти": 9, "девятеро": 9,
            "десять": 10, "десяти": 10, "десятеро": 10,
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
        
        # If the word is a digit string, convert directly
        if word.isdigit():
            return int(word)
            
        # Otherwise, look up in dictionary
        return word_to_number.get(word, 0)
    
    def _check_tour_selection(self, text: str) -> Optional[str]:
        """Check if user has selected a specific tour"""
        # Define patterns for different tours
        tour_patterns = {
            "desert_safari": [r"сафари", r"пустын", r"desert safari", r"safari"],
            "dubai_city_tour": [r"обзор", r"дубай", r"город", r"city tour", r"dubai tour", r"тур по дубаю"],
            "night_cruise": [r"круиз", r"марин", r"ночн", r"cruise", r"marina", r"ужин", r"dinner"],
            "abu_dhabi_tour": [r"абу[ -]даби", r"зайд", r"мечеть", r"abu dhabi", r"sheikh zayed", r"абу-даби"],
            "ferrari_world": [r"феррари", r"ferrari"]
        }
        
        # Direct mentions like "I want the desert safari" or "book the city tour"
        booking_prefixes = [r"хочу", r"интересует", r"бронь", r"заказ", r"выбираю", r"хотим", r"want", r"book", r"choose", r"interested"]
        
        for tour_id, patterns in tour_patterns.items():
            # Check for direct selection phrases
            for prefix in booking_prefixes:
                for pattern in patterns:
                    selection_pattern = fr"{prefix}.*{pattern}"
                    if re.search(selection_pattern, text):
                        return tour_id
            
            # Check for strong indication of interest in this specific tour
            if all(re.search(pattern, text) for pattern in patterns) or \
               any(re.search(fr"(^|[,.!? ]){pattern}($|[,.!? ])", text) for pattern in patterns):
                return tour_id
                
        return None

    def _handle_undecided_customer(self, context: ConversationContext) -> str:
        """Handle customers who haven't specified clear preferences"""
        # Start with introduction to popular options
        response = self.templates["undecided_customer"]["intro"]
        
        # Add follow-up question
        response += "\n\n" + self.templates["undecided_customer"]["follow_up"]
        
        return response
    
    def _get_recommendations(self, customer: CustomerProfile) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Get personalized tour recommendations based on customer profile.
        Returns list of tuples (tour_id, score, detailed_info).
        """
        recommendations = []
        
        # Define tours with their base details
        tours = {
            "desert_safari": {
                "name": "Сафари по пустыне с ужином и шоу",
                "description": "Захватывающее приключение в золотых песках пустыни",
                "starting_price": 550,
                "includes_transfer": True,
                "includes_meals": True,
                "duration": "5.5 часов (15:30-21:00)",
                "tags": ["adventure", "desert", "family", "photo", "dinner"]
            },
            "dubai_city_tour": {
                "name": "VIP-экскурсия по Дубаю с Бурдж Халифа",
                "description": "Увлекательное путешествие по всем знаковым достопримечательностям города",
                "starting_price": 680,
                "includes_transfer": True,
                "includes_meals": True,
                "duration": "8 часов (9:00-17:00)",
                "tags": ["city", "culture", "family", "photo", "burj_khalifa"]
            },
            "night_cruise": {
                "name": "Ночной круиз по Дубай Марине с ужином",
                "description": "Романтический вечер на роскошной яхте с панорамными видами на ночной Дубай",
                "starting_price": 495,
                "includes_transfer": True,
                "includes_meals": True,
                "duration": "2.5 часа (19:30-22:00)"
            }
        }
        
        # Calculate scores based on customer profile
        for tour_id, tour_info in tours.items():
            score = 0.0
            
            # Match interests
            for tag in tour_info.get("tags", []):
                if tag in customer.interests:
                    score += 1.0
            
            # Match budget preference
            if customer.budget_preference == "low" and tour_info["starting_price"] <= 500:
                score += 1.0
            elif customer.budget_preference == "medium" and 500 < tour_info["starting_price"] <= 1000:
                score += 1.0
            elif customer.budget_preference == "high" and tour_info["starting_price"] > 1000:
                score += 1.0
            
            # Match group size
            if customer.group_size and customer.group_size > 2 and "family" in tour_info.get("tags", []):
                score += 1.0
            
            # Match travel dates
            if customer.travel_dates and "arrival" in customer.travel_dates and "departure" in customer.travel_dates:
                duration = (customer.travel_dates["departure"] - customer.travel_dates["arrival"]).days
                if duration >= 3 and "adventure" in tour_info.get("tags", []):
                    score += 1.0
            
            recommendations.append((tour_id, score, tour_info))
        
        # Sort recommendations by score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations

    def _determine_intent(self, message: str) -> Dict[str, bool]:
        """
        Analyze user message to determine conversation intent.
        Uses regex pattern matching for nuanced intent detection.
        
        Args:
            message (str): User's input message
        
        Returns:
            Dict[str, bool]: Dictionary of detected intents
        """
        message_lower = message.lower()
        intents = {
            "booking": bool(re.search(r"\b(бронировать|забронировать|book|reserve|reservation)\b", message_lower)),
            "objection": bool(re.search(r"\b(дорого|цена\s?высок|слишком|expensive|cost|дешевле|cheaper)\b", message_lower)),
            "pricing_inquiry": bool(re.search(r"\b(стоимость|цена|price|cost|сколько стоит)\b", message_lower)),
            "greeting": bool(re.search(r"\b(привет|здравствуй|добрый|hello|hi|good)\b", message_lower)),
            "gratitude": bool(re.search(r"\b(спасибо|благодар|thank|thanks)\b", message_lower)),
            "tour_inquiry": bool(re.search(r"\b(тур|экскурси|посмотреть|посетить|tour|excursion|visit)\b", message_lower)),
            "confirmation": bool(re.search(r"\b(да|конечно|верно|согласен|yes|sure|correct|agree)\b", message_lower)),
            "rejection": bool(re.search(r"\b(нет|не|never|no)\b", message_lower))
        }
        logger.info("Detected intents: %s", intents)
        return intents

    # The following methods use our existing extraction methods but adapt them to 
    # the new method signatures that update the context directly
    
    def _extract_emirate_context(self, context: ConversationContext, message: str) -> None:
        """
        Extract emirate information from user message and update context.
        Supports multiple language variants and flexible matching.
        
        Args:
            context (ConversationContext): Current conversation context
            message (str): User's input message
        """
        emirate = self._extract_emirate(message.lower())
        if emirate:
            context.customer.emirate = emirate
            logger.info("Extracted emirate: %s", emirate)

    def _extract_group_size_context(self, context: ConversationContext, message: str) -> None:
        """
        Extract group size and children information from user message and update context.
        Handles complex linguistic variations in Russian and English.
        
        Args:
            context (ConversationContext): Current conversation context
            message (str): User's input message
        """
        group_size, children_count = self._extract_group_size(message.lower())
        if group_size is not None:
            context.customer.group_size = group_size
            logger.info("Extracted group size: %s", group_size)
        
        if children_count is not None:
            context.customer.children_count = children_count
            logger.info("Extracted children count: %s", children_count)
        
        # Extract children ages using the existing method
        children_ages = self._extract_children_ages(message.lower())
        if children_ages:
            context.customer.children_ages = children_ages
            logger.info("Extracted children ages: %s", children_ages)

    def _extract_interests_context(self, context: ConversationContext, message: str) -> None:
        """
        Extract user interests from the message and update context.
        Supports multiple interest categories with flexible matching.
        
        Args:
            context (ConversationContext): Current conversation context
            message (str): User's input message
        """
        interests = self._extract_interests(message.lower())
        if interests:
            # Update existing interests in context
            existing_interests = set(context.customer.interests)
            for interest in interests:
                existing_interests.add(interest)
            context.customer.interests = list(existing_interests)
            logger.info("Extracted interests: %s", interests)

    def _check_tour_selection_context(self, context: ConversationContext, message: str) -> None:
        """
        Identify specific tour and variant selection from user message and update context.
        
        Args:
            context (ConversationContext): Current conversation context
            message (str): User's input message
        """
        selected_tour = self._check_tour_selection(message.lower())
        if selected_tour:
            context.customer.selected_tour = selected_tour
            context.state = ConversationState.PRESENTING_DETAILS
            logger.info("Selected tour: %s", selected_tour)
        
        # Variant selection logic
        if context.customer.selected_tour:
            variant_patterns = {
                "standard": r"\b(стандарт|basic)\b",
                "premium": r"\b(премиум|premium|улучшенн)\b",
                "vip": r"\b(вип|vip|люкс|luxury)\b"
            }
            for variant_id, pattern in variant_patterns.items():
                if re.search(pattern, message.lower()):
                    context.customer.selected_variant = variant_id
                    logger.info("Selected variant: %s", variant_id)
                    break
    
    def _update_conversation_state(self, context: ConversationContext, message: str) -> None:
        """
        Update conversation state based on detected intents and context.
        
        Args:
            context (ConversationContext): Current conversation context
            message (str): User's input message
        """
        intents = self._determine_intent(message)
        
        # Update customer information based on message
        self._extract_emirate_context(context, message)
        self._extract_group_size_context(context, message)
        self._extract_interests_context(context, message)
        self._check_tour_selection_context(context, message)
        
        # State transitions based on intents and context
        if context.state == ConversationState.GREETING:
            # After greeting, always move to gathering info
            context.state = ConversationState.GATHERING_INFO
            
        elif context.state == ConversationState.GATHERING_INFO:
            # If we have enough information, move to recommendations
            if (context.customer.emirate and context.customer.group_size and 
                (context.customer.interests or context.customer.selected_tour)):
                context.state = ConversationState.RECOMMENDING
            
        elif context.state == ConversationState.RECOMMENDING:
            # If customer selected a tour, show details
            if context.customer.selected_tour:
                context.state = ConversationState.PRESENTING_DETAILS
            # If objection detected, handle it
            elif intents["objection"]:
                context.state = ConversationState.HANDLING_OBJECTION
                
        elif context.state == ConversationState.PRESENTING_DETAILS:
            # If booking intent detected, move to booking
            if intents["booking"] or intents["confirmation"]:
                context.state = ConversationState.BOOKING
            # If objection detected, handle it
            elif intents["objection"]:
                context.state = ConversationState.HANDLING_OBJECTION
                
        elif context.state == ConversationState.HANDLING_OBJECTION:
            # If objection resolved (confirmation or booking intent)
            if intents["confirmation"] or intents["booking"]:
                if context.customer.selected_tour:
                    context.state = ConversationState.BOOKING
                else:
                    context.state = ConversationState.RECOMMENDING
                    
        elif context.state == ConversationState.BOOKING:
            # After booking, try upselling
            if intents["confirmation"] or re.search(r"\b(дата|date|когда|when)\b", message.lower()):
                context.state = ConversationState.UPSELLING
                
        elif context.state == ConversationState.UPSELLING:
            # After upselling, move to closing
            if intents["confirmation"] or intents["rejection"]:
                context.state = ConversationState.CLOSING
        
        logger.info("State updated to: %s", context.state)

    def _handle_recommending(self, context: ConversationContext) -> str:
        """
        Generate personalized tour recommendations based on customer profile.
        Incorporates urgency and availability to drive conversions.
        
        Args:
            context (ConversationContext): Current conversation context
        
        Returns:
            str: Personalized recommendation response
        """
        # If we don't have enough information to make proper recommendations,
        # handle as an undecided customer
        if not context.customer.interests and not context.customer.selected_tour:
            if context.customer.emirate is None and context.customer.group_size is None:
                return self._handle_undecided_customer(context)
        
        # Get personalized recommendations based on customer profile
        recommendations = self._get_recommendations(context.customer)
        
        # Store recommendations for later reference
        context.last_recommendations = [rec[0] for rec in recommendations[:3]]
        
        # Build the recommendation response
        response = self.templates["recommendations"]["intro"] + "\n\n"
        
        # Add top 3 recommendations with personalized details
        for tour_id, score, tour_info in recommendations[:3]:
            if tour_id in self.templates["recommendations"]:
                # Add recommendation with urgency element
                rec_text = self.templates["recommendations"][tour_id]
                
                # Add personalization based on customer profile
                if context.customer.group_size and context.customer.group_size > 4:
                    rec_text += f" Для группы из {context.customer.group_size} человек предоставляется скидка 10%!"
                
                # Add urgency element
                slots_left = random.randint(3, 9)
                rec_text += f" 🔥 Осталось всего {slots_left} мест на ближайшие даты!"
                
                response += rec_text + "\n\n"
            
        # Add call to action from random selection
        if self.templates.get("call_to_action") and isinstance(self.templates["call_to_action"], list):
            response += random.choice(self.templates["call_to_action"])
        else:
            response += "Какой вариант вас заинтересовал? Я с удовольствием расскажу подробнее и помогу с бронированием."
            
        return response

    def _handle_presenting_details(self, context: ConversationContext) -> str:
        """
        Present detailed information about selected tour with emotional elements.
        Focuses on building desire and adding urgency to drive conversion.
        
        Args:
            context (ConversationContext): Current conversation context
        
        Returns:
            str: Detailed tour information with sales elements
        """
        selected_tour = context.customer.selected_tour
        
        # If no tour selected, recommend options
        if not selected_tour:
            return self._handle_recommending(context)
            
        # Get tour details from templates
        tour_details = self.templates.get("tour_details", {}).get(selected_tour)
        if not tour_details:
            # Fallback if tour details not found
            return (
                f"У нас есть отличный выбор для вас! "
                f"Могу я уточнить, какой аспект {selected_tour} вас интересует больше всего? "
                f"Стоимость, включенные услуги или расписание?"
            )
            
        # Build the detailed response
        response = ""
        
        # Include emotional introduction if available
        if "emotional_intro" in tour_details:
            response += tour_details["emotional_intro"] + "\n\n"
            
        # Include detailed program information
        if "program" in tour_details:
            response += tour_details["program"] + "\n\n"
            
        # Present variant options if available
        if "variant_intro" in tour_details and hasattr(self, 'price_db') and self.price_db:
            response += tour_details["variant_intro"] + "\n\n"
            
            # Get tour from price database if available
            tour = self.price_db.get_tour(selected_tour)
            
            if tour and tour.variants:
                # If specific variant selected, show its details
                if context.customer.selected_variant and context.customer.selected_variant in tour.variants:
                    variant = tour.variants[context.customer.selected_variant]
                    response += self._format_variant_details(selected_tour, context.customer.selected_variant, variant, context.customer)
                else:
                    # Show available variants (limited to 3 for readability)
                    variants_shown = 0
                    for variant_id, variant in tour.variants.items():
                        # Skip private variants if group size doesn't match
                        if "private" in variant_id and (context.customer.group_size is None or context.customer.group_size > variant.max_participants):
                            continue
                            
                        response += self._format_variant_details(selected_tour, variant_id, variant, context.customer) + "\n\n"
                        variants_shown += 1
                        if variants_shown >= 3:
                            break
            else:
                # Fallback to template-based tour variants without database
                response += "К сожалению, детали вариантов тура временно недоступны. Пожалуйста, свяжитесь с нами для уточнения.\n\n"
        
        # Add urgency element
        dates = ["пятницу", "субботу", "воскресенье"]
        slots = random.randint(3, 7)
        response += f"🔥 На ближайшие {dates[random.randint(0, 2)]} и выходные осталось всего {slots} мест! "
        response += "Рекомендую бронировать заранее, так как места закрываются очень быстро.\n\n"
            
        # Add booking call-to-action
        response += "Желаете забронировать этот тур? На какую дату вам удобно?"
        
        return response

    def _handle_objection(self, context: ConversationContext) -> str:
        """
        Handle customer objections with effective responses.
        Addresses price, uncertainty, and alternatives to overcome resistance.
        
        Args:
            context (ConversationContext): Current conversation context
        
        Returns:
            str: Objection handling response
        """
        # Try to detect the type of objection from recent messages
        objection_type = "thinking"  # Default objection type
        
        # Check the last few messages for objection patterns
        recent_messages = [msg["content"].lower() for msg in context.prev_messages[-3:] if msg["role"] == "user"]
        for msg in recent_messages:
            # Check price objections
            if any(re.search(pattern, msg) for pattern in self.objection_handler["detection_patterns"]["price_high"]):
                objection_type = "price_high"
                if "price_high" not in context.customer.objections_raised:
                    context.customer.objections_raised.append("price_high")
                break
                
            # Check for pricing inquiries
            elif any(re.search(pattern, msg) for pattern in self.objection_handler["detection_patterns"]["pricing_inquiry"]):
                objection_type = "pricing_inquiry"
                break
                
            # Check for "thinking about it" objections
            elif any(re.search(pattern, msg) for pattern in self.objection_handler["detection_patterns"]["thinking"]):
                objection_type = "thinking"
                break
        
        # Get the appropriate response template
        response = self.objection_handler["responses"].get(objection_type, self.objection_handler["responses"]["alternatives"])
        
        # Personalize the response if it's a date template
        if "{date}" in response:
            # Calculate a date 5-7 days in the future
            future_days = random.randint(5, 7)
            future_date = (datetime.now() + timedelta(days=future_days)).strftime("%d.%m.%Y")
            response = response.replace("{date}", future_date)
            
        # Add recommendation if no tour selected yet
        if not context.customer.selected_tour and objection_type == "price_high":
            # Suggest cheaper alternatives
            response += "\n\nВот несколько наших самых популярных экскурсий по выгодным ценам:\n"
            response += "• Обзорная экскурсия по Дубаю (групповая): 450 AED\n"
            response += "• Круиз с ужином по Дубай Марине: 495 AED\n"
            response += "• Посещение аквариума в Дубай Молле: 130 AED\n\n"
            response += "Что из этого вас больше всего заинтересовало?"
            
        return response

    def _handle_booking(self, context: ConversationContext) -> str:
        """
        Process booking request and confirm details.
        Focuses on creating smooth path to completed booking.
        
        Args:
            context (ConversationContext): Current conversation context
        
        Returns:
            str: Booking confirmation response
        """
        # If this is initial booking request, confirm and ask for date
        if not any("дат" in msg["content"].lower() for msg in context.prev_messages[-3:] if msg["role"] == "user"):
            return self.templates["booking"]["confirmation"] + "\n\n" + self.templates["booking"]["date_request"]
            
        # If they've mentioned a date, process the booking
        return self.templates["booking"]["processing"]

    def _handle_upselling(self, context: ConversationContext) -> str:
        """
        Present additional product/service options to increase order value.
        Strategic upselling based on customer profile and selected tour.
        
        Args:
            context (ConversationContext): Current conversation context
        
        Returns:
            str: Upsell offer response
        """
        response = self.templates["upsell"]["intro"] + " "
        
        # Select appropriate upsell based on selected tour
        selected_tour = context.customer.selected_tour
        
        if selected_tour == "dubai_city_tour":
            response += self.templates["upsell"]["burj_khalifa"]
        elif selected_tour == "desert_safari":
            response += self.templates["upsell"]["photo_package"]
        elif selected_tour == "ferrari_world":
            response += self.templates["upsell"]["fast_track"]
        elif selected_tour == "abu_dhabi_tour":
            response += self.templates["upsell"]["ferrari_world"]
        else:
            # Default upsell
            response += self.templates["upsell"]["aquarium"]
            
        return response

    def _handle_closing(self, context: ConversationContext) -> str:
        """
        Deliver final confirmation and next steps.
        Maintains relationship for future bookings while confirming current one.
        
        Args:
            context (ConversationContext): Current conversation context
        
        Returns:
            str: Closing response with next steps
        """
        return (
            f"Отлично! Ваше бронирование успешно оформлено. Мы отправим подтверждение на указанный контактный номер в течение ближайшего часа.\n\n"
            f"В день экскурсии наш гид будет ждать вас в лобби отеля за 15 минут до начала тура. "
            f"Убедительная просьба не опаздывать, так как другие туристы будут ждать.\n\n"
            f"У вас остались какие-то вопросы? Если нет, то благодарю за бронирование и желаю вам незабываемых впечатлений от экскурсии! 😊"
        )

    def _format_variant_details(self, tour_id: str, variant_id: str, variant: TourVariant, customer: CustomerProfile) -> str:
        """
        Generate detailed variant information with pricing and specifics.
        
        Args:
            tour_id (str): ID of the selected tour
            variant_id (str): ID of the specific tour variant
            variant (TourVariant): Tour variant details
            customer (CustomerProfile): Customer profile
        
        Returns:
            str: Formatted variant details in Russian
        """
        emirate = customer.emirate or "dubai"
        pricing = None
        
        # Pricing selection logic
        pricing_keys = [
            emirate,
            f"{emirate}_no_transfer",
            "dubai",
            "dubai_no_transfer"
        ]
        
        for key in pricing_keys:
            if key in variant.pricing:
                pricing = variant.pricing[key]
                break
        
        if not pricing:
            return f"Вариант: {variant.name}\nЦены не доступны для вашего региона."
        
        # Construct detailed variant description
        result = f"Вариант: {variant.name}\n"
        result += f"Описание: {variant.description}\n"
        result += f"Продолжительность: {variant.duration}\n"
        
        # Pricing details
        result += f"Стоимость: {pricing.adult_price} AED за взрослого"
        
        # Child pricing
        if pricing.child_price is not None and (customer.children_count > 0 or customer.children_ages):
            result += f", {pricing.child_price} AED за ребенка"
            if pricing.child_age_min is not None and pricing.child_age_max is not None:
                result += f" (от {pricing.child_age_min} до {pricing.child_age_max} лет)"
        
        # Infant pricing
        if pricing.infant_price is not None and pricing.infant_price == 0:
            result += f", дети до {pricing.infant_age_max or 3} лет - бесплатно"
        
        # Additional notes
        if pricing.notes:
            result += f"\nПримечание: {pricing.notes}"
        
        # Inclusions
        inclusions = []
        if variant.includes_transfer:
            inclusions.append("трансфер")
        if variant.includes_meals:
            inclusions.append("питание")
        if variant.includes_guide:
            inclusions.append("русскоговорящий гид")
        if variant.includes_tickets:
            inclusions.append("входные билеты")
        
        if inclusions:
            result += f"\nВключено: {', '.join(inclusions)}"
        
        # Available days
        if variant.available_days and variant.available_days != ["daily"]:
            days_map = {
                "monday": "понедельник",
                "tuesday": "вторник",
                "wednesday": "среду",
                "thursday": "четверг",
                "friday": "пятницу",
                "saturday": "субботу",
                "sunday": "воскресенье",
                "daily": "ежедневно"
            }
            days_ru = [days_map.get(day, day) for day in variant.available_days]
            result += f"\nДоступно в: {', '.join(days_ru)}"
            
        # Add urgency element
        slots_left = random.randint(2, 8)
        result += f"\n\n🔥 Осталось всего {slots_left} мест на ближайшие даты!"
        
        return result