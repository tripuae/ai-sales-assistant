import os
import sys
import json
import requests
import time
from typing import Dict, Any
from threading import Thread, Event
from dotenv import load_dotenv

# Load the environment variables for API keys
load_dotenv()

class ConversationContext:
    def __init__(self):
        """Initialize an empty conversation context with no messages."""
        self.messages = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation context."""
        self.messages.append({"role": role, "content": content})

class ClaudeAssistant:
    def __init__(self, system_message: str):
        """
        Initialize Claude assistant with direct API access.
        
        Args:
            system_message: System instructions for Claude
        """
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.system_message = system_message
        
        # Test the API connection and find available models
        self.model = self._find_best_model()
        print(f"Using Claude model: {self.model}")
    
    def _find_best_model(self):
        """Find the best available Claude model for the API key."""
        try:
            response = requests.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            
            if response.status_code == 200:
                models_data = response.json()
                # Preferred models in order
                preferred_models = [
                    "claude-3-7-sonnet-20250219",
                    "claude-3-5-sonnet-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240229",
                    "claude-3-opus",
                    "claude-3-sonnet",
                    "claude-3-haiku",
                    "claude-2.0",
                    "claude-2"
                ]
                
                available_model_ids = [model.get("id") for model in models_data.get("data", [])]
                
                # Find the first preferred model that's available
                for model in preferred_models:
                    if model in available_model_ids:
                        return model
                
                # If none of the preferred models are available, return the first available one
                if available_model_ids:
                    return available_model_ids[0]
            
            # Default to a recent model if the API call fails
            return "claude-3-sonnet-20240229"
            
        except Exception as e:
            print(f"Error finding models: {e}")
            # Fallback to a recent model
            return "claude-3-sonnet-20240229"
    
    def generate_response(self, context: ConversationContext, user_message: str) -> str:
        """
        Generate a response using Claude API.
        
        Args:
            context: Conversation context with message history
            user_message: The latest user message
            
        Returns:
            str: Claude's response
        """
        try:
            # Add user message to context
            context.add_message("user", user_message)
            
            # Format messages for API
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in context.messages]
            
            # Call Claude API
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model,
                    "system": self.system_message,
                    "messages": messages,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code != 200:
                error_msg = f"API error: {response.status_code} - {response.text}"
                print(error_msg)
                return f"Sorry, I encountered an error: {error_msg}"
                
            # Extract response text
            data = response.json()
            response_text = data.get("content", [{"text": "No response"}])[0].get("text")
            
            # Add assistant response to context
            context.add_message("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return error_message

class DirectTelegramBot:
    """
    A Telegram bot implementation that uses direct HTTP API calls
    and doesn't depend on external libraries.
    """
    
    def __init__(self, token: str, claude_assistant: ClaudeAssistant):
        """
        Initialize the Telegram bot.
        
        Args:
            token: Telegram Bot API token
            claude_assistant: Claude assistant for generating responses
        """
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.claude = claude_assistant
        self.offset = 0
        self.user_contexts: Dict[int, ConversationContext] = {}
        self.stop_event = Event()
    
    def send_message(self, chat_id: int, text: str) -> Dict[str, Any]:
        """
        Send a message to a chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            
        Returns:
            Dict: API response
        """
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"  # Support markdown formatting
        }
        
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return {"ok": False, "error": str(e)}
    
    def send_typing_action(self, chat_id: int) -> None:
        """
        Send typing action to indicate the bot is generating a response.
        
        Args:
            chat_id: Telegram chat ID
        """
        url = f"{self.api_url}/sendChatAction"
        data = {
            "chat_id": chat_id,
            "action": "typing"
        }
        
        try:
            requests.post(url, json=data)
        except Exception as e:
            print(f"Error sending typing action: {e}")
    
    def get_updates(self) -> Dict[str, Any]:
        """
        Get updates from Telegram API.
        
        Returns:
            Dict: Updates from Telegram
        """
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
            return {"ok": False, "error": str(e)}
    
    def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process a message from a user.
        
        Args:
            message: Telegram message object
        """
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")
        user_name = message.get("from", {}).get("first_name", "User")
        
        print(f"Received message from {user_name} ({user_id}): {text}")
        
        # Handle commands
        if text.startswith("/"):
            if text == "/start":
                # Reset or create new conversation context
                self.user_contexts[user_id] = ConversationContext()
                self.send_message(chat_id, 
                    "👋 *Welcome to TripUAE Assistant!*\n\n"
                    "I can help you with information about our tours:\n"
                    "• Desert Safari\n"
                    "• Dubai City Tour\n"
                    "• Night Cruise\n\n"
                    "How can I assist you today?")
                return
            elif text == "/help":
                self.send_message(chat_id,
                    "*TripUAE Assistant Help*\n\n"
                    "I can provide information about our tours:\n\n"
                    "You can ask me about:\n"
                    "• Tour details and highlights\n"
                    "• Pricing information\n"
                    "• Booking procedures\n"
                    "• Practical information\n\n"
                    "*Commands:*\n"
                    "/start - Start a new conversation\n"
                    "/help - Show this help message\n"
                    "/reset - Reset your conversation history")
                return
            elif text == "/reset":
                self.user_contexts[user_id] = ConversationContext()
                self.send_message(chat_id, "✓ Conversation history has been reset.")
                return
        
        # Get or create user context
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = ConversationContext()
        
        # Send typing indicator
        self.send_typing_action(chat_id)
        
        # Generate response using Claude
        response = self.claude.generate_response(self.user_contexts[user_id], text)
        
        # Handle potential long responses
        if len(response) > 4000:
            # Split long messages
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                self.send_message(chat_id, chunk)
        else:
            self.send_message(chat_id, response)
    
    def poll_updates(self) -> None:
        """Poll for updates in a loop."""
        print("Starting update polling...")
        
        while not self.stop_event.is_set():
            try:
                updates = self.get_updates()
                
                if updates.get("ok", False):
                    for update in updates.get("result", []):
                        # Update offset for long polling
                        self.offset = max(self.offset, update.get("update_id", 0) + 1)
                        
                        # Process message if present
                        if "message" in update:
                            self.process_message(update["message"])
                
                time.sleep(1)
            except Exception as e:
                print(f"Error polling updates: {e}")
                time.sleep(5)  # Wait a bit longer if there's an error
    
    def start(self) -> None:
        """Start the bot in a separate thread."""
        self.stop_event.clear()
        Thread(target=self.poll_updates).start()
        print("Bot started in background thread.")
    
    def stop(self) -> None:
        """Stop the bot."""
        self.stop_event.set()
        print("Bot stopping...")

def main():
    """Main function to run the bot directly."""
    # Load environment variables
    load_dotenv()
    
    # Get API token
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
        sys.exit(1)
    
    # Create Claude assistant
    system_message = """
    You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
    You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
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
    """
    
    claude = ClaudeAssistant(system_message)
    
    # Create and start bot
    bot = DirectTelegramBot(token, claude)
    
    try:
        print("Starting bot. Press Ctrl+C to stop.")
        bot.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping bot...")
        bot.stop()

if __name__ == "__main__":
    main()
