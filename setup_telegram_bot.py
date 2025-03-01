import sys
import subprocess
import os

def setup_telegram_bot():
    """
    Set up the requirements for the Telegram bot.
    """
    print("===== Setting up Telegram Bot Requirements =====")
    
    # Step 1: Install python-telegram-bot with the correct version (v13.7)
    print("\nStep 1: Installing python-telegram-bot version 13.7...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "python-telegram-bot==13.7"],
            check=True
        )
        print("✅ Successfully installed python-telegram-bot")
    except Exception as e:
        print(f"❌ Error installing python-telegram-bot: {e}")
        return False
    
    # Step 2: Check for Telegram Bot Token
    print("\nStep 2: Checking for Telegram Bot Token...")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        print(f"✅ Found TELEGRAM_BOT_TOKEN in environment variables: {token[:5]}...{token[-5:]}")
    else:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        print("\nPlease set your Telegram Bot Token with:")
        print("export TELEGRAM_BOT_TOKEN=your_token_here")
        
        # Ask if user wants to set it now
        user_input = input("\nDo you want to enter your Telegram Bot Token now? (y/n): ")
        if user_input.lower() == 'y':
            token = input("Enter your Telegram Bot Token: ")
            os.environ["TELEGRAM_BOT_TOKEN"] = token
            print(f"✅ Set TELEGRAM_BOT_TOKEN: {token[:5]}...{token[-5:]}")
            print("Note: This will only last for the current terminal session.")
            print("To make it permanent, add it to your .env file or shell profile.")
    
    # Step 3: Check for Anthropic API Key
    print("\nStep 3: Checking for Anthropic API Key...")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print(f"✅ Found ANTHROPIC_API_KEY in environment variables: {api_key[:5]}...{api_key[-5:]}")
    else:
        print("❌ ANTHROPIC_API_KEY not found in environment variables")
        print("Please make sure your Anthropic API key is set.")
    
    # Step 4: Final instructions
    print("\n===== Setup Complete! =====")
    print("\nYou can now run the Telegram bot with:")
    print("python telegram_bot_claude_direct.py")
    
    return True

if __name__ == "__main__":
    setup_telegram_bot()
