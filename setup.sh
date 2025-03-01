#!/bin/bash

echo "🚀 Setting up TripUAE Assistant environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Create and activate a virtual environment
echo "📦 Creating a virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Update pip
echo "🔄 Updating pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Run diagnostics
echo "🔍 Running diagnostics..."
python advanced_diagnostics.py

echo ""
echo "✅ Setup complete! If diagnostics passed, you can now run the bot with:"
echo "python telegram_bot.py"
echo ""
echo "If diagnostics failed, check the error messages and diagnostics.log file."
