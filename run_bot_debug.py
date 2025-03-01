import logging
import os
import sys
from dotenv import load_dotenv

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Make sure environment is loaded
load_dotenv()

# Check critical environment variables
for var in ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN"]:
    if not os.getenv(var):
        print(f"Error: {var} not found in environment variables.")
        print("Make sure you have a .env file with all required API keys.")
        sys.exit(1)

print("Starting bot in debug mode...")

# Import and run the bot (will use the DEBUG logging level)
try:
    # This will run the main function from telegram_bot.py
    from telegram_bot import main
    main()
except Exception as e:
    print(f"Error running bot: {e}")
    import traceback
    traceback.print_exc()
