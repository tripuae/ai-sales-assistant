
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/test_claude_setup.py
import os
import anthropic
from dotenv import load_dotenv

def test_claude_api():
    # Load .env file if it exists
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        return False
        
    print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")
    
    try:
        # Create client
        client = anthropic.Client(api_key=api_key)
        print("✅ Client created successfully")
        
        # Try a simple completion
        print("Sending test request to Claude API...")
        prompt = f"{anthropic.HUMAN_PROMPT} Tell me a short fact about Dubai. {anthropic.AI_PROMPT}"
        
        response = client.completion(
            prompt=prompt,
            model="claude-2",  # Try with claude-2 model
            max_tokens_to_sample=100,
            stop_sequences=[anthropic.HUMAN_PROMPT]
        )
        
        print("✅ API call successful!")
        print(f"\nResponse from Claude:\n")
        print(response["completion"].strip())
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
if __name__ == "__main__":
    test_claude_api()
