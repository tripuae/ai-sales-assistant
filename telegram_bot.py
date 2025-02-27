import os
import logging
from typing import Dict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from simple_openai_engine import OpenAIAssistant, ConversationContext

# Load environment variables
load_dotenv()

# Configure logging - Increase level to DEBUG for more information
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Store conversation contexts for different users
user_contexts: Dict[int, ConversationContext] = {}

# Initialize the assistant (passing None since we don't need the price database for now)
assistant = OpenAIAssistant(None)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    user_id = update.effective_user.id
    logger.debug(f"Start command received from user {user_id}")
    
    # Create a new conversation context for this user
    user_contexts[user_id] = ConversationContext()
    
    welcome_message = (
        "👋 Welcome to TripUAE Assistant! I can help you discover our tours and activities in Dubai and UAE.\n\n"
        "Ask me about desert safaris, city tours, or night cruises. I can provide information about prices, "
        "schedules, and what's included in our packages."
    )
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the /help command is issued."""
    logger.debug("Help command received")
    help_text = (
        "Here are some things you can ask me:\n\n"
        "• What tours do you offer?\n"
        "• How much is the desert safari for 2 adults and 1 child?\n"
        "• Tell me about the night cruise in Dubai Marina\n"
        "• What's included in the Dubai city tour?\n\n"
        "Just type your question and I'll do my best to help!"
    )
    await update.message.reply_text(help_text)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset the conversation when the /reset command is issued."""
    user_id = update.effective_user.id
    logger.debug(f"Reset command received from user {user_id}")
    user_contexts[user_id] = ConversationContext()
    await update.message.reply_text("Our conversation has been reset. What would you like to know about our tours?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and generate responses using the OpenAI assistant."""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.debug(f"Message received: '{user_message}' from user {user_id}")
    
    # If this is a new user, create a conversation context
    if user_id not in user_contexts:
        logger.debug(f"Creating new context for user {user_id}")
        user_contexts[user_id] = ConversationContext()
    
    # Get the user's conversation context
    user_context = user_contexts[user_id]
    
    # Show typing indicator
    await update.message.chat.send_action(action="typing")
    
    try:
        # Generate response using the OpenAI assistant
        logger.debug("Calling OpenAI assistant to generate response")
        response = assistant.generate_response(user_context, user_message)
        logger.debug(f"Response generated: {response[:30]}...")
        
        # Send the response
        await update.message.reply_text(response)
        logger.debug("Response sent successfully")
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "I'm sorry, I encountered an error while processing your request. "
            "Please try again or contact support if the issue persists."
        )

def main() -> None:
    """Start the bot."""
    # Get the bot token from environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Telegram bot token not found in environment variables")
        return
    
    # Create the Application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    logger.info("Starting bot")
    application.run_polling()
    logger.info("Bot started")

if __name__ == "__main__":
    main()