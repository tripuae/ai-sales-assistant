#!/bin/bash

echo "Installing required packages..."
pip install -r requirements.txt

echo "Creating .env file template if it doesn't exist..."
if [ ! -f .env ]; then
    cat > .env << EOL
# Your OpenAI API key
OPENAI_API_KEY=your_api_key_here

# Your Telegram bot token from BotFather
TELEGRAM_BOT_TOKEN=your_telegram_token_here
EOL
    echo ".env file created. Please edit it to add your API keys."
    echo "Then run this script again to start the bot."
    exit 0
fi

echo "Running the bot..."
python telegram_bot.py
