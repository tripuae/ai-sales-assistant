import os
import sys
import json
import requests
import time
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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


class ClaudeTelegramBot:
    """A Telegram bot that uses Claude API directly"""
    
    def __init__(self):
        """Initialize the bot"""
        # Get Telegram token
        self.telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not self.telegram_token:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            sys.exit(1)
        logger.info(f"Telegram token: {self.telegram_token[:5]}...{self.telegram_token[-5:]}")
        
        # Get Claude API key
        self.claude_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.claude_api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment variables")
            sys.exit(1)
        logger.info(f"Claude API key: {self.claude_api_key[:5]}...{self.claude_api_key[-5:]}")
        
        # Claude model and setup
        self.claude_model = "claude-3-7-sonnet-20250219"  # Using the known working model
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
        # First, add user message to context
        context.add_message("user", user_message)
        
        if chat_id:
            logger.info(f"Generating Claude response for chat {chat_id}")
            # Send typing indicator while generating response
            self.send_chat_action(chat_id, "typing")
        
        try:
            # Format messages for Claude API
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in context.messages]
            
            # Make Claude API request
            logger.info(f"Sending request to Claude API with {len(messages)} messages")
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
            
            # Check if response is successful
            if response.status_code == 200:
                # Parse the response
                data = response.json()
                response_text = data.get('content', [{'text': 'No response from Claude'}])[0].get('text')
                logger.info(f"Claude response received ({len(response_text)} chars)")
                
                # Add Claude's response to context
                context.add_message("assistant", response_text)
                return response_text
            else:
                # Log error
                error_msg = f"Claude API error: {response.status_code} - {response.text[:300]}"
                logger.error(error_msg)
                return f"I'm having trouble connecting to my AI brain. Technical error: {response.status_code}"
        
        except Exception as e:
            # Log exception
            logger.error(f"Error generating Claude response: {str(e)}")
            return "Sorry, I encountered an error while processing your request. Please try again later."
    
    def send_message(self, chat_id, text):
        """Send a message through Telegram API"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"  # Enable markdown formatting
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
    
    def handle_command(self, chat_id, user_id, command):
        """Handle Telegram bot commands"""
        if command == "/start":
            # Reset or initialize conversation context
            self.user_contexts[user_id] = ConversationContext()
            return self.send_message(chat_id, 
                "*Welcome to TripUAE Assistant!* 🌴\n\n"
                "I can help you with information about our Dubai tours:\n"
                "• Desert Safari\n"
                "• Dubai City Tour\n"
                "• Night Cruise\n\n"
                "How can I assist you today?"
            )
        elif command == "/help":
            return self.send_message(chat_id,
                "*TripUAE Assistant Help* 📋\n\n"
                "I can answer questions about our tours including:\n"
                "• Tour details and highlights\n"
                "• Pricing information\n"
                "• Booking procedures\n"
                "• Practical information\n\n"
                "*Available commands:*\n"
                "/start - Start a new conversation\n"
                "/help - Show this help message\n"
                "/reset - Clear conversation history"
            )
        elif command == "/reset":
            self.user_contexts[user_id] = ConversationContext()
            return self.send_message(chat_id, "✅ Conversation history has been reset.")
        else:
            return self.send_message(chat_id, f"Unknown command: {command}")
    
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
            return self.handle_command(chat_id, user_id, text)
        
        # Generate response using Claude
        self.send_chat_action(chat_id, "typing")
        
        # Debug: log that we're using Claude for this message
        logger.info(f"Generating Claude AI response for message: '{text}'")
        
        response = self.generate_claude_response(self.user_contexts[user_id], text, chat_id)
        
        # Debug: log the response from Claude
        logger.info(f"Claude response: '{response[:50]}...'")
        
        # Handle long messages (Telegram has 4096 character limit)
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                self.send_message(chat_id, chunk)
        else:
            self.send_message(chat_id, response)
    
    def start_polling(self):
        """Start the polling loop"""
        logger.info("Starting bot polling")
        
        try:
            # Verify bot can connect to Telegram
            response = requests.get(f"{self.api_url}/getMe")
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get("ok"):
                    bot_name = bot_info["result"]["first_name"]
                    bot_username = bot_info["result"].get("username")
                    logger.info(f"Connected as: {bot_name} (@{bot_username})")
                else:
                    logger.error(f"Bot verification failed: {bot_info}")
                    return
            else:
                logger.error(f"Bot verification failed: {response.status_code} - {response.text}")
                return
            
            # Test Claude API connection
            logger.info("Testing Claude API connection...")
            test_context = ConversationContext()
            test_response = self.generate_claude_response(test_context, "Test message - please respond with 'Claude API is working'")
            if "working" in test_response.lower() or "claude" in test_response.lower():
                logger.info(f"Claude API test successful: '{test_response[:50]}...'")
            else:
                logger.warning(f"Claude API test response unclear: '{test_response[:50]}...'")
            
            # Main polling loop
            logger.info("Starting main polling loop")
            print("Bot is running! Send a message to your bot on Telegram.")
            print("Press Ctrl+C to stop.")
            
            while True:
                try:
                    # Get updates from Telegram with timeout
                    updates_response = requests.get(
                        f"{self.api_url}/getUpdates",
                        params={"offset": self.offset, "timeout": 30}
                    )
                    
                    if updates_response.status_code == 200:
                        updates = updates_response.json()
                        
                        if updates.get("ok"):
                            for update in updates.get("result", []):
                                # Update offset to acknowledge this update
                                self.offset = update["update_id"] + 1
                                
                                # Process message if present
                                if "message" in update and "text" in update["message"]:
                                    self.handle_message(update["message"])
                        else:
                            logger.error(f"Error in updates response: {updates}")
                    else:
                        logger.error(f"Failed to get updates: {updates_response.status_code} - {updates_response.text[:100]}")
                        time.sleep(5)  # Wait longer before retry
                
                except KeyboardInterrupt:
                    logger.info("Bot stopped by user")
                    print("\nBot stopped.")
                    break
                except Exception as e:
                    logger.error(f"Error in polling loop: {str(e)}")
                    time.sleep(5)  # Wait before retry
                    
                # Small delay to avoid hitting rate limits
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Critical bot error: {str(e)}")

def main():
    """Main function"""
    print("Starting TripUAE Telegram Bot with Claude AI integration...")
    
    # Create and start bot
    bot = ClaudeTelegramBot()
    bot.start_polling()

if __name__ == "__main__":
    main()
