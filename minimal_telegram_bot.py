import os
import sys
import requests
import time
import json
from dotenv import load_dotenv
from threading import Thread

# Import Claude integration directly
from direct_claude_engine import ClaudeAssistant, ConversationContext
from data_loader import create_database

class SimpleTelegramBot:
    """
    A simple Telegram bot that uses direct API calls instead of the python-telegram-bot library.
    This avoids the compatibility issues with the library.
    """
    def __init__(self, token, claude_assistant):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.claude_assistant = claude_assistant
        self.offset = 0
        self.running = False
        self.user_contexts = {}  # Store conversation contexts for each user
        
    def send_message(self, chat_id, text):
        """Send a message to a Telegram chat"""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"  # Enable markdown formatting
        }
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def get_updates(self):
        """Get new messages from Telegram"""
        url = f"{self.api_url}/getUpdates"
        params = {
            "offset": self.offset,
            "timeout": 30
        }
        try:
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            print(f"Error getting updates: {e}")
            return {"ok": False}
    
    def process_message(self, message):
        """Process a single message"""
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")
        
        # Handle commands
        if text.startswith("/"):
            if text == "/start":
                self.user_contexts[user_id] = ConversationContext()
                return self.send_message(chat_id, 
                    "Welcome to TripUAE Assistant powered by Claude!\n\n"
                    "I can help you with information about our tours including Desert Safari, "
                    "Dubai City Tour, and Night Cruise.\n\n"
                    "How can I assist you today?")
            elif text == "/help":
                return self.send_message(chat_id,
                    "I can provide information about TripUAE's tours.\n\n"
                    "You can ask me about:\n"
                    "- Tour details and highlights\n"
                    "- Pricing information\n"
                    "- Booking procedures\n"
                    "- Practical information\n\n"
                    "Commands:\n"
                    "/start - Start a new conversation\n"
                    "/help - Show this help message\n"
                    "/reset - Reset your conversation history")
            elif text == "/reset":
                self.user_contexts[user_id] = ConversationContext()
                return self.send_message(chat_id, "Conversation history has been reset.")
        
        # Get or create user's conversation context
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = ConversationContext()
        
        # Generate a typing indicator
        typing_url = f"{self.api_url}/sendChatAction"
        typing_data = {
            "chat_id": chat_id,
            "action": "typing"
        }
        requests.post(typing_url, json=typing_data)
        
        # Generate response using Claude
        try:
            response_text = self.claude_assistant.generate_response(self.user_contexts[user_id], text)
            
            # Handle long responses (Telegram has 4096 character limit)
            if len(response_text) > 4000:
                chunks = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
                for chunk in chunks:
                    self.send_message(chat_id, chunk)
                return
            else:
                return self.send_message(chat_id, response_text)
        except Exception as e:
            print(f"Error generating response: {e}")
            return self.send_message(chat_id, "I'm having trouble responding right now. Please try again later.")
    
    def process_update(self, update):
        """Process a single update from Telegram"""
        update_id = update.get("update_id")
        self.offset = update_id + 1
        
        message = update.get("message")
        if message:
            self.process_message(message)
    
    def start(self):
        """Start the bot polling loop"""
        self.running = True
        print("🤖 Bot started! Press Ctrl+C to stop.")
        
        try:
            while self.running:
                updates = self.get_updates()
                if updates.get("ok", False):
                    for update in updates.get("result", []):
                        self.process_update(update)
                time.sleep(1)
        except KeyboardInterrupt:
            print("Bot stopped by user.")
        except Exception as e:
            print(f"Error in bot loop: {e}")
            self.running = False

def main():
    """Main function to run the bot"""
    # Load environment variables
    load_dotenv()
    
    # Get the API token
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not found.")
        print("Please set it in your .env file or export it.")
        sys.exit(1)
    
    # Initialize Claude assistant
    price_db = create_database()
    claude_assistant = ClaudeAssistant(price_db)
    
    # Create and start the bot
    bot = SimpleTelegramBot(token, claude_assistant)
    
    print(f"Starting TripUAE Assistant bot...")
    bot.start()

if __name__ == "__main__":
    main()
