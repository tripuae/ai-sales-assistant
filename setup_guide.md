# TripUAE Assistant Setup Guide

This guide will help you set up the TripUAE Assistant on your local machine.

## Prerequisites

- Python 3.8 or higher
- Git
- A Telegram Bot token (from BotFather)
- An Anthropic API key for Claude

## Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/tripuae/ai-sales-assistant.git
   cd ai-sales-assistant
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   ```bash
   cp .env.example .env
   ```
   
5. Edit the `.env` file with your actual API keys:
   ```
   OPENAI_API_KEY=your_actual_openai_api_key
   TELEGRAM_BOT_TOKEN=your_actual_telegram_bot_token
   ANTHROPIC_API_KEY=your_actual_anthropic_api_key
   ```

6. Run the bot:
   ```bash
   python direct_telegram_token_bot.py
   ```

## Usage

The bot can be controlled with the following commands:
- `/start` - Start a new conversation
- `/help` - Show help message
- `/reset` - Reset conversation history

## Troubleshooting

If you encounter any issues:

1. Verify your API keys are correct
2. Make sure your Telegram bot is active
3. Run the debug script: `python debug_telegram_bot.py`

## Security Note

Never commit your `.env` file with actual API keys to the repository!
