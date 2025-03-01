#!/bin/bash

echo "Restarting TripUAE Assistant bot..."

# Find all Python processes running telegram_bot.py
PIDS=$(ps aux | grep "[p]ython.*telegram_bot.py" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No running bot instances found."
else
    echo "Found bot instances with PIDs: $PIDS"
    echo "Sending graceful termination signal..."
    
    for PID in $PIDS; do
        kill -TERM $PID
    done
    
    # Wait up to 5 seconds for graceful shutdown
    COUNTER=0
    while [ $COUNTER -lt 5 ]; do
        if ! ps -p $PIDS > /dev/null 2>&1; then
            echo "Bot shutdown successfully."
            break
        fi
        echo "Waiting for bot to shutdown..."
        sleep 1
        COUNTER=$((COUNTER+1))
    done
    
    # Force kill if still running
    if ps -p $PIDS > /dev/null 2>&1; then
        echo "Forcing shutdown..."
        for PID in $PIDS; do
            kill -9 $PID
        done
    fi
fi

echo "Starting new bot instance..."
cd "$(dirname "$0")"
nohup python telegram_bot.py > bot_log.txt 2>&1 &
echo "Bot started with PID $!"
echo "Logs are being written to bot_log.txt"
