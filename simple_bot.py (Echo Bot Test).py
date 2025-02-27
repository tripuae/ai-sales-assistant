import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Setup
load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Start command received")
    await update.message.reply_text("Hello! I'm a test echo bot.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    logger.debug(f"Message received: {message}")
    await update.message.reply_text(f"You said: {message}")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No Telegram bot token found in .env file!")
        return
        
    logger.debug(f"Using token: {token[:5]}...")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.debug("Starting echo bot...")
    application.run_polling()
    logger.info("Echo bot started")

if __name__ == "__main__":
    main()