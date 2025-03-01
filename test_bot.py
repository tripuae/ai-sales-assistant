import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

def test_environment():
    """Test if environment variables are properly loaded."""
    load_dotenv()
    
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OpenAI API key not found in environment variables")
        return False
    else:
        logger.info(f"OpenAI API key found: {openai_api_key[:5]}...")
    
    # Check for Telegram bot token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Telegram bot token not found in environment variables")
        return False
    else:
        logger.info(f"Telegram bot token found: {bot_token[:5]}...")
    
    return True

def test_telegram_connection():
    """Test connection to the Telegram API."""
    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    try:
        from telegram import Bot
        from telegram.error import InvalidToken, Unauthorized
        
        bot = Bot(token=bot_token)
        bot_info = bot.get_me()
        logger.info(f"Successfully connected to Telegram as @{bot_info.username} (ID: {bot_info.id})")
        return True
    except InvalidToken:
        logger.error("Invalid Telegram bot token")
        return False
    except Unauthorized:
        logger.error("Unauthorized: The token is valid but was revoked or the bot was blocked by the user")
        return False
    except Exception as e:
        logger.error(f"Error connecting to Telegram: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_openai_connection():
    """Test connection to the OpenAI API."""
    from simple_openai_engine import test_openai
    return test_openai()

def run_tests():
    """Run all tests and report results."""
    logger.info("Running diagnostic tests...")
    
    # Test 1: Environment variables
    logger.info("Test 1: Checking environment variables...")
    if not test_environment():
        logger.error("Environment test failed")
        return False
    logger.info("Environment test passed")
    
    # Test 2: OpenAI API connection
    logger.info("Test 2: Testing OpenAI API connection...")
    if not test_openai_connection():
        logger.error("OpenAI API connection test failed")
        return False
    logger.info("OpenAI API connection test passed")
    
    # Test 3: Telegram bot connection
    logger.info("Test 3: Testing Telegram bot connection...")
    if not test_telegram_connection():
        logger.error("Telegram bot connection test failed")
        return False
    logger.info("Telegram bot connection test passed")
    
    logger.info("All tests passed!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
