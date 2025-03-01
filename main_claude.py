import argparse
import os
import json
from typing import List, Dict, Any, Optional
import sys

# Import Claude components
from claude_engine import ClaudeAssistant, ConversationContext
from data_loader import create_database

# Optional imports for different modes
try:
    from flask import Flask, request, Response
    from twilio.twiml.messaging_response import MessagingResponse
except ImportError:
    pass

try:
    import telegram
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
except ImportError:
    pass

def interactive_console_mode(db_path: str = None):
    """Run the assistant in interactive console mode.
    
    Args:
        db_path: Optional path to the database file
    """
    # Initialize the price database
    price_db = create_database(db_path)
    
    # Create assistant instance
    assistant = ClaudeAssistant(price_db)
    
    # Create conversation context
    context = ConversationContext()
    
    # Initial greeting
    print("Welcome to TripUAE Assistant powered by Claude! How can I help you today?")
    print("(Type 'exit' or 'quit' to end the conversation)")
    
    # Conversation loop
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for using TripUAE Assistant. Have a great day!")
            break
        
        # Generate and print response
        response = assistant.generate_response(context, user_input)
        print(f"\nAssistant: {response}")

def batch_test_mode(test_scenarios_path: str, db_path: str = None):
    """Run the assistant in batch test mode.
    
    Args:
        test_scenarios_path: Path to test scenarios JSON file
        db_path: Optional path to the database file
    """
    # Initialize the price database
    price_db = create_database(db_path)
    
    # Create assistant instance
    assistant = ClaudeAssistant(price_db)
    
    # Load test scenarios
    try:
        with open(test_scenarios_path, 'r') as file:
            scenarios = json.load(file)
    except Exception as e:
        print(f"Error loading test scenarios: {e}")
        return
    
    # Process each scenario
    results = []
    for i, scenario in enumerate(scenarios):
        print(f"\nRunning scenario {i+1}: {scenario.get('name', 'Unnamed')}")
        
        # Create fresh conversation context for each scenario
        context = ConversationContext()
        
        # Process messages in the scenario
        for message in scenario.get('messages', []):
            user_input = message.get('content', '')
            print(f"User: {user_input}")
            
            # Generate response
            response = assistant.generate_response(context, user_input)
            print(f"Assistant: {response}")
            
            # Record result
            results.append({
                'scenario': scenario.get('name', 'Unnamed'),
                'user_input': user_input,
                'response': response
            })
    
    # Option to save results
    save_path = input("\nEnter a file path to save results (or press Enter to skip): ")
    if save_path:
        try:
            with open(save_path, 'w') as file:
                json.dump(results, file, indent=2)
            print(f"Results saved to {save_path}")
        except Exception as e:
            print(f"Error saving results: {e}")

def setup_whatsapp_mode(account_sid: str, auth_token: str, port: int = 5000, db_path: str = None):
    """Set up a Flask server for WhatsApp integration.
    
    Args:
        account_sid: Twilio account SID
        auth_token: Twilio auth token
        port: Port for the Flask server
        db_path: Optional path to the database file
    """
    try:
        # Check if Flask is installed
        if 'flask' not in sys.modules or 'twilio' not in sys.modules:
            print("WhatsApp mode requires Flask and Twilio. Please install them with:")
            print("pip install flask twilio")
            return
        
        from flask import Flask, request, Response
        from twilio.twiml.messaging_response import MessagingResponse
        
        # Initialize the price database
        price_db = create_database(db_path)
        
        # Create assistant instance
        assistant = ClaudeAssistant(price_db)
        
        # Create Flask app
        app = Flask(__name__)
        
        # Dictionary to store conversation contexts
        conversation_contexts = {}
        
        @app.route('/webhook', methods=['POST'])
        def webhook():
            # Get incoming message information
            incoming_msg = request.values.get('Body', '').strip()
            sender_id = request.values.get('From', '')
            
            # Get or create conversation context for this sender
            if sender_id not in conversation_contexts:
                conversation_contexts[sender_id] = ConversationContext()
            context = conversation_contexts[sender_id]
            
            # Generate response
            response = assistant.generate_response(context, incoming_msg)
            
            # Create Twilio response
            twilio_resp = MessagingResponse()
            twilio_resp.message(response)
            
            return Response(str(twilio_resp), mimetype='text/xml')
        
        # Start Flask server
        print(f"Starting WhatsApp webhook server on port {port}...")
        app.run(host='0.0.0.0', port=port)
        
    except Exception as e:
        print(f"Error setting up WhatsApp mode: {e}")

def telegram_mode(token: str, db_path: str = None):
    """Set up a Telegram bot.
    
    Args:
        token: Telegram bot token
        db_path: Optional path to the database file
    """
    try:
        # Check if python-telegram-bot is installed
        if 'telegram' not in sys.modules:
            print("Telegram mode requires python-telegram-bot. Please install it with:")
            print("pip install python-telegram-bot==13.7")  # Specific version for compatibility
            return
            
        # Initialize the price database
        price_db = create_database(db_path)
        
        # Create assistant instance
        assistant = ClaudeAssistant(price_db)
        
        # Dictionary to store conversation contexts
        conversation_contexts = {}
        
        def start(update, context):
            """Handle the /start command."""
            welcome_message = "Welcome to TripUAE Assistant! How can I help you today?"
            update.message.reply_text(welcome_message)
        
        def handle_message(update, context):
            """Handle incoming messages."""
            user_id = update.effective_user.id
            message_text = update.message.text
            
            # Get or create conversation context for this user
            if user_id not in conversation_contexts:
                conversation_contexts[user_id] = ConversationContext()
            
            # Generate response
            response = assistant.generate_response(conversation_contexts[user_id], message_text)
            
            # Send response
            update.message.reply_text(response)
        
        # Set up updater and dispatcher
        updater = Updater(token=token, use_context=True)
        dispatcher = updater.dispatcher
        
        # Register handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # Start the bot
        print("Starting Telegram bot...")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"Error setting up Telegram bot: {e}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="TripUAE Claude Assistant")
    parser.add_argument("--mode", choices=["interactive", "batch", "whatsapp", "telegram"], 
                      default="interactive", help="Operation mode")
    parser.add_argument("--test-scenarios", help="Path to test scenarios JSON file for batch mode")
    parser.add_argument("--account-sid", help="Twilio account SID for WhatsApp mode")
    parser.add_argument("--auth-token", help="Twilio auth token for WhatsApp mode")
    parser.add_argument("--telegram-token", help="Telegram bot token for Telegram mode")
    parser.add_argument("--port", type=int, default=5000, help="Port for webhook server")
    parser.add_argument("--db-path", help="Path to database file")
    
    args = parser.parse_args()
    
    # Run the selected mode
    if args.mode == "interactive":
        interactive_console_mode(args.db_path)
    elif args.mode == "batch":
        if not args.test_scenarios:
            parser.error("Batch mode requires --test-scenarios")
        batch_test_mode(args.test_scenarios, args.db_path)
    elif args.mode == "whatsapp":
        if not args.account_sid or not args.auth_token:
            parser.error("WhatsApp mode requires --account-sid and --auth-token")
        setup_whatsapp_mode(args.account_sid, args.auth_token, args.port, args.db_path)
    elif args.mode == "telegram":
        if not args.telegram_token:
            parser.error("Telegram mode requires --telegram-token")
        telegram_mode(args.telegram_token, args.db_path)

if __name__ == "__main__":
    main()
