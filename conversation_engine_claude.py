import os
from typing import Dict, List, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage

class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content

class ConversationContext:
    def __init__(self):
        self.messages = []
    
    def add_message(self, role: str, content: str):
        self.messages.append(Message(role, content))

class ResponseGenerator:
    def __init__(self, price_db, use_claude=False):
        """
        Initialize the response generator with a price database.
        
        Args:
            price_db: Database containing pricing information for tours
            use_claude: Whether to use Claude for generating responses
        """
        self.price_db = price_db
        self.use_claude = use_claude
        
        # Initialize Claude client if needed
        if self.use_claude:
            self.claude = ChatAnthropic(
                model_name="claude-3-opus-20240229",
                anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY")
            )
    
    def generate_response(self, context: ConversationContext, user_message: str) -> str:
        """
        Generate a response to the user message based on the conversation context.
        
        Args:
            context: The conversation context
            user_message: The latest message from the user
            
        Returns:
            str: The generated response
        """
        # Check for rule-based responses first
        rule_based_response = self._check_rule_based_responses(user_message)
        if rule_based_response:
            return rule_based_response
        
        # If no rule-based response and Claude is enabled, use Claude
        if self.use_claude:
            messages = [
                SystemMessage(content="""You are a helpful and knowledgeable tourism assistant for TripUAE, 
                a tourism company based in Dubai, UAE. You can provide information about their tours including 
                Desert Safari, Dubai City Tour, and Night Cruise. Be friendly, informative, and helpful. 
                Always provide accurate pricing information when asked about costs."""),
            ]
            
            # Add conversation history
            for message in context.messages:
                if message.role == "user":
                    messages.append(HumanMessage(content=message.content))
                else:
                    # Assume assistant role for non-user messages
                    messages.append(SystemMessage(content=message.content))
            
            # Add the latest user message
            messages.append(HumanMessage(content=user_message))
            
            # Generate response using Claude
            response = self.claude.invoke(messages)
            return response.content
        
        # Default response if Claude is not enabled
        return self._generate_default_response(user_message)
    
    def _check_rule_based_responses(self, message: str) -> Optional[str]:
        """
        Check if the message can be answered with a rule-based response.
        
        Args:
            message: The user message
            
        Returns:
            Optional[str]: A rule-based response if applicable, None otherwise
        """
        # Check for various types of queries
        greeting_response = self._handle_greeting(message)
        if greeting_response:
            return greeting_response
            
        pricing_response = self._handle_pricing_query(message)
        if pricing_response:
            return pricing_response
            
        booking_response = self._handle_booking_query(message)
        if booking_response:
            return booking_response
            
        tour_info_response = self._handle_tour_info_query(message)
        if tour_info_response:
            return tour_info_response
            
        return None
    
    def _generate_default_response(self, message: str) -> str:
        """
        Generate a default response when no rule-based response is available.
        
        Args:
            message: The user message
            
        Returns:
            str: The default response
        """
        return "I'm sorry, I don't have specific information about that. Would you like to know about our Desert Safari, Dubai City Tour, or Night Cruise packages?"
    
    def _handle_greeting(self, message: str) -> Optional[str]:
        """Handle greeting messages."""
        # ...existing code...
        return None
    
    def _handle_pricing_query(self, message: str) -> Optional[str]:
        """Handle queries about pricing."""
        # ...existing code...
        return None
    
    def _handle_booking_query(self, message: str) -> Optional[str]:
        """Handle queries about bookings."""
        # ...existing code...
        return None
    
    def _handle_tour_info_query(self, message: str) -> Optional[str]:
        """Handle queries about tour information."""
        # ...existing code...
        return None
