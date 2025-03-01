import sys
import os
import subprocess

def test_imports():
    """Test if telegram packages can be imported correctly"""
    print("===== Testing Telegram Imports =====")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check installed packages
    print("\nChecking installed telegram packages:")
    # Use a different approach to check for installed telegram package
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "python-telegram-bot"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("Package python-telegram-bot is not installed.")
    except Exception as e:
        print(f"Error checking packages: {e}")
    
    # Try direct import
    print("\nTrying to import telegram module:")
    try:
        import telegram
        print(f"✅ Successfully imported telegram module, version: {telegram.__version__}")
        
        # Try importing specific classes
        try:
            from telegram import Update, Bot, ChatAction
            print("✅ Successfully imported telegram classes: Update, Bot, ChatAction")
        except ImportError as e:
            print(f"❌ Error importing telegram classes: {e}")
        
        # Try importing ext module
        try:
            from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
            print("✅ Successfully imported telegram.ext classes")
        except ImportError as e:
            print(f"❌ Error importing telegram.ext classes: {e}")
            
    except ImportError as e:
        print(f"❌ Error importing telegram module: {e}")
    
    # Try fixing with a reinstall
    if input("\nWould you like to try reinstalling python-telegram-bot? (y/n): ").lower() == 'y':
        print("\nUninstalling and reinstalling python-telegram-bot...")
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "python-telegram-bot"])
        subprocess.run([sys.executable, "-m", "pip", "install", "python-telegram-bot==13.7"])
        print("\nPlease run this test script again to see if the issue is resolved.")
    
    # Create simplified telegram bot
    print("\nCreating a simplified telegram bot script...")
    create_simplified_bot()
    
    print("\n===== Test Complete =====")

def create_simplified_bot():
    """Create a simplified version of the telegram bot"""
    code = """
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/simple_telegram_bot.py
import os
import logging
import sys
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import telegram modules directly
try:
    import telegram
    print(f"Successfully imported telegram module version {telegram.__version__}")

    from telegram import Update, Bot
    print("Successfully imported telegram.Update and telegram.Bot")

    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
    print("Successfully imported telegram.ext modules")
except ImportError as e:
    print(f"Error importing telegram: {e}")
    print("Try installing python-telegram-bot==13.7")
    sys.exit(1)

def start(update, context):
    update.message.reply_text("Hello! I am a simple test bot.")

def echo(update, context):
    update.message.reply_text(f"You said: {update.message.text}")

def main():
    # Load environment variables
    load_dotenv()
    
    # Get token
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        sys.exit(1)
    
    print(f"Using token: {token[:5]}...{token[-5:]}")
        
    # Create updater and dispatcher
    try:
        updater = Updater(token=token)
        dispatcher = updater.dispatcher
        
        # Register handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
        
        # Start the bot
        print("Starting bot...")
        updater.start_polling()
        print("Bot is running! Press Ctrl+C to stop.")
        updater.idle()
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()
"""
    
    with open("/Users/tripuae/Desktop/TripUAE-Assistant/simple_telegram_bot.py", "w") as f:
        f.write(code)
    
    print("Created simple_telegram_bot.py - you can run it with:")
    print("python simple_telegram_bot.py")

if __name__ == "__main__":
    test_imports()
