# TripUAE Assistant Telegram Bot

A Telegram bot that provides information about tours and activities in Dubai and UAE using OpenAI's API.

## Setup Instructions

### Prerequisites

- Python 3.7 or newer
- OpenAI API key
- Telegram Bot token (from BotFather)

### Installation

1. Clone this repository or download the files
2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project directory with the following content:

```
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

### Running the Bot

Run the bot with:

```bash
python telegram_bot.py
```

If you encounter any issues, run the diagnostic tool first:

```bash
python debug.py
```

## Troubleshooting

If you encounter errors, check the following:

1. Verify your API keys in the .env file
2. Make sure all dependencies are installed
3. Check the log files for errors (bot_debug.log and openai_debug.log)
4. Run the diagnostic tool: `python debug.py`

## Common Issues and Solutions

### OpenAI Connection Issues

- Check that your API key is correct
- Ensure you have sufficient credits in your OpenAI account
- Check if there are any outages with OpenAI's service

### Telegram Connection Issues

- Verify your bot token is correct
- Make sure your bot is properly set up through BotFather
- Check your internet connection

### Permission Issues

If you're on Linux or Mac, you might need to make the script executable:

```bash
chmod +x install_and_run.sh
```

## Bot Commands

The bot supports the following commands:

- `/start` - Start the conversation with the bot
- `/help` - Show help information
- `/reset` - Reset the conversation history
