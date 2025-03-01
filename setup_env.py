import os
import sys

def setup_environment():
    """
    Set up the environment files and check configurations.
    """
    print("===== Setting up TripUAE Assistant Environment =====")
    
    # Check if .env file exists
    env_file = os.path.join(os.getcwd(), '.env')
    env_example_file = os.path.join(os.getcwd(), '.env.example')
    
    # Create .env.example if it doesn't exist
    if not os.path.exists(env_example_file):
        print("Creating .env.example file...")
        with open(env_example_file, 'w') as f:
            f.write("""# OpenAI API key - get from https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Telegram Bot Token - get from BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Anthropic API key for Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here
""")
        print("✅ Created .env.example file")
    
    # Create .env file if it doesn't exist
    if not os.path.exists(env_file):
        print("\nCreating .env file from .env.example...")
        with open(env_example_file, 'r') as example:
            with open(env_file, 'w') as env:
                env.write(example.read())
        print("✅ Created .env file")
        print("\nPlease edit the .env file to include your actual API keys.")
    else:
        print("\n✅ .env file already exists")
    
    # Check if we have actual API keys in the .env file
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    placeholders = [
        "your_openai_api_key_here", 
        "your_telegram_bot_token_here", 
        "your_anthropic_api_key_here"
    ]
    
    if any(placeholder in env_content for placeholder in placeholders):
        print("\n⚠️  Warning: Your .env file contains placeholder values.")
        print("Please edit the .env file to include your actual API keys.")
        
        # Ask if user wants to edit now
        response = input("\nWould you like to enter your API keys now? (y/n): ")
        if response.lower() == 'y':
            # Get API keys
            anthropic_key = input("Enter your Anthropic API key: ").strip()
            telegram_token = input("Enter your Telegram Bot token: ").strip()
            
            # Update .env file
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            with open(env_file, 'w') as f:
                for line in lines:
                    if "ANTHROPIC_API_KEY=" in line:
                        f.write(f"ANTHROPIC_API_KEY={anthropic_key}\n")
                    elif "TELEGRAM_BOT_TOKEN=" in line:
                        f.write(f"TELEGRAM_BOT_TOKEN={telegram_token}\n")
                    else:
                        f.write(line)
            
            print("\n✅ Updated .env file with API keys")
    else:
        print("\n✅ Your .env file appears to have actual API keys")
    
    print("\n===== Environment Setup Complete =====")
    print("\nNext steps:")
    print("1. Run the Telegram bot: python claude_telegram_bot.py")
    print("2. Or test Claude directly: python claude_main.py")

if __name__ == "__main__":
    setup_environment()
