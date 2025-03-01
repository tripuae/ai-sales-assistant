import os
import json
import requests
from typing import Dict, Optional
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

from claude_engine import ClaudeAssistant, ConversationContext
from data_loader import create_database

class WhatsAppIntegration:
    def __init__(self, assistant: ClaudeAssistant, context_file_path: str = "whatsapp_contexts.json"):
        """
        Initialize WhatsApp integration with a Claude assistant.
        
        Args:
            assistant: Claude assistant for generating responses
            context_file_path: File path for saving conversation contexts
        """
        self.assistant = assistant
        self.contexts: Dict[str, ConversationContext] = {}
        self.context_file_path = context_file_path
        
        # Load existing contexts if file exists
        self.load_contexts()
    
    def save_contexts(self):
        """Save conversation contexts to file."""
        try:
            # Convert ConversationContext objects to serializable dictionaries
            serializable_contexts = {}
            for phone_number, context in self.contexts.items():
                serializable_contexts[phone_number] = {
                    "messages": context.messages
                }
            
            # Save to file
            with open(self.context_file_path, 'w') as file:
                json.dump(serializable_contexts, file)
        except Exception as e:
            print(f"Error saving contexts: {e}")
    
    def load_contexts(self):
        """Load conversation contexts from file."""
        try:
            if os.path.exists(self.context_file_path):
                with open(self.context_file_path, 'r') as file:
                    serialized_contexts = json.load(file)
                
                # Convert serialized data back to ConversationContext objects
                for phone_number, data in serialized_contexts.items():
                    context = ConversationContext()
                    for message in data.get("messages", []):
                        context.add_message(message["role"], message["content"])
                    self.contexts[phone_number] = context
        except Exception as e:
            print(f"Error loading contexts: {e}")
    
    def get_or_create_context(self, phone_number: str) -> ConversationContext:
        """
        Get or create conversation context for the given phone number.
        
        Args:
            phone_number: The user's phone number
            
        Returns:
            ConversationContext: The conversation context for the user
        """
        if phone_number not in self.contexts:
            self.contexts[phone_number] = ConversationContext()
        
        return self.contexts[phone_number]
    
    def process_incoming_message(self, phone_number: str, message_text: str) -> str:
        """
        Process an incoming message and generate a response.
        
        Args:
            phone_number: The user's phone number
            message_text: The incoming message text
            
        Returns:
            str: The generated response
        """
        # Get or create context
        context = self.get_or_create_context(phone_number)
        
        # Generate response using Claude
        response = self.assistant.generate_response(context, message_text)
        
        # Save updated contexts
        self.save_contexts()
        
        return response

def create_app(account_sid: Optional[str] = None, auth_token: Optional[str] = None, db_path: Optional[str] = None):
    """
    Create a Flask app for WhatsApp integration.
    
    Args:
        account_sid: Twilio account SID
        auth_token: Twilio auth token
        db_path: Path to database file
        
    Returns:
        Flask: The Flask app
    """
    # Initialize database and assistant
    price_db = create_database(db_path)
    assistant = ClaudeAssistant(price_db)
    
    # Initialize WhatsApp integration
    whatsapp_integration = WhatsAppIntegration(assistant)
    
    # Create Flask app
    app = Flask(__name__)
    
    @app.route('/webhook', methods=['POST'])
    def webhook():
        # Get incoming message details
        incoming_msg = request.values.get('Body', '').strip()
        sender_phone = request.values.get('From', '')
        
        # Process message and get response
        response = whatsapp_integration.process_incoming_message(sender_phone, incoming_msg)
        
        # Create Twilio response
        twilio_response = MessagingResponse()
        twilio_response.message(response)
        
        return Response(str(twilio_response), mimetype='text/xml')
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return "Service is running", 200
    
    return app

def initialize_whatsapp_integration(account_sid: str, auth_token: str, phone_number: str, port: int = 5000, db_path: Optional[str] = None):
    """
    Initialize and start WhatsApp integration.
    
    Args:
        account_sid: Twilio account SID
        auth_token: Twilio auth token
        phone_number: WhatsApp phone number
        port: Port for the Flask server
        db_path: Path to database file
    """
    # Create app
    app = create_app(account_sid, auth_token, db_path)
    
    # Print information
    print(f"Starting WhatsApp integration on port {port}")
    print(f"WhatsApp number: {phone_number}")
    
    # Run app
    app.run(host='0.0.0.0', port=port)

def send_test_message(account_sid: str, auth_token: str, from_number: str, to_number: str, message: str):
    """
    Send a test message using Twilio.
    
    Args:
        account_sid: Twilio account SID
        auth_token: Twilio auth token
        from_number: Twilio WhatsApp number
        to_number: Recipient phone number
        message: Message content
    """
    try:
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        # Send message
        message = client.messages.create(
            body=message,
            from_=f"whatsapp:{from_number}",
            to=f"whatsapp:{to_number}"
        )
        
        print(f"Test message sent. SID: {message.sid}")
    except Exception as e:
        print(f"Error sending test message: {e}")

if __name__ == '__main__':
    # Get environment variables
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not account_sid or not auth_token or not phone_number:
        print("Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables.")
        exit(1)
    
    # Initialize WhatsApp integration
    initialize_whatsapp_integration(account_sid, auth_token, phone_number)
