#!/usr/bin/env python3
"""
Test script for Telegram Bot API connection
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the bot token
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    print("Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
    print("Make sure you have a .env file with your bot token.")
    exit(1)

print(f"Found bot token: {token[:4]}...{token[-4:]}")

# Define the async function to test the bot
async def test_telegram_bot():
    try:
        from telegram import Bot
        
        # Create a bot instance
        print("Creating bot instance...")
        bot = Bot(token=token)
        
        # Get bot information (this requires await with newer python-telegram-bot versions)
        print("Getting bot information...")
        bot_info = await bot.get_me()
        
        print("\nSuccess! Bot information:")
        print(f"Username: @{bot_info.username}")
        print(f"Name: {bot_info.first_name}")
        print(f"Bot ID: {bot_info.id}")
        print("\nYour Telegram bot token is working correctly.")
        return True
    
    except Exception as e:
        print(f"Error connecting to Telegram Bot API: {e}")
        print("\nPossible issues:")
        print("1. Your bot token might be invalid")
        print("2. There could be a network/firewall issue")
        print("3. Telegram API might be experiencing issues")
        return False

# Run the async function
if __name__ == "__main__":
    # Use asyncio to run our async function
    result = asyncio.run(test_telegram_bot())
    # Exit with appropriate status code
    exit(0 if result else 1)
