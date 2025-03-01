import os
import logging
import signal
import time
import sys
import traceback
from typing import Dict, Any
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import NetworkError, TimedOut, TelegramError
from dotenv import load_dotenv
from simple_openai_engine import OpenAIAssistant, ConversationContext, test_openai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
user_contexts: Dict[int, ConversationContext] = {}
assistant = None
app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    user_id = update.effective_user.id
    logger.info(f"Start command received from user {user_id}")
    
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
    logger.info("Help command received")
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
    logger.info(f"Reset command received from user {user_id}")
    user_contexts[user_id] = ConversationContext()
    await update.message.reply_text("Our conversation has been reset. What would you like to know about our tours?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and generate responses using the OpenAI assistant."""
    if update is None or update.effective_user is None:
        logger.error("Received update with no effective user")
        return
        
    user_id = update.effective_user.id
    user_message = update.effective_message.text if update.effective_message else ""
    
    if not user_message:
        logger.warning(f"Received empty message from user {user_id}")
        await update.effective_message.reply_text("I received an empty message. Please send me a text message.")
        return
    
    logger.info(f"Message received from user {user_id}")
    logger.debug(f"Message content: '{user_message}'")
    
    # Check if assistant is initialized
    if assistant is None:
        logger.error("OpenAI assistant not initialized")
        await update.effective_message.reply_text("Sorry, the AI assistant is not available right now. Please try again later.")
        return
    
    # If this is a new user, create a conversation context
    if user_id not in user_contexts:
        logger.debug(f"Creating new context for user {user_id}")
        user_contexts[user_id] = ConversationContext()
    
    # Get the user's conversation context
    user_context = user_contexts[user_id]
    
    try:
        # Show typing indicator
        await update.effective_chat.send_action(action="typing")
        
        # Run OpenAI task in thread pool to avoid blocking
        response = await asyncio.to_thread(
            assistant.generate_response, user_context, user_message
        )
        
        # Ensure we have a valid response
        if not response or not isinstance(response, str):
            logger.error(f"Invalid response type: {type(response)}")
            response = "I apologize, but I received an invalid response. Please try again."
        
        # Send the response - break into chunks if too long
        if len(response) > 4000:
            chunks = []
            current_chunk = ""
            
            # Split by paragraphs
            for paragraph in response.split('\n\n'):
                if len(current_chunk + paragraph + '\n\n') > 4000:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n\n'
                else:
                    current_chunk += paragraph + '\n\n'
                    
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Send each chunk
            for chunk in chunks:
                if chunk:  # Make sure it's not empty
                    await update.effective_message.reply_text(chunk)
        else:
            await update.effective_message.reply_text(response)
        
        logger.info(f"Response sent to user {user_id}")
            
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            await update.effective_message.reply_text(
                "I'm sorry, I encountered an error while processing your request. Please try again in a moment."
            )
        except Exception:
            logger.error("Failed to send error message to user")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the telegram-python-bot framework."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. I've notified my developers about this issue."
            )
        except Exception as e:
            logger.error(f"Error sending error message to user: {e}")

async def run_bot():
    """Set up and run the bot as an async function."""
    global app, assistant
    
    try:
        # Get API credentials
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not bot_token or not openai_api_key:
            logger.error("Missing required environment variables. Check .env file.")
            return
        
        # Initialize OpenAI assistant
        logger.info("Initializing OpenAI Assistant...")
        assistant = OpenAIAssistant(None)
        
        # Build the application
        logger.info("Setting up Telegram bot...")
        builder = Application.builder().token(bot_token)
        app = builder.build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("reset", reset))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("Starting bot...")
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        logger.info("Bot is running!")
        
        # Keep the bot running until stopped
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.critical(f"Critical bot error: {e}")
        logger.critical(traceback.format_exc())
    finally:
        # Ensure proper cleanup
        logger.info("Shutting down...")
        if app:
            await app.stop()
            await app.shutdown()

if __name__ == "__main__":
    try:
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            logger.info("Received signal to terminate. Shutting down...")
            if app:
                # Use asyncio.run to stop the app
                async def stop_app():
                    try:
                        await app.stop()
                        await app.shutdown()
                    except Exception as e:
                        logger.error(f"Error during shutdown: {e}")
                
                try:
                    # Create a loop if necessary
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                    loop.run_until_complete(stop_app())
                except Exception as e:
                    logger.error(f"Failed to stop app gracefully: {e}")
            
            sys.exit(0)
            
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting TripUAE Assistant Bot")
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.critical(traceback.format_exc())