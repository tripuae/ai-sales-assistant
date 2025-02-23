"""
WhatsApp Integration for TripUAE Sales Assistant
This module integrates the AI sales assistant with WhatsApp using Twilio.
"""

import os
import json
import logging
from typing import Dict
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# Import conversation engine and database loader
from conversation_engine import ResponseGenerator, ConversationContext
from data_loader import create_database

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class WhatsAppIntegration:
    """Integration with WhatsApp using Twilio."""
    
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        twilio_whatsapp_number: str,
        response_generator: ResponseGenerator,
        contexts_file: str = "conversation_contexts.json"
    ):
        """Initialize WhatsApp integration."""
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.twilio_whatsapp_number = twilio_whatsapp_number
        self.response_generator = response_generator
        self.client = Client(account_sid, auth_token)
        self.conversation_contexts: Dict[str, ConversationContext] = {}  # Maps phone numbers to contexts
        self.contexts_file = contexts_file

    def save_conversation_contexts(self) -> None:
        """Save conversation contexts to file."""
        try:
            contexts_dict = {
                phone: context.to_dict()
                for phone, context in self.conversation_contexts.items()
            }
            with open(self.contexts_file, "w", encoding="utf-8") as f:
                json.dump(contexts_dict, f)
            logger.info("Conversation contexts saved successfully.")
        except Exception as e:
            logger.error("Error saving conversation contexts: %s", e)

    def load_conversation_contexts(self) -> None:
        """Load conversation contexts from file."""
        if not os.path.exists(self.contexts_file):
            return
        try:
            with open(self.contexts_file, "r", encoding="utf-8") as f:
                contexts_dict = json.load(f)
            self.conversation_contexts = {
                phone: ConversationContext.from_dict(context_dict)
                for phone, context_dict in contexts_dict.items()
            }
            logger.info("Conversation contexts loaded successfully.")
        except Exception as e:
            logger.error("Error loading conversation contexts: %s", e)

    def send_message(self, to_number: str, message: str) -> None:
        """Send a WhatsApp message with error handling."""
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        try:
            self.client.messages.create(
                from_=self.twilio_whatsapp_number,
                body=message,
                to=to_number
            )
            logger.info("Message sent to %s", to_number)
        except Exception as e:
            logger.error("Error sending message to %s: %s", to_number, e)

    def process_incoming_message(self, from_number: str, message_body: str) -> str:
        """Process an incoming WhatsApp message and return the response."""
        if from_number not in self.conversation_contexts:
            self.conversation_contexts[from_number] = ConversationContext()
        context = self.conversation_contexts[from_number]
        logger.info("Processing message from %s: %s", from_number, message_body)
        response = self.response_generator.generate_response(context, message_body)
        self.save_conversation_contexts()
        return response

def create_app() -> Flask:
    """Create and configure the Flask app."""
    app = Flask(__name__)
    
    # Create database and response generator
    price_db = create_database()
    response_generator = ResponseGenerator(price_db)
    
    # Initialize WhatsApp integration and store it in app config
    whatsapp_integration = WhatsAppIntegration(
        account_sid=os.environ.get("TWILIO_ACCOUNT_SID", "AC80c152218f4f67385aa54f1bf2b3eaa4"),
        auth_token=os.environ.get("TWILIO_AUTH_TOKEN", "your_auth_token"),
        twilio_whatsapp_number=os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"),
        response_generator=response_generator,
        contexts_file="conversation_contexts.json"
    )
    app.config["whatsapp_integration"] = whatsapp_integration

    @app.route("/webhook", methods=["POST"])
    def webhook():
        """Handle incoming WhatsApp webhook."""
        try:
            incoming_msg = request.values.get("Body", "").strip()
            from_number = request.values.get("From", "")
            whatsapp_integration = app.config["whatsapp_integration"]
            response_text = whatsapp_integration.process_incoming_message(from_number, incoming_msg)
            twilio_response = MessagingResponse()
            twilio_response.message(response_text)
            return str(twilio_response)
        except Exception as e:
            logger.error("Error in webhook: %s", e)
            return "Internal Server Error", 500

    return app

def initialize_whatsapp_integration(port: int = 5000) -> None:
    """Initialize WhatsApp integration and start the Flask server."""
    app = create_app()
    whatsapp_integration = app.config["whatsapp_integration"]
    whatsapp_integration.load_conversation_contexts()
    app.run(host="0.0.0.0", port=port)

def send_test_message(phone_number: str, message: str) -> None:
    """Send a test message to a specific phone number."""
    app = create_app()
    whatsapp_integration = app.config.get("whatsapp_integration")
    if not whatsapp_integration:
        raise ValueError("WhatsApp integration not initialized")
    whatsapp_integration.send_message(phone_number, message)

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    initialize_whatsapp_integration(PORT)