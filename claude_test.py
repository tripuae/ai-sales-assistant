import os
from dotenv import load_dotenv
from anthropic import Anthropic, AuthenticationError, APIConnectionError

def test_claude_connection():
    """
    Test connection to Claude API using credentials from .env file
    """
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment variables
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not found. Make sure it's in your .env file.")
        
        # Initialize the Anthropic client
        client = Anthropic(api_key=api_key)
        
        # Send a test message using claude-3-opus-20240229 model
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=300,
            messages=[
                {"role": "user", "content": "Hello Claude! This is a test message from TripUAE Assistant. Please respond with a brief greeting."}
            ]
        )
        
        # Print the response
        print("✅ Connection to Claude API successful!")
        print(f"Response: {message.content[0].text}")
        return True
        
    except AuthenticationError:
        print("❌ Authentication Error: The API key provided is invalid or expired.")
        return False
    except APIConnectionError:
        print("❌ Connection Error: Could not connect to Claude API. Please check your internet connection.")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Claude API: {e}")
        return False

if __name__ == "__main__":
    test_claude_connection()
