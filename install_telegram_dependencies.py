import subprocess
import sys
import os

def install_dependencies():
    """
    Install the required dependencies for the Telegram bot.
    """
    print("===== Installing Telegram Bot Dependencies =====")
    
    # Install python-telegram-bot
    print("Installing python-telegram-bot version 13.7...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "python-telegram-bot==13.7"],
            check=True
        )
        print("✅ Successfully installed python-telegram-bot")
    except Exception as e:
        print(f"❌ Error installing python-telegram-bot: {e}")
        return False
    
    print("\n===== Installation Complete =====")
    print("Now you can run the Telegram bot with:")
    print("python telegram_bot_claude_direct.py")
    
    return True

if __name__ == "__main__":
    install_dependencies()
