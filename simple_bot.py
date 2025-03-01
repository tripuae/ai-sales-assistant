#!/usr/bin/env python3
"""
Super simple implementation of the TripUAE Assistant Telegram Bot.
This version has minimal dependencies and error handling to maximize chances of working.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === BASIC SETUP ===

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
print("Loading environment variables from .env file...")
load_dotenv(override=True)

# Get API tokens from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Print the first and last few characters of each token for verification
if TELEGRAM_TOKEN:
    masked_token = TELEGRAM_TOKEN[:4] + "..." + TELEGRAM_TOKEN[-4:] 
    print(f"Found Telegram token: {masked_token}")
else:
    print("ERROR: TELEGRAM_BOT_TOKEN not found in environment")

if OPENAI_API_KEY:
    masked_key = OPENAI_API_KEY[:4] + "..." + OPENAI_API_KEY[-4:]
    print(f"Found OpenAI API key: {masked_key}")
else:
    print("ERROR: OPENAI_API_KEY not found in environment")

# Check for required credentials
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    logger.error("Missing API credentials. Please set TELEGRAM_BOT_TOKEN and OPENAI_API_KEY in your .env file")
    sys.exit(1)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# === CONVERSATION HANDLING ===

# Store user conversations
user_conversations = {}

def get_user_messages(user_id):
    """Get or create conversation history for a user"""
    if user_id not in user_conversations:
        # Start with system message
        user_conversations[user_id] = [
            {"role": "system", "content": (
                "You are TripUAE Assistant, a helpful guide for tourists visiting UAE. "
                "You provide information about tours and activities in Dubai and the UAE. "
                "Always be friendly, concise, and helpful. If you don't know specific information, "
                "politely say so and offer to help with other questions about UAE tourism."
            )}
        ]
    return user_conversations[user_id]

def generate_response(user_id, user_message):
    """Generate a response using OpenAI"""
    # Get user's message history
    messages = get_user_messages(user_id)
    
    # Add user's new message
    messages.append({"role": "user", "content": user_message})
    
    try:
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract assistant's message
        assistant_message = response.choices[0].message.content
        
        # Add assistant's response to conversation history
        messages.append({"role": "assistant", "content": assistant_message})
        
        # Limit conversation history to prevent token overflow
        if len(messages) > 10:
            # Keep system message and last 9 messages
            messages = [messages[0]] + messages[-9:]
        
        return assistant_message
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "I'm sorry, I'm having trouble connecting to my system right now. Please try again in a moment."

# === TELEGRAM HANDLERS ===

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start command is issued"""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started conversation")
    
    # Reset conversation history
    user_conversations[user_id] = [
        {"role": "system", "content": (
            "You are TripUAE Assistant, a helpful guide for tourists visiting UAE. "
            "You provide information about tours and activities in Dubai and the UAE. "
            "Always be friendly, concise, and helpful."
        )}
    ]
    
    await update.message.reply_text(
        "👋 Welcome to TripUAE Assistant! I can help you discover tours and activities in Dubai and UAE.\n\n"
        "How may I assist you today?"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help info when /help command is issued"""
    await update.message.reply_text(
        "Here are some things you can ask me:\n\n"
        "• What tours do you offer?\n"
        "• Tell me about desert safaris\n"
        "• How much is the Dubai city tour?\n"
        "• What's included in the night cruise?"
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset conversation when /reset command is issued"""
    user_id = update.effective_user.id
    
    # Reset conversation history
    user_conversations[user_id] = [
        {"role": "system", "content": (
            "You are TripUAE Assistant, a helpful guide for tourists visiting UAE. "
            "You provide information about tours and activities in Dubai and the UAE. "
            "Always be friendly, concise, and helpful."
        )}
    ]
    
    await update.message.reply_text("I've reset our conversation. How can I help you now?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming user messages"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"Message from User {user_id}: {user_message[:20]}...")
    
    # Show typing indicator
    await update.effective_chat.send_action(action="typing")
    
    try:
        # Process message in a non-blocking way
        response = await asyncio.to_thread(generate_response, user_id, user_message)
        
        # Send response, split if necessary
        if len(response) > 4000:
            # Split by paragraphs to avoid breaking mid-sentence
            parts = []
            current_part = ""
            
            for paragraph in response.split('\n\n'):
                if len(current_part) + len(paragraph) + 2 > 4000:
                    parts.append(current_part.strip())
                    current_part = paragraph + '\n\n'
                else:
                    current_part += paragraph + '\n\n'
            
            if current_part.strip():
                parts.append(current_part.strip())
                
            # Send each part
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("I'm sorry, something went wrong. Please try again.")

# === MAIN FUNCTION ===

async def main():
    """Run the bot"""
    logger.info("Starting TripUAE Assistant bot")
    
    # Create the Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("Bot started successfully!")
    
    # Keep the bot running
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        # Proper shutdown
        logger.info("Shutting down...")
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
