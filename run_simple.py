#!/usr/bin/env python3
"""
Simplified launcher for the TripUAE Assistant Telegram Bot
This version uses minimal error handling to avoid complexity
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from simple_openai_engine import OpenAIAssistant, ConversationContext

# Set up basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Store user conversations
user_contexts = {}
assistant = None

# Command handlers
async def start_command(update, context):
    await update.message.reply_text(
        "👋 Welcome to TripUAE Assistant! Ask me about tours in Dubai and UAE."
    )
    user_id = update.effective_user.id
    user_contexts[user_id] = ConversationContext()

async def help_command(update, context):
    await update.message.reply_text(
        "You can ask me about desert safaris, city tours, or cruises. "
        "I can provide information about prices and what's included."
    )

async def reset_command(update, context):
    user_id = update.effective_user.id
    user_contexts[user_id] = ConversationContext()
    await update.message.reply_text("Conversation reset. How can I help you?")

# Message handler
async def handle_message(update, context):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # Create context if needed
    if user_id not in user_contexts:
        user_contexts[user_id] = ConversationContext()
    
    # Show typing...
    await update.effective_chat.send_action(action="typing")
    
    # Get response (use asyncio.to_thread to not block)
    try:
        response = await asyncio.to_thread(
            assistant.generate_response,
            user_contexts[user_id],
            user_text
        )
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "Sorry, I encountered an error. Please try again."
        )

async def main():
    global assistant

    # Initialize OpenAI assistant
    assistant = OpenAIAssistant(None)
    
    # Initialize bot
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep running
    print("Bot is running! Press Ctrl+C to stop.")
    
    # Keep the application running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
