import os
import logging
from typing import Dict

import telegram
from telegram import Update, Bot, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from claude_engine import ClaudeAssistant, ConversationContext
from data_loader import create_database

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionary to store conversation contexts for each user
user_contexts: Dict[int, ConversationContext] = {}

# Initialize the assistant
price_db = create_database()
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
    
    # Generate response
    try:
        response = assistant.generate_response(user_contexts[user_id], message_text)
        update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        update.message.reply_text(
            "I'm having trouble responding right now. Please try again later."
        )

def main():
    """Start the bot."""
    # Get the Telegram token from environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set. Please set this environment variable.")
        return
    
    # Create the Updater and dispatcher
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    
    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("reset", reset))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Start the Bot
    logger.info("Starting TripUAE Claude Telegram bot...")
    updater.start_polling()
    
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == "__main__":
    main()
