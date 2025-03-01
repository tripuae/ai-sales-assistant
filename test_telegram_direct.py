
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/test_telegram_direct.py
import requests
import time

def test_bot():
    # Token is hardcoded for direct test
    token = "7520286452:AAHEjYROx3L8pdBduHF-0EqMz-VLRBlvcUc"
    
    print(f"Testing token: 75202...lvcUc")
    
    # Test connection
    response = requests.get(f"https://api.telegram.org/bot7520286452:AAHEjYROx3L8pdBduHF-0EqMz-VLRBlvcUc/getMe")
    if response.status_code == 200:
        bot_info = response.json()
        print(f"Connected to bot: {bot_info['result']['first_name']}")
    else:
        print(f"Connection failed: {response.text}")
        return
    
    # Start polling
    offset = 0
    print("Bot started! Press Ctrl+C to stop.")
    print("Open Telegram and send a message to your bot.")
    
    try:
        while True:
            updates_url = f"https://api.telegram.org/bot7520286452:AAHEjYROx3L8pdBduHF-0EqMz-VLRBlvcUc/getUpdates?offset={offset}&timeout=30"
            updates = requests.get(updates_url).json()
            
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        sender = update["message"]["from"]["first_name"]
                        
                        print(f"Message from {sender}: {text}")
                        
                        # Echo back
                        requests.post(
                            f"https://api.telegram.org/bot7520286452:AAHEjYROx3L8pdBduHF-0EqMz-VLRBlvcUc/sendMessage",
                            json={"chat_id": chat_id, "text": f"You said: {text}"}
                        )
            time.sleep(1)
    except KeyboardInterrupt:
        print("Bot stopped.")

if __name__ == "__main__":
    test_bot()
