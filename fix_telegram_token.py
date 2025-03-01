import os
import re
import requests
from dotenv import load_dotenv, set_key

def fix_telegram_token():
    """Fix Telegram bot token issues"""
    print("===== Telegram Bot Token Fixer =====")
    
    # Load environment variables
    load_dotenv()
    
    # Check current token
    current_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if current_token:
        print(f"Current token in environment: {current_token[:5]}...{current_token[-5:]}")
        
        # Check if token is properly formatted (NNNNNNNNNN:XXXX...)
        token_pattern = re.compile(r'^\d+:[\w-]+$')
        if not token_pattern.match(current_token):
            print("❌ Current token doesn't match expected format (numbers:letters)")
            print("It should look like: 1234567890:ABCDEFabcdef-...")
        
        # Test the current token
        print("\nTesting current token...")
        try:
            response = requests.get(f"https://api.telegram.org/bot{current_token}/getMe")
            if response.status_code == 200 and response.json().get("ok"):
                print("✅ Current token is valid!")
                bot_data = response.json().get("result", {})
                print(f"Bot name: {bot_data.get('first_name')}")
                print(f"Username: @{bot_data.get('username')}")
                return
            else:
                print(f"❌ Current token is invalid: {response.text}")
        except Exception as e:
            print(f"❌ Error testing token: {e}")
    else:
        print("No TELEGRAM_BOT_TOKEN found in environment variables.")
    
    # Get new token from user
    print("\nYou need to get a new Telegram bot token from @BotFather:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /start to BotFather")
    print("3. Send /newbot to create a new bot OR /mybots to see your existing bots")
    print("4. Follow the instructions to get your bot token")
    print("\nEnter your new Telegram bot token:")
    
    new_token = input("> ").strip()
    if not new_token:
        print("No token entered. Exiting.")
        return
    
    # Test the new token
    print("\nTesting new token...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{new_token}/getMe")
        if response.status_code == 200 and response.json().get("ok"):
            print("✅ New token is valid!")
            bot_data = response.json().get("result", {})
            print(f"Bot name: {bot_data.get('first_name')}")
            print(f"Username: @{bot_data.get('username')}")
            
            # Save the new token to .env file
            env_path = os.path.join(os.getcwd(), '.env')
            if os.path.exists(env_path):
                set_key(env_path, "TELEGRAM_BOT_TOKEN", new_token)
                print("✅ Token saved to .env file")
            else:
                with open(env_path, 'a') as f:
                    f.write(f"\nTELEGRAM_BOT_TOKEN={new_token}\n")
                print("✅ Token added to new .env file")
            
            # Also set it in the current environment
            os.environ["TELEGRAM_BOT_TOKEN"] = new_token
            
            print("\nYour Telegram bot token has been updated!")
            print("Now you can run the bot with: python direct_telegram_claude.py")
        else:
            print(f"❌ New token is invalid: {response.text}")
    except Exception as e:
        print(f"❌ Error testing token: {e}")

if __name__ == "__main__":
    fix_telegram_token()
