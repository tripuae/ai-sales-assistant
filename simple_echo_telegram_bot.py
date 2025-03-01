import os
import requests
import time
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def echo_bot():
    """
    A minimal Telegram bot that just echoes back what you say.
    This helps test if the Telegram bot token is working correctly.
    """
    # Load environment variables
    load_dotenv()
    
    # Get token
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return
    
    # Remove quotes if they exist
    if (token.startswith("'") and token.endswith("'")) or \
       (token.startswith('"') and token.endswith('"')):
        token = token[1:-1]
        logger.info("Removed quotes from token")
    
    logger.info(f"Using token: {token[:5]}...{token[-5:]}")
    
    # Test connection
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code != 200:
            logger.error(f"Failed to connect to Telegram: {response.text}")
            return
        
        bot_info = response.json()
        logger.info(f"Connected as: {bot_info['result']['first_name']} (@{bot_info['result']['username']})")
    except Exception as e:
        logger.error(f"Error connecting to Telegram: {e}")
        return
    
    # Main polling loop
    offset = None
    logger.info("Starting bot polling. Press Ctrl+C to stop.")
    print("Bot started! Send a message to your bot on Telegram.")
    
    try:
        while True:
            try:
                # Get updates with increased timeout
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                params = {"timeout": 30}
                if offset:
                    params["offset"] = offset
                
                response = requests.get(url, params=params)
                updates = response.json()
                
                if not updates.get("ok"):
                    logger.error(f"Error getting updates: {updates}")
                    time.sleep(5)
                    continue
                
                # Process updates
                for update in updates.get("result", []):
                    # Update offset
                    offset = update["update_id"] + 1
                    
                    # Check for message
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        user = update["message"]["from"]["first_name"]
                        
                        # Log received message
                        logger.info(f"Received from {user}: {text}")
                        
                        # Process commands
                        if text.startswith('/'):
                            if text == '/start':
                                send_message(token, chat_id, "Hello! I'm a simple echo bot. Send me a message and I'll repeat it back to you.")
                            elif text == '/help':
                                send_message(token, chat_id, "Send me any message and I'll echo it back.")
                            else:
                                send_message(token, chat_id, f"Unknown command: {text}")
                        else:
                            # Echo back normal messages
                            send_message(token, chat_id, f"You said: {text}")
                
                # Small delay
                time.sleep(1)
                
            except requests.RequestException as e:
                logger.error(f"Network error: {e}")
                time.sleep(5)
                
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def send_message(token, chat_id, text):
    """Send a message through the Telegram API"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(url, json=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to send message: {response.text}")
            return False
        
        logger.info(f"Message sent: {text[:30]}...")
        return True
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False

if __name__ == "__main__":
    echo_bot()
