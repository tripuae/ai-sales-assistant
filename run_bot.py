import logging
import sys
import subprocess
import time

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_diagnostics():
    """Run diagnostic tests first"""
    logger.info("Running diagnostics before starting the bot...")
    try:
        result = subprocess.run(
            [sys.executable, "advanced_diagnostics.py"],
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        logger.error("Diagnostics failed! Check the issues before running the bot.")
        return False

def run_bot():
    """Run the Telegram bot with auto-restart on failure"""
    if not run_diagnostics():
        logger.error("Not starting bot due to failed diagnostics.")
        return False
        
    max_restarts = 5
    restart_count = 0
    restart_delay = 5  # seconds
    
    while restart_count < max_restarts:
        try:
            logger.info(f"Starting bot (attempt {restart_count + 1}/{max_restarts})...")
            
            # Run the bot
            process = subprocess.Popen(
                [sys.executable, "telegram_bot.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for the process to complete and get output
            stdout, stderr = process.communicate()
            
            # Log output
            if stdout:
                logger.info(f"Bot output: {stdout}")
            if stderr:
                logger.error(f"Bot error: {stderr}")
                
            # Check return code
            if process.returncode == 0:
                logger.info("Bot exited normally.")
                break
            else:
                logger.error(f"Bot exited with error code {process.returncode}")
                restart_count += 1
                logger.info(f"Restarting bot in {restart_delay} seconds...")
                time.sleep(restart_delay)
                restart_delay *= 2  # Increase delay for next restart
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            restart_count += 1
            logger.info(f"Restarting bot in {restart_delay} seconds...")
            time.sleep(restart_delay)
            restart_delay *= 2
    
    if restart_count >= max_restarts:
        logger.error(f"Bot failed to run after {max_restarts} attempts.")
        return False
    
    return True

if __name__ == "__main__":
    success = run_bot()
    sys.exit(0 if success else 1)
