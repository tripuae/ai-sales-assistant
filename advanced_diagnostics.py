import os
import sys
import logging
import platform
import json
import subprocess
import traceback
from dotenv import load_dotenv, find_dotenv

# Configure detailed logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("diagnostics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_python_environment():
    """Check Python version and environment details"""
    logger.info("=== Python Environment ===")
    logger.info(f"Python Version: {platform.python_version()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Working Directory: {os.getcwd()}")
    
    # Check virtual environment
    in_virtualenv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    logger.info(f"Running in virtual environment: {in_virtualenv}")
    
    # Log path info
    logger.info(f"Python Path: {sys.executable}")
    logger.info(f"Path Variable: {os.environ.get('PATH')}")
    
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    logger.info("=== Checking Dependencies ===")
    
    required_packages = [
        "python-telegram-bot",
        "openai",
        "python-dotenv",
        "tenacity"
    ]
    
    missing_packages = []
    version_info = {}
    
    for package in required_packages:
        try:
            # Try to import the package to verify it's installed
            if package == "python-telegram-bot":
                import telegram
                version_info[package] = telegram.__version__
            elif package == "openai":
                import openai
                version_info[package] = getattr(openai, "__version__", "unknown")
            elif package == "python-dotenv":
                import dotenv
                version_info[package] = dotenv.__version__
            elif package == "tenacity":
                import tenacity
                version_info[package] = tenacity.__version__
            
            logger.info(f"✓ {package} (version: {version_info.get(package, 'unknown')})")
        except ImportError:
            logger.error(f"✗ {package} is not installed")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Try installing them with: pip install " + " ".join(missing_packages))
        return False
    
    # Specifically check OpenAI version
    import openai
    openai_version = getattr(openai, "__version__", "unknown")
    logger.info(f"OpenAI package version: {openai_version}")
    
    # Check if using v0.x or v1.x
    is_v1 = openai_version.startswith("1.")
    logger.info(f"Using OpenAI API v1: {is_v1}")
    
    return True

def check_env_variables():
    """Check if environment variables are properly set"""
    logger.info("=== Checking Environment Variables ===")
    
    # Try to find .env file
    dotenv_path = find_dotenv()
    if not dotenv_path:
        logger.warning("No .env file found")
    else:
        logger.info(f".env file found at: {dotenv_path}")
    
    # Load environment variables
    load_dotenv()
    
    # Check OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not openai_api_key:
        logger.error("OPENAI_API_KEY is not set")
        return False
    else:
        prefix = openai_api_key[:7]  # Show just a prefix for security
        logger.info(f"OPENAI_API_KEY starts with: {prefix}...")
        
        # Check if it's a valid format
        if not (prefix.startswith("sk-") or prefix.startswith("org-")):
            logger.warning("OPENAI_API_KEY doesn't start with 'sk-' or 'org-', it might be invalid")
    
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set")
        return False
    else:
        # Check if token contains a colon (standard format is number:string)
        if ":" not in telegram_token:
            logger.warning("TELEGRAM_BOT_TOKEN doesn't contain a colon, it might be invalid")
            logger.info("Telegram bot tokens should have format like: 1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        else:
            logger.info(f"TELEGRAM_BOT_TOKEN appears to be in correct format")
    
    return True

def test_openai_connection():
    """Test connection to OpenAI API"""
    logger.info("=== Testing OpenAI API Connection ===")
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("No OpenAI API key found")
        return False
    
    # Try new OpenAI client (v1.x)
    try:
        logger.info("Attempting to connect using OpenAI v1.x client...")
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=10
        )
        
        logger.info(f"OpenAI v1 API response: {response.choices[0].message.content}")
        return True
    except Exception as e1:
        logger.error(f"Error with OpenAI v1 client: {str(e1)}")
        logger.error(traceback.format_exc())
        
        # Try legacy OpenAI client (v0.x) as fallback
        try:
            logger.info("Attempting to connect using OpenAI v0.x client...")
            import openai as legacy_openai
            legacy_openai.api_key = api_key
            
            response = legacy_openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello!"}],
                max_tokens=10
            )
            
            logger.info(f"OpenAI v0 API response: {response.choices[0].message.content}")
            return True
        except Exception as e2:
            logger.error(f"Error with OpenAI v0 client: {str(e2)}")
            logger.error(traceback.format_exc())
            return False

def test_telegram_connection():
    """Test connection to Telegram Bot API"""
    logger.info("=== Testing Telegram Bot API Connection ===")
    
    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        logger.error("No Telegram bot token found")
        return False
    
    try:
        logger.info("Attempting to connect to Telegram Bot API...")
        from telegram import Bot
        from telegram.error import InvalidToken, Unauthorized
        
        # Create an instance of the Bot class
        bot = Bot(token=bot_token)
        
        # Get information about the bot
        bot_info = bot.get_me()
        logger.info(f"Successfully connected to Telegram as @{bot_info.username} (ID: {bot_info.id})")
        logger.info(f"Bot name: {bot_info.first_name}")
        
        # Test if bot can get updates
        logger.info("Testing if bot can get updates...")
        updates = bot.get_updates(limit=1, timeout=1)
        logger.info(f"Successfully retrieved updates from Telegram")
        
        return True
    except InvalidToken:
        logger.error(f"Invalid Telegram bot token: {bot_token}")
        return False
    except Unauthorized:
        logger.error("Unauthorized: The token is valid but was revoked or the bot was blocked")
        return False
    except Exception as e:
        logger.error(f"Error connecting to Telegram: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def check_network_connectivity():
    """Check network connectivity to required services"""
    logger.info("=== Checking Network Connectivity ===")
    
    endpoints = {
        "OpenAI API": "api.openai.com",
        "Telegram API": "api.telegram.org"
    }
    
    all_connected = True
    
    for service, endpoint in endpoints.items():
        try:
            # Try to ping the endpoint
            logger.info(f"Testing connection to {service} ({endpoint})...")
            
            if sys.platform.startswith("win"):
                # For Windows
                response = subprocess.run(
                    ["ping", "-n", "1", endpoint], 
                    capture_output=True, 
                    text=True
                )
            else:
                # For Unix/Linux/Mac
                response = subprocess.run(
                    ["ping", "-c", "1", endpoint], 
                    capture_output=True, 
                    text=True
                )
            
            if response.returncode == 0:
                logger.info(f"✓ Successfully connected to {service}")
            else:
                logger.warning(f"✗ Could not connect to {service}")
                logger.debug(response.stdout)
                all_connected = False
        except Exception as e:
            logger.error(f"Error testing connection to {service}: {str(e)}")
            all_connected = False
    
    return all_connected

def run_full_diagnostics():
    """Run all diagnostic tests"""
    logger.info("Starting comprehensive diagnostics...")
    
    results = {
        "python_environment": check_python_environment(),
        "dependencies": check_dependencies(),
        "env_variables": check_env_variables(),
        "network_connectivity": check_network_connectivity(),
        "openai_connection": test_openai_connection(),
        "telegram_connection": test_telegram_connection()
    }
    
    logger.info("\n=== Diagnostic Results Summary ===")
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status} - {test}")
    
    if all(results.values()):
        logger.info("\n✅ ALL TESTS PASSED! Your environment should be ready to run the bot.")
        return True
    else:
        logger.error("\n❌ SOME TESTS FAILED. See details above for troubleshooting.")
        return False

if __name__ == "__main__":
    print("\n🔍 Running Advanced Diagnostics...\n")
    success = run_full_diagnostics()
    print("\nDiagnostics completed. Check the diagnostics.log file for detailed results.")
    sys.exit(0 if success else 1)
