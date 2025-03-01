import os
import sys
from dotenv import load_dotenv
import anthropic

def check_claude_api_access():
    """
    Check if the provided Anthropic API key has access to Claude models.
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Please set it in your .env file or export it in your terminal.")
        sys.exit(1)
    
    print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")
    
    try:
        # Initialize the Anthropic client with older API version
        client = anthropic.Client(api_key=api_key)
        
        # Older API doesn't have models.list, so we'll hard-code known models
        print("\nUsing Anthropic API v0.5.0")
        print("Available models in Claude API v0.5.0:")
        print("- claude-2")
        print("- claude-instant-1")
        
        # Try a simple completion with Claude-2
        print("\nTesting API with a simple message to claude-2...")
        try:
            prompt = f"{anthropic.HUMAN_PROMPT} Say hello and identify yourself. {anthropic.AI_PROMPT}"
            response = client.completion(
                prompt=prompt,
                model="claude-2",
                max_tokens_to_sample=100,
                stop_sequences=[anthropic.HUMAN_PROMPT]
            )
            
            print("\n✅ API test successful! Response:")
            print(f"'{response['completion'].strip()}'")
            
            print("\nYour API key is working correctly with the Anthropic API v0.5.0.")
            print("You can now use claude_main.py and other scripts that use claude_engine.py.")
            
        except Exception as e:
            print(f"\n❌ Claude-2 test failed with error: {str(e)}")
            print("\nThis might be due to:")
            print("1. Your API key doesn't have access to the claude-2 model")
            print("2. The model name might be different for your account")
            
    except Exception as e:
        print(f"\n❌ API connection failed: {str(e)}")
        print("\nPossible issues:")
        print("1. The API key may be invalid")
        print("2. Your account may not have access to Claude models")
        print("3. There might be network connectivity issues")
        print("4. The Anthropic API might be experiencing downtime")

if __name__ == "__main__":
    check_claude_api_access()
