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
from typing import Dict, List, Optional, Any
from enum import Enum

# Updated import statements from langchain-community
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# Import your database schema definitions
from database_schema import PriceDatabase, TourPackage, TourVariant, PriceOption, TransferOption

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "emirate": self.emirate,
            "group_size": self.group_size,
            "children_count": self.children_count,
            "children_ages": self.children_ages,
            "budget_preference": self.budget_preference,
            "interests": self.interests,
            "selected_tour": self.selected_tour,
            "selected_variant": self.selected_variant,
            "name": self.name,
            "language": self.language
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerProfile':
        profile = cls()
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
        return profile

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

        if self.use_chatgpt:
            self.llm = ChatOpenAI(model_name="gpt-4-turbo")

        if self.use_llama_index:
            # Comment out LlamaIndex functionality for now
            # documents = [
            #     Document(text="You are a professional tourism sales assistant. Respond in Russian with a friendly tone."),
            #     Document(text="Offer tour recommendations based on customer interests."),
            #     Document(text="Handle pricing objections gracefully and suggest upsell options."),
            #     Document(text="Guide customers to book tours when ready.")
            # ]
            # self.index = GPTVectorStoreIndex.from_documents(documents)
            pass  # Skip LlamaIndex integration

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        return {
            "greeting": {
                "initial": (
                    "Здравствуйте! Благодарим за обращение в компанию TripUAE. "
                    "Меня зовут Жасмина, и я с удовольствием помогу!😊\n\n"
                    "В каком эмирате вы находитесь и сколько человек в вашей группе?"
                ),
                "return_visitor": "Рада снова вас видеть! Чем могу помочь сегодня?"
            },
            "gather_info": {
                "emirate": "Пожалуйста, укажите, в каком эмирате вы находитесь.",
                "group_size": "Сколько человек будет участвовать в экскурсии?",
                "children": "Будут ли с вами дети? Если да, укажите их возраст.",
                "interests": "Что вас больше всего интересует: городские экскурсии, пустынное сафари, круизы или другое?"
            },
            "recommendations": {
                "intro": "Исходя из предоставленной информации, я рекомендую следующие варианты:",
                "desert_safari": "🏜 Пустынное джип-сафари – захватывающее приключение по песчаным дюнам с ужином и шоу.",
                "dubai_city": "🏙 Обзорная экскурсия по Дубаю – знакомство с главными достопримечательностями.",
                "night_cruise": "🚤 Ночной круиз по Дубай Марине – романтическое путешествие с ужином и великолепными видами."
            },
            "tour_details": {
                "desert_safari": {
                    "emotional_intro": (
                        "Окунитесь в магию аравийской пустыни, где золотые пески и закат создают незабываемую атмосферу."
                    ),
                    "program": (
                        "Вас ждет катание по дюнам, поездка на верблюдах, национальные костюмы и шоу с ужином-барбекю."
                    ),
                    "variant_intro": "Выберите один из следующих вариантов:"
                },
                "dubai_city": {
                    "emotional_intro": (
                        "Откройте для себя удивительный Дубай – город контрастов, где современность встречается с историей."
                    ),
                    "program": (
                        "Экскурсия включает посещение Бурдж Халифа, Дубай Молл, исторических кварталов и многое другое."
                    ),
                    "variant_intro": "Доступны следующие варианты:"
                },
                "night_cruise": {
                    "emotional_intro": (
                        "Представьте вечер под звездами на традиционной лодке, плывущей по мерцающей Дубай Марине."
                    ),
                    "program": (
                        "Круиз включает ужин, развлекательную программу и великолепные виды ночного города."
                    ),
                    "variant_intro": "Мы предлагаем следующие варианты:"
                }
            },
            "objection_handling": {
                "price_high": (
                    "Я понимаю, что цена может показаться высокой. Но стоимость включает трансфер, профессионального гида, билеты и сервис. "
                    "Можем обсудить возможные скидки."
                ),
                "thinking": (
                    "Понимаю, решение требует времени. Могу зарезервировать место, пока вы обдумываете варианты."
                ),
                "alternatives": (
                    "Если этот вариант не подходит, я могу предложить альтернативные экскурсии, соответствующие вашим требованиям."
                ),
                "pricing_inquiry": (
                    "Стоимость экскурсии зависит от выбранного пакета. Какой вариант вас интересует: стандарт, премиум или VIP?"
                )
            },
            "booking": {
                "confirmation": "Отлично! Я зарезервирую для вас выбранную экскурсию.",
                "date_request": "На какую дату вы планируете посещение экскурсии? (TUAE)",
                "processing": "Я оформляю вашу бронь, это займет несколько минут.",
                "success": "Ваша бронь успешно оформлена! Спасибо за выбор TripUAE."
            },
            "upsell": {
                "intro": "Чтобы сделать ваше путешествие еще более особенным, рекомендую:",
                "burj_khalifa": (
                    "дополнить тур подъемом на смотровую площадку Бурдж Халифа – увидеть город с высоты за $55."
                ),
                "aquarium": (
                    "посетить аквариум в Дубай Молле – уникальная возможность увидеть более 33 000 морских обитателей за $35."
                )
            },
            "not_available": (
                "Мне необходимо немного времени, чтобы уточнить информацию. "
                "Я чуть позже вернусь с ответом. Вы не против? (TUAE)"
            )
        }

    def _assemble_prompt(self, context: ConversationContext, user_message: str) -> str:
        prompt = "You are a professional tourism sales assistant. Respond in Russian with a friendly, professional tone.\n\n"
        prompt += "Conversation History:\n"
        for msg in context.prev_messages:
            prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        prompt += f"User: {user_message}\n\n"
        prompt += "Based on this, provide a helpful and informative answer."
        return prompt

    def generate_response(self, context: ConversationContext, user_message: str) -> str:
        context.add_message("user", user_message)
        logger.info("Processing user message: %s", user_message)
        
        # If using ChatGPT integration, try that first
        if self.use_chatgpt:
            prompt = self._assemble_prompt(context, user_message)
            try:
                chat_response = self.llm.invoke(prompt)
                response_text = chat_response.content.strip()
                context.add_message("assistant", response_text)
                logger.info("ChatGPT response: %s", response_text)
                return response_text
            except Exception as e:
                logger.error("Error during ChatGPT invocation: %s", e)
        
        # If using LlamaIndex integration, try that next
        if self.use_llama_index:
            # Comment out for now
            # prompt = self._assemble_prompt(context, user_message)
            # try:
            #     index_result = self.index.query(prompt)
            #     response_text = index_result.strip()
            #     context.add_message("assistant", response_text)
            #     logger.info("LlamaIndex response: %s", response_text)
            #     return response_text
            # except Exception as e:
            #     logger.error("Error during LlamaIndex query: %s", e)
            pass  # Skip LlamaIndex integration
        
        # Fallback: use internal logic
        self._extract_emirate(context, user_message)
        self._extract_group_size(context, user_message)
        self._extract_interests(context, user_message)
        self._check_tour_selection(context, user_message)
        intents = self._determine_intent(user_message)
        if intents["objection"]:
            context.state = ConversationState.HANDLING_OBJECTION
        elif intents["booking"] and context.customer.selected_tour:
            context.state = ConversationState.BOOKING
        elif intents["pricing_inquiry"]:
            context.state = ConversationState.HANDLING_OBJECTION
        self._update_conversation_state(context)
        logger.info("Updated conversation state: %s", context.state.value)
        
        if context.state == ConversationState.GREETING:
            response = self._handle_greeting(context)
        elif context.state == ConversationState.GATHERING_INFO:
            response = self._handle_gathering_info(context)
        elif context.state == ConversationState.RECOMMENDING:
            response = self._handle_recommending(context)
        elif context.state == ConversationState.PRESENTING_DETAILS:
            response = self._handle_presenting_details(context)
        elif context.state == ConversationState.HANDLING_OBJECTION:
            response = self._handle_objection(context, user_message)
        elif context.state == ConversationState.BOOKING:
            response = self._handle_booking(context, user_message)
        elif context.state == ConversationState.UPSELLING:
            response = self._handle_upsell(context, user_message)
        elif context.state == ConversationState.CLOSING:
            response = self._handle_closing(context)
        else:
            response = self.templates["not_available"]
        
        context.add_message("assistant", response)
        return response

    def _determine_intent(self, message: str) -> Dict[str, bool]:
        message_lower = message.lower()
        intents = {
            "booking": bool(re.search(r"\b(бронировать|забронировать|book|reserve|reservation)\b", message_lower)),
            "objection": bool(re.search(r"\b(дорого|цена\s?высок|слишком|expensive|cost|дешевле|cheaper)\b", message_lower)),
            "pricing_inquiry": bool(re.search(r"\b(стоимость|цена)\b", message_lower))
        }
        logger.info("Detected intents: %s", intents)
        return intents

    def _extract_emirate(self, context: ConversationContext, message: str) -> None:
        patterns = {
            "dubai": r"\b(дубай|dubai|дубаи)\b",
            "abu_dhabi": r"\b(абу\s?-?даби|abu\s?dhabi)\b",
            "sharjah": r"\b(шарджа|sharjah)\b",
            "ajman": r"\b(аджман|ajman)\b",
            "ras_al_khaimah": r"\b(рас\s?-?аль\s?-?хайма|ras\s?al\s?khaimah)\b",
            "fujairah": r"\b(фуджейра|fujairah)\b"
        }
        for emirate, pattern in patterns.items():
            if re.search(pattern, message.lower()):
                context.customer.emirate = emirate
                logger.info("Extracted emirate: %s", emirate)
                break

    def _extract_group_size(self, context: ConversationContext, message: str) -> None:
        size_patterns = [
            (r"\b(\d+)\s+(человек|людей|взрослых|гостей)\b", lambda x: int(x)),
            (r"\b(один|одна|1)\b", lambda x: 1),
            (r"\b(два|две|2)\b", lambda x: 2),
            (r"\b(три|3)\b", lambda x: 3),
            (r"\b(четыре|4)\b", lambda x: 4),
            (r"\b(пять|5)\b", lambda x: 5),
            (r"\b(шесть|6)\b", lambda x: 6),
            (r"\b(семь|7)\b", lambda x: 7),
            (r"\b(нас|группа)\s+(\d+)\b", lambda x: int(x))
        ]
        msg_lower = message.lower()
        for pattern, converter in size_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                context.customer.group_size = converter(match.group(1))
                logger.info("Extracted group size: %s", context.customer.group_size)
                break

        child_patterns = [
            (r"\b(\d+)\s+(ребенка|детей|ребенок|дитя)\b", lambda x: int(x)),
            (r"\bс\s+(ребенком|детьми)\b", lambda x: 1),
            (r"\bвозрастом\s+(\d+)\b", lambda x: int(x)),
            (r"\b(\d+)\s+(года|лет)\b", lambda x: int(x))
        ]
        for pattern, converter in child_patterns:
            for m in re.finditer(pattern, msg_lower):
                if m.groups():
                    age = converter(m.group(1))
                    if age <= 18:
                        context.customer.children_count += 1
                        context.customer.children_ages.append(age)
                        logger.info("Detected child with age: %s", age)

    def _extract_interests(self, context: ConversationContext, message: str) -> None:
        interest_patterns = {
            "desert_safari": r"\b(пустын|сафари|desert|джип)\b",
            "city_tour": r"\b(город|сити|обзорн|tour|экскурси)\b",
            "cruise": r"\b(круиз|яхт|boat|marina)\b",
            "adventure": r"\b(приключени|адреналин|вертолет)\b",
            "attractions": r"\b(музей|парк|билет|аттракцион|бурдж|khalifa)\b"
        }
        msg_lower = message.lower()
        for interest, pattern in interest_patterns.items():
            if re.search(pattern, msg_lower):
                if interest not in context.customer.interests:
                    context.customer.interests.append(interest)
                    logger.info("Extracted interest: %s", interest)

    def _check_tour_selection(self, context: ConversationContext, message: str) -> None:
        tour_patterns = {
            "desert_jeep_safari": r"\b(пустынное\s?сафари|desert\s?safari)\b",
            "night_cruise": r"\b(круиз|ночной\s?круиз|marina\s?cruise)\b",
            "dubai_city_tour": r"\b(обзорная\s?экскурсия|city\s?tour|dubai\s?tour|сити\s?тур)\b"
        }
        msg_lower = message.lower()
        for tour_id, pattern in tour_patterns.items():
            if re.search(pattern, msg_lower):
                context.customer.selected_tour = tour_id
                context.state = ConversationState.PRESENTING_DETAILS
                logger.info("Selected tour: %s", tour_id)
                break
        
        if context.customer.selected_tour:
            variant_patterns = {
                "standard": r"\b(стандарт|basic)\b",
                "premium": r"\b(премиум|premium|улучшенн)\b",
                "vip": r"\b(вип|vip|люкс|luxury)\b"
            }
            for variant_id, pattern in variant_patterns.items():
                if re.search(pattern, msg_lower):
                    context.customer.selected_variant = variant_id
                    logger.info("Selected variant: %s", variant_id)
                    break

    def _update_conversation_state(self, context: ConversationContext) -> None:
        if context.state == ConversationState.GREETING:
            context.state = ConversationState.GATHERING_INFO
        
        if (context.state == ConversationState.GATHERING_INFO and 
            context.customer.emirate is not None and 
            context.customer.group_size is not None):
            context.state = ConversationState.RECOMMENDING
        
        if context.customer.selected_tour and context.state == ConversationState.RECOMMENDING:
            context.state = ConversationState.PRESENTING_DETAILS

    def _handle_greeting(self, context: ConversationContext) -> str:
        if len(context.prev_messages) > 2:
            return self.templates["greeting"]["return_visitor"]
        return self.templates["greeting"]["initial"]

    def _handle_gathering_info(self, context: ConversationContext) -> str:
        if context.customer.emirate is None:
            return self.templates["gather_info"]["emirate"]
        if context.customer.group_size is None:
            return self.templates["gather_info"]["group_size"]
        return self.templates["gather_info"]["interests"]

    def _handle_recommending(self, context: ConversationContext) -> str:
        recommendations = self._get_recommendations(context.customer)
        context.last_recommendations = recommendations
        response = self.templates["recommendations"]["intro"] + "\n\n"
        for rec_id in recommendations[:3]:
            if rec_id in self.templates["recommendations"]:
                response += self.templates["recommendations"][rec_id] + "\n\n"
        response += "Какой вариант вас интересует?"
        return response

    def _get_recommendations(self, customer: CustomerProfile) -> List[str]:
        recs = []
        if "desert_safari" in customer.interests:
            recs.append("desert_jeep_safari")
        if "city_tour" in customer.interests:
            recs.append("dubai_city_tour")
        if "cruise" in customer.interests:
            recs.append("night_cruise")
        if not recs:
            if customer.emirate == "dubai":
                recs = ["desert_jeep_safari", "dubai_city_tour", "night_cruise"]
            elif customer.emirate == "abu_dhabi":
                recs = ["dubai_city_tour", "desert_jeep_safari"]
            else:
                recs = ["desert_jeep_safari", "dubai_city_tour"]
        return recs

    def _handle_presenting_details(self, context: ConversationContext) -> str:
        tour_id = context.customer.selected_tour
        if not tour_id or tour_id not in self.price_db.tours:
            context.state = ConversationState.RECOMMENDING
            return self._handle_recommending(context)
        
        tour = self.price_db.tours[tour_id]
        response = ""
        if tour_id in self.templates["tour_details"]:
            tdata = self.templates["tour_details"][tour_id]
            response += tdata["emotional_intro"] + "\n\n"
            response += tdata["program"] + "\n\n"
            if len(tour.variants) > 1:
                response += tdata["variant_intro"] + "\n\n"
                if context.customer.selected_variant and context.customer.selected_variant in tour.variants:
                    variant = tour.variants[context.customer.selected_variant]
                    response += self._format_variant_details(tour_id, context.customer.selected_variant, variant, context.customer)
                else:
                    for variant_id, variant in tour.variants.items():
                        if "private" in variant_id and (context.customer.group_size is None or context.customer.group_size > variant.min_participants):
                            continue
                        response += self._format_variant_details(tour_id, variant_id, variant, context.customer) + "\n\n"
        else:
            response += f"Экскурсия '{tour.name}' - {tour.description}\n\n"
            for variant_id, variant in tour.variants.items():
                response += self._format_variant_details(tour_id, variant_id, variant, context.customer) + "\n\n"
        
        if tour.upsell_suggestions:
            upsell_id = tour.upsell_suggestions[0]
            if upsell_id in self.templates["upsell"]:
                response += self.templates["upsell"]["intro"] + " " + self.templates["upsell"][upsell_id] + "\n\n"
        
        response += "Хотели бы забронировать экскурсию?"
        return response

    def _format_variant_details(self, tour_id: str, variant_id: str, variant: TourVariant, customer: CustomerProfile) -> str:
        emirate = customer.emirate or "dubai"
        pricing = None
        if emirate in variant.pricing:
            pricing = variant.pricing[emirate]
        elif f"{emirate}_no_transfer" in variant.pricing:
            pricing = variant.pricing[f"{emirate}_no_transfer"]
        elif "dubai" in variant.pricing:
            pricing = variant.pricing["dubai"]
        elif "dubai_no_transfer" in variant.pricing:
            pricing = variant.pricing["dubai_no_transfer"]
        if not pricing:
            return f"Вариант: {variant.name}\nЦены не доступны для вашего региона. {self.templates['not_available']}"
        
        result = f"Вариант: {variant.name}\nОписание: {variant.description}\nПродолжительность: {variant.duration}\n"
        result += f"Стоимость: ${pricing.adult_price} за взрослого"
        if pricing.child_price is not None and (customer.children_count > 0 or customer.children_ages):
            result += f", ${pricing.child_price} за ребенка"
            if pricing.child_age_min is not None and pricing.child_age_max is not None:
                result += f" (от {pricing.child_age_min} до {pricing.child_age_max} лет)"
        if pricing.infant_price is not None and pricing.infant_price == 0:
            result += f", дети до {pricing.infant_age_max or 3} лет - бесплатно"
        if pricing.notes:
            result += f"\nПримечание: {pricing.notes}"
        
        inclusions = []
        if variant.includes_transfer:
            inclusions.append("трансфер")
        if variant.includes_meals:
            inclusions.append("питание")
        if inclusions:
            result += f"\nВключено: {', '.join(inclusions)}"
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
        return result

    def _handle_objection(self, context: ConversationContext, user_message: str) -> str:
        msg_lower = user_message.lower()
        if re.search(r"(дорого|цена\s?высок|слишком|expensive|cost)", msg_lower):
            return self.templates["objection_handling"]["price_high"]
        elif re.search(r"(подумаю|надо\s?обсудить|think\s?about\s?it|not\s?sure)", msg_lower):
            return self.templates["objection_handling"]["thinking"]
        elif re.search(r"(стоимость|цена)", msg_lower):
            return self.templates["objection_handling"]["pricing_inquiry"]
        else:
            return self.templates["objection_handling"]["alternatives"]

    def _handle_booking(self, context: ConversationContext, user_message: str) -> str:
        return self.templates["booking"]["date_request"]

    def _handle_upsell(self, context: ConversationContext, user_message: str) -> str:
        return self.templates["upsell"]["intro"] + " " + self.templates["upsell"]["burj_khalifa"]

    def _handle_closing(self, context: ConversationContext) -> str:
        return self.templates["booking"]["success"]