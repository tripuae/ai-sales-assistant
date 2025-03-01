import os
import requests
from dotenv import load_dotenv
import time

def debug_telegram_bot():
    """Debug Telegram bot connection and permissions"""
    print("===== Debugging Telegram Bot =====")
    
    # Load environment variables
    load_dotenv()
    
    # Get token
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        return
        
    print(f"✓ Found token: {token[:5]}...{token[-5:]}")
    
    # Test 1: Check if the bot token is valid
    print("\nTest 1: Checking bot token validity...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get("ok"):
                bot_data = bot_info.get("result", {})
                print(f"✓ Bot token is valid")
                print(f"   Bot name: {bot_data.get('first_name')}")
                print(f"   Username: @{bot_data.get('username')}")
            else:
                print(f"❌ Bot token returned an error: {bot_info}")
        else:
            print(f"❌ Error checking bot token: HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Test 2: Check webhook settings
    print("\nTest 2: Checking webhook settings...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
        if response.status_code == 200:
            webhook_info = response.json()
            if webhook_info.get("ok"):
                webhook_data = webhook_info.get("result", {})
                webhook_url = webhook_data.get("url", "")
                if webhook_url:
                    print(f"❌ Bot has a webhook set to: {webhook_url}")
                    print("   This will prevent polling methods from working.")
                    print("   Would you like to remove the webhook? (y/n)")
                    if input("> ").lower() == "y":
                        delete_response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
                        if delete_response.status_code == 200 and delete_response.json().get("ok"):
                            print("✓ Webhook deleted successfully")
                        else:
                            print(f"❌ Failed to delete webhook: {delete_response.text}")
                else:
                    print("✓ No webhook is set (good for polling)")
        else:
            print(f"❌ Error checking webhook: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Test 3: Test sending a message
    print("\nTest 3: Sending a test message...")
    print("Please enter your Telegram user ID or chat ID:")
    chat_id = input("> ")
    if chat_id:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "👋 This is a test message from the TripUAE debugging script."
                }
            )
            if response.status_code == 200 and response.json().get("ok"):
                print("✓ Test message sent successfully!")
            else:
                print(f"❌ Failed to send test message: {response.text}")
        except Exception as e:
            print(f"❌ Connection error: {e}")
    else:
        print("Skipping test message (no chat ID provided)")
    
    # Test 4: Check for updates
    print("\nTest 4: Checking for recent updates...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
        if response.status_code == 200:
            updates = response.json()
            if updates.get("ok"):
                update_data = updates.get("result", [])
                if update_data:
                    print(f"✓ Found {len(update_data)} recent updates")
                    latest = update_data[-1]
                    update_id = latest.get("update_id")
                    message = latest.get("message", {})
                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    user = message.get("from", {})
                    user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                    text = message.get("text", "")
                    print(f"   Latest update ID: {update_id}")
                    print(f"   From: {user_name} (ID: {user.get('id')})")
                    print(f"   Chat ID: {chat_id}")
                    print(f"   Message: {text}")
                else:
                    print("❌ No recent updates found")
                    print("   Your bot might not be receiving messages or hasn't received any yet")
            else:
                print(f"❌ Error checking updates: {updates}")
        else:
            print(f"❌ Error checking updates: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Provide next steps
    print("\n===== Next Steps =====")
    print("1. Make sure your bot is running in the terminal using:")
    print("   python direct_telegram_claude.py")
    print("2. Try sending a message to the bot again")
    print("3. If still not working, try using the simpler implementation:")
    print("   python minimal_telegram_bot.py")
    print("\nRemember: The terminal running the bot must remain open for the bot to function.")

if __name__ == "__main__":
    debug_telegram_bot()
