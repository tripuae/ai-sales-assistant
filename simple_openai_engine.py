import os
import logging
import time
import json
import sys
import traceback
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("openai_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import openai with try/except to handle different versions
try:
    import openai
    
    # Check if we're using v1.0+ of the OpenAI package
    if hasattr(openai, "__version__") and openai.__version__.startswith(("1.", "2.")):
        # OpenAI v1.0+ style imports
        logger.info(f"Using OpenAI v{openai.__version__} with new API style")
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Define common exceptions for retry logic
        class RateLimitError(Exception): pass
        class APITimeoutError(Exception): pass
        class APIConnectionError(Exception): pass
        
    else:
        # OpenAI v0.x style imports (legacy)
        logger.info(f"Using OpenAI v{getattr(openai, '__version__', 'unknown')} with legacy API style")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        client = openai
        
        # Use legacy exceptions
        RateLimitError = openai.error.RateLimitError
        APITimeoutError = openai.error.Timeout
        APIConnectionError = openai.error.APIConnectionError
        
except ImportError as e:
    logger.error(f"Failed to import openai: {e}")
    logger.error("Make sure it's installed with: pip install openai")
    sys.exit(1)

class ConversationContext:
    """Class to store conversation history for a user."""
    def __init__(self):
        self.messages = [
            {"role": "system", "content": (
                "You are TripUAE Assistant, a helpful guide for tourists visiting UAE. "
                "You provide information about tours and activities in Dubai and the UAE. "
                "Always be friendly, concise, and helpful. If you don't have specific information, "
                "say so politely and offer to help with other questions about UAE tourism."
            )}
        ]
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages in the conversation."""
        return self.messages

class OpenAIAssistant:
    """Class to interact with OpenAI's API."""
    
    def __init__(self, price_database: Optional[Any] = None):
        """Initialize the assistant with optional price database."""
        self.price_database = price_database
        self.model = "gpt-3.5-turbo"  # Default model
        
        # Test connection on init
        logger.debug("Testing OpenAI connection on initialization...")
        test_result = self.test_connection()
        if not test_result:
            logger.warning("Initial OpenAI connection test failed. Will retry on actual requests.")
    
    def test_connection(self) -> bool:
        """Test the connection to OpenAI API."""
        try:
            logger.debug("Sending test request to OpenAI")
            if hasattr(openai, "__version__") and openai.__version__.startswith(("1.", "2.")):
                # v1.x API style
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
            else:
                # v0.x API style (legacy)
                response = client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
            logger.debug("OpenAI test request successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI test request failed: {str(e)}")
            return False

    def generate_response(self, context: ConversationContext, user_message: str) -> str:
        """Generate a response based on the user's message and conversation context."""
        # Add the user's message to the context
        context.add_message("user", user_message)
        
        # Implement our own retry logic
        max_retries = 5
        base_delay = 1  # starting delay in seconds
        
        for attempt in range(max_retries):
            try:
                # Call the OpenAI API with version-appropriate method
                if hasattr(openai, "__version__") and openai.__version__.startswith(("1.", "2.")):
                    # v1.x API style
                    response = client.chat.completions.create(
                        model=self.model,
                        messages=context.get_messages(),
                        max_tokens=500,
                        temperature=0.7,
                    )
                    assistant_message = response.choices[0].message.content
                else:
                    # v0.x API style (legacy)
                    response = client.ChatCompletion.create(
                        model=self.model,
                        messages=context.get_messages(),
                        max_tokens=500,
                        temperature=0.7,
                    )
                    assistant_message = response["choices"][0]["message"]["content"]
                
                # Add the assistant's response to the context
                context.add_message("assistant", assistant_message)
                return assistant_message
                
            except Exception as e:
                delay = base_delay * (2 ** attempt)  # exponential backoff
                logger.error(f"Error on attempt {attempt+1}/{max_retries}: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Check if we should retry based on error type
                if "rate limit" in str(e).lower() or "timeout" in str(e).lower() or "connection" in str(e).lower():
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error("Max retries exceeded.")
                        raise Exception("Failed to generate response after multiple retries") from e
                else:
                    # For other errors, don't retry
                    raise e

    def set_model(self, model_name: str) -> None:
        """Change the OpenAI model being used."""
        self.model = model_name

def test_openai() -> bool:
    """Test connection to OpenAI API with proper error handling."""
    try:
        logger.debug("Testing OpenAI API connection")
        if hasattr(openai, "__version__") and openai.__version__.startswith(("1.", "2.")):
            # v1.x API style
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello!"}],
                max_tokens=5
            )
        else:
            # v0.x API style (legacy)
            response = client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello!"}],
                max_tokens=5
            )
        logger.info("OpenAI API connection successful")
        return True
        
    except Exception as e:
        logger.error(f"OpenAI API test failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Test the OpenAI connection when run directly
    success = test_openai()
    print(f"OpenAI API test {'succeeded' if success else 'failed'}")