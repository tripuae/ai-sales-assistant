import os
import sys
import requests
import time
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hardcoded token from your .env file
TELEGRAM_TOKEN = "7520286452:AAHEjYROx3L8pdBduHF-0EqMz-VLRBlvcUc"  # This is your token from the .env file
CLAUDE_API_KEY = "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"  # Your Claude API key

class ConversationContext:
    """Store conversation history for each user"""
    def __init__(self):
        self.messages = []
    
    def add_message(self, role, content):
        """Add a message to conversation history"""
        self.messages.append({"role": role, "content": content})
        # Keep context at a reasonable size
        if len(self.messages) > 10:
            self.messages = self.messages[-10:]

class DirectTokenTelegramBot:
    """A Telegram bot that directly uses the token without environment variables"""
    
    def __init__(self):
        """Initialize the bot"""
        # Use hardcoded tokens
        self.telegram_token = TELEGRAM_TOKEN
        self.claude_api_key = CLAUDE_API_KEY
        
        logger.info(f"Telegram token: {self.telegram_token[:5]}...{self.telegram_token[-5:]}")
        logger.info(f"Claude API key: {self.claude_api_key[:5]}...{self.claude_api_key[-5:]}")
        
        # Claude model and setup
        self.claude_model = "claude-3-7-sonnet-20250219"
        logger.info(f"Using Claude model: {self.claude_model}")
        
        # System message for Claude
        self.system_message = """
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        
        Desert Safari prices:
        - Standard: 150 AED per person
        - Premium: 250 AED per person
        - VIP: 350 AED per person
        
        Dubai City Tour prices:
        - Half Day: 120 AED per person
        - Full Day: 200 AED per person
        - Private Tour: 500 AED (up to 4 people)
        
        Night Cruise prices:
        - Standard: 180 AED per person
        - Dinner Cruise: 280 AED per person
        - Luxury Cruise: 400 AED per person
        
        For all inquiries, provide detailed yet concise responses about the experiences.
        """
        
        # User context storage
        self.user_contexts = {}
        
        # Bot setup
        self.api_url = f"https://api.telegram.org/bot{self.telegram_token}"
        self.offset = 0
    
    def generate_claude_response(self, context, user_message, chat_id=None):
        """Generate response using Claude API"""
        # Add user message to context
        context.add_message("user", user_message)
        
        if chat_id:
            logger.info(f"Generating Claude response for chat {chat_id}")
            # Send typing indicator
            self.send_chat_action(chat_id, "typing")
        
        try:
            # Format messages for Claude API
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in context.messages]
            
            # Make Claude API request
            logger.info(f"Sending request to Claude API")
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.claude_model,
                    "system": self.system_message,
                    "messages": messages,
                    "max_tokens": 1000
                }
            )
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('content', [{'text': 'No response from Claude'}])[0].get('text')
                logger.info(f"Claude response received ({len(response_text)} chars)")
                
                # Add response to context
                context.add_message("assistant", response_text)
                return response_text
            else:
                error_msg = f"Claude API error: {response.status_code} - {response.text[:100]}"
                logger.error(error_msg)
                return f"Sorry, I encountered a technical issue: {response.status_code}"
        
        except Exception as e:
            logger.error(f"Error generating Claude response: {str(e)}")
            return "Sorry, I encountered an error. Please try again later."
    
    def send_message(self, chat_id, text):
        """Send a message through Telegram API"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text
            }
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                logger.info(f"Message sent to chat {chat_id}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text[:100]}")
                return False
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    def send_chat_action(self, chat_id, action="typing"):
        """Send chat action (typing indicator)"""
        try:
            url = f"{self.api_url}/sendChatAction"
            data = {
                "chat_id": chat_id,
                "action": action
            }
            requests.post(url, json=data)
        except Exception as e:
            logger.error(f"Error sending chat action: {str(e)}")
    
    def handle_message(self, message):
        """Process incoming message"""
        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        text = message.get("text", "")
        username = message.get("from", {}).get("username", "unknown")
        
        logger.info(f"Received message from {username} (ID: {user_id}): {text}")
        
        # Create context if needed
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = ConversationContext()
        
        # Handle commands
        if text.startswith('/'):
            if text == "/start":
                self.user_contexts[user_id] = ConversationContext()
                return self.send_message(chat_id, "Welcome to TripUAE Assistant! How can I help you today?")
            elif text == "/help":
                return self.send_message(chat_id, "I can provide information about TripUAE's tours including Desert Safari, Dubai City Tour, and Night Cruise.")
            elif text == "/reset":
                self.user_contexts[user_id] = ConversationContext()
                return self.send_message(chat_id, "Conversation history has been reset.")
            else:
                return self.send_message(chat_id, f"Unknown command: {text}")
        
        # Generate response
        response = self.generate_claude_response(self.user_contexts[user_id], text, chat_id)
        
        # Handle long messages
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                self.send_message(chat_id, chunk)
        else:
            self.send_message(chat_id, response)
    
    def start_polling(self):
        """Start the polling loop"""
        logger.info("Starting bot polling")
        
        # Verify bot connection
        try:
            response = requests.get(f"{self.api_url}/getMe")
            if response.status_code != 200 or not response.json().get("ok"):
                logger.error(f"Bot verification failed: {response.status_code} - {response.text}")
                print("\n❌ Bot verification failed!")
                print("Please check that your Telegram token is correct.")
                return
            
            bot_info = response.json()["result"]
            print(f"\n✅ Connected to Telegram as @{bot_info.get('username')} ({bot_info.get('first_name')})")
        except Exception as e:
            logger.error(f"Error verifying bot: {e}")
            print(f"\n❌ Could not connect to Telegram API: {e}")
            return
        
        # Main polling loop
        print("\nBot is running! Send a message to your bot on Telegram.")
        print("Press Ctrl+C to stop.")
        
        while True:
            try:
                # Get updates
                params = {"offset": self.offset, "timeout": 30}
                response = requests.get(f"{self.api_url}/getUpdates", params=params)
                
                if response.status_code == 200:
                    updates = response.json()
                    if updates.get("ok"):
                        for update in updates.get("result", []):
                            # Update offset
                            self.offset = update["update_id"] + 1
                            
                            # Process message
                            if "message" in update and "text" in update["message"]:
                                self.handle_message(update["message"])
                else:
                    logger.error(f"Error getting updates: {response.status_code} - {response.text}")
                    time.sleep(5)
                
                time.sleep(0.5)  # Small delay
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                print("\nBot stopped.")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {str(e)}")
                time.sleep(5)

def main():
    """Main function"""
    print("Starting TripUAE Telegram Bot with Direct Token...")
    
    # Create and start bot
    bot = DirectTokenTelegramBot()
    bot.start_polling()

if __name__ == "__main__":
    main()
