#!/bin/bash

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BOLD}TripUAE Assistant Troubleshooter${NC}"
echo "==============================="

# Check if we're in the right directory
if [ ! -f "telegram_bot.py" ]; then
    echo -e "${RED}Error: Cannot find telegram_bot.py in the current directory${NC}"
    echo "Please run this script from the project directory"
    exit 1
fi

# Check environment file
echo -e "\n${BOLD}1. Checking environment variables...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Creating a template .env file..."
    cat > .env << EOL
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
EOL
    echo -e "${YELLOW}Created .env template. Please edit it with your API keys.${NC}"
else
    echo -e "${GREEN}Found .env file${NC}"
    
    # Check for API keys
    if grep -q "OPENAI_API_KEY=" .env && ! grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env; then
        echo -e "${GREEN}OpenAI API key found in .env${NC}"
    else
        echo -e "${RED}OpenAI API key missing or not set in .env${NC}"
    fi
    
    if grep -q "TELEGRAM_BOT_TOKEN=" .env && ! grep -q "TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here" .env; then
        echo -e "${GREEN}Telegram Bot token found in .env${NC}"
    else
        echo -e "${RED}Telegram Bot token missing or not set in .env${NC}"
    fi
fi

# Check dependencies
echo -e "\n${BOLD}2. Checking Python dependencies...${NC}"
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

echo "Installing/updating required packages..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Error installing dependencies. Please check the errors above.${NC}"
else
    echo -e "${GREEN}Dependencies installed successfully${NC}"
fi

# Check OpenAI API health
echo -e "\n${BOLD}3. Testing OpenAI API connection...${NC}"
python check_api_health.py
if [ $? -ne 0 ]; then
    echo -e "${RED}OpenAI API check failed. Please fix the issues before continuing.${NC}"
    echo -e "You may need to update your API key or check your account status."
    exit 1
else
    echo -e "${GREEN}OpenAI API connection verified${NC}"
fi

# Stop any running bot instances
echo -e "\n${BOLD}4. Managing bot processes...${NC}"
BOT_PIDS=$(ps aux | grep "[p]ython.*telegram_bot.py" | awk '{print $2}')

if [ -z "$BOT_PIDS" ]; then
    echo "No running bot instances found."
else
    echo -e "${YELLOW}Found running bot instances. Stopping them...${NC}"
    for PID in $BOT_PIDS; do
        echo "Stopping process $PID..."
        kill -TERM $PID
    done
    
    # Wait for processes to stop
    sleep 2
    
    # Check if any processes are still running
    REMAINING_PIDS=$(ps aux | grep "[p]ython.*telegram_bot.py" | awk '{print $2}')
    if [ ! -z "$REMAINING_PIDS" ]; then
        echo -e "${YELLOW}Forcing termination of remaining processes...${NC}"
        for PID in $REMAINING_PIDS; do
            echo "Force stopping process $PID..."
            kill -9 $PID
        done
    fi
    
    echo -e "${GREEN}All bot processes stopped${NC}"
fi

# Clear any Python bytecode files
echo -e "\n${BOLD}5. Cleaning cached Python files...${NC}"
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
echo -e "${GREEN}Python cache files cleaned${NC}"

# Start the bot
echo -e "\n${BOLD}6. Starting the bot...${NC}"
echo "Starting in background mode with logging to bot_log.txt"
nohup python telegram_bot.py > bot_log.txt 2>&1 &
NEW_PID=$!
echo -e "${GREEN}Bot started with PID ${NEW_PID}${NC}"
echo "Logs are being written to bot_log.txt"

echo -e "\n${BOLD}7. Monitoring for startup issues...${NC}"
sleep 3
if ps -p $NEW_PID > /dev/null; then
    echo -e "${GREEN}Bot is still running after startup${NC}"
    echo -e "Initial log output:"
    tail -n 10 bot_log.txt
else
    echo -e "${RED}Bot failed to start and exited immediately${NC}"
    echo -e "Check the log file for errors:"
    cat bot_log.txt
    exit 1
fi

echo -e "\n${GREEN}${BOLD}Bot troubleshooting and restart completed!${NC}"
echo "To check logs in real-time, use: tail -f bot_log.txt"
echo "To stop the bot, use: kill $NEW_PID"
