import os
import requests

def fix_telegram_token():
    """Directly fix the Telegram token issue without using dotenv"""
    print("===== Direct Telegram Token Fix =====")
    
    # Path to .env file
    env_file = os.path.join(os.getcwd(), '.env')
    
    # Read token directly from file
    token = None
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('TELEGRAM_BOT_TOKEN'):
                        # Split by first equals sign
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            token = parts[1].strip()
                            # Remove any quotes
                            for quote in ["'", '"']:
                                if token.startswith(quote) and token.endswith(quote):
                                    token = token[1:-1]
                            break
        except Exception as e:
            print(f"Error reading .env file: {e}")
    
    if not token:
        print("Could not find TELEGRAM_BOT_TOKEN in .env file.")
        token = input("Please paste your Telegram bot token here: ").strip()
    
    print(f"\nToken found: {token}")
    
    # Verify format
    if not token or ':' not in token:
        print("❌ Token format appears invalid. It should contain a colon.")
        token = input("Please enter a valid token (format: 1234567890:ABCDEFGabcdef...): ")
    
    # Test the token
    print("\nTesting token with Telegram API...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code == 200:
            bot_data = response.json()
            if bot_data.get("ok"):
                print("✅ Token is valid!")
                bot_name = bot_data["result"]["first_name"]
                bot_username = bot_data["result"]["username"]
                print(f"Bot name: {bot_name}")
                print(f"Username: @{bot_username}")
            else:
                print(f"❌ Token returned error: {bot_data}")
        else:
            print(f"❌ Token is invalid. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False
    
    # Update .env file with clean token
    try:
        lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
        
        new_lines = []
        token_updated = False
        for line in lines:
            if line.strip().startswith('TELEGRAM_BOT_TOKEN'):
                new_lines.append(f"TELEGRAM_BOT_TOKEN={token}\n")
                token_updated = True
            else:
                new_lines.append(line)
        
        if not token_updated:
            new_lines.append(f"\nTELEGRAM_BOT_TOKEN={token}\n")
        
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        print("\n✅ Updated .env file with clean token")
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
    
    # Set environment variable directly
    os.environ["TELEGRAM_BOT_TOKEN"] = token
    print("✅ Set TELEGRAM_BOT_TOKEN environment variable")
    
    # Create a simple test script
    test_script = f'''
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/test_telegram_direct.py
import requests
import time

def test_bot():
    # Token is hardcoded for direct test
    token = "{token}"
    
    print(f"Testing token: {token[:5]}...{token[-5:]}")
    
    # Test connection
    response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
    if response.status_code == 200:
        bot_info = response.json()
        print(f"Connected to bot: {{bot_info['result']['first_name']}}")
    else:
        print(f"Connection failed: {{response.text}}")
        return
    
    # Start polling
    offset = 0
    print("Bot started! Press Ctrl+C to stop.")
    print("Open Telegram and send a message to your bot.")
    
    try:
        while True:
            updates_url = f"https://api.telegram.org/bot{token}/getUpdates?offset={{offset}}&timeout=30"
            updates = requests.get(updates_url).json()
            
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        sender = update["message"]["from"]["first_name"]
                        
                        print(f"Message from {{sender}}: {{text}}")
                        
                        # Echo back
                        requests.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={{"chat_id": chat_id, "text": f"You said: {{text}}"}}
                        )
            time.sleep(1)
    except KeyboardInterrupt:
        print("Bot stopped.")

if __name__ == "__main__":
    test_bot()
'''
    
    with open("test_telegram_direct.py", "w") as f:
        f.write(test_script)
    
    print("\n✅ Created direct test script: test_telegram_direct.py")
    print("\nTo test your bot, run:")
    print("python test_telegram_direct.py")
    
    return True

if __name__ == "__main__":
    fix_telegram_token()
