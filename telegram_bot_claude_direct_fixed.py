import os
import logging
import sys
from typing import Dict
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# First, verify telegram is properly installed
try:
    import telegram
    logger.info(f"Successfully imported telegram version {telegram.__version__}")
except ImportError as e:
    logger.error(f"Error importing telegram: {e}")
    logger.error("Try reinstalling with: pip install python-telegram-bot==13.7")
    sys.exit(1)

# Then try to import specific telegram classes
try:
    from telegram import Update, Bot, ChatAction
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
    logger.info("Successfully imported telegram classes")
except ImportError as e:
    logger.error(f"Error importing telegram classes: {e}")
    logger.error("This might be due to a version mismatch. Try reinstalling with: pip install python-telegram-bot==13.7")
    sys.exit(1)

# Import our direct Claude implementation
try:
    from direct_claude_engine import ClaudeAssistant, ConversationContext
    from data_loader import create_database
    logger.info("Successfully imported Claude engine")
except ImportError as e:
    logger.error(f"Error importing Claude engine: {e}")
    sys.exit(1)

# Dictionary to store conversation contexts for each user
user_contexts: Dict[int, ConversationContext] = {}

# Initialize the price database
price_db = create_database()

# Initialize the Claude assistant
assistant = ClaudeAssistant(price_db)

def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command."""
    user_id = update.effective_user.id
    user_contexts[user_id] = ConversationContext()  # Reset the conversation
    
    welcome_message = (
        "Welcome to TripUAE Assistant powered by Claude!\n\n"
        "I can help you with information about our tours including Desert Safari, "
        "Dubai City Tour, and Night Cruise.\n\n"
        "How can I assist you today?"
    )
    update.message.reply_text(welcome_message)

def help_command(update: Update, context: CallbackContext) -> None:
    """Handle the /help command."""
    help_message = (
        "I can provide information about TripUAE's tours.\n\n"
        "You can ask me about:\n"
        "- Tour details and highlights\n"
        "- Pricing information\n"
        "- Booking procedures\n"
        "- Practical information\n\n"
        "Commands:\n"
        "/start - Start a new conversation\n"
        "/help - Show this help message\n"
        "/reset - Reset your conversation history"
    )
    update.message.reply_text(help_message)

def reset(update: Update, context: CallbackContext) -> None:
    """Handle the /reset command."""
    user_id = update.effective_user.id
    user_contexts[user_id] = ConversationContext()  # Reset the conversation
    update.message.reply_text("Conversation history has been reset.")

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming text messages."""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Get or create conversation context for this user
    if user_id not in user_contexts:
        user_contexts[user_id] = ConversationContext()
    
    # Show typing indicator
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    
    # Generate response using our direct Claude implementation
    try:
        response = assistant.generate_response(user_contexts[user_id], message_text)
        
        # Handle potential long messages (Telegram has a 4096 character limit)
        if len(response) > 4000:
            # Split long messages
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                update.message.reply_text(chunk)
        else:
            update.message.reply_text(response)
            
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        update.message.reply_text(
            "I'm having trouble responding right now. Please try again later."
        )

def main() -> None:
    """Start the bot."""
    # Load environment variables
    load_dotenv()
    
    # Get the Telegram token from environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set. Please set this environment variable.")
        print("You need to set the TELEGRAM_BOT_TOKEN environment variable.")
        print("Run: export TELEGRAM_BOT_TOKEN=your_token_here")
        return
    
    logger.info(f"Using token: {token[:5]}...{token[-5:]}")
    
    # Create the Updater and dispatcher
    try:
        updater = Updater(token=token)
        dispatcher = updater.dispatcher
    except Exception as e:
        logger.error(f"Error initializing Telegram bot: {e}")
        print(f"Error: {e}")
        return
    
    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("reset", reset))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Start the Bot
    logger.info("Starting TripUAE Claude Telegram bot...")
    print("Starting Telegram bot. Press Ctrl+C to stop.")
    
    try:
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
