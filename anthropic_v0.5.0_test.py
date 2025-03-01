import os
import sys
from dotenv import load_dotenv
import anthropic

def test_anthropic_v0_5_0():
    """
    Test script specifically for Anthropic SDK version 0.5.0
    """
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)
    
    print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")
    print("Using Anthropic SDK v0.5.0")
    
    try:
        # Create client using the correct method for v0.5.0
        client = anthropic.Client(api_key=api_key)
        print("\n✅ Client initialization successful")
        
        # API call using v0.5.0 format
        print("\nTrying to create a completion with claude-v1...")
        try:
            response = client.completion(
                prompt=f"{anthropic.HUMAN_PROMPT} Say hello! {anthropic.AI_PROMPT}",
                model="claude-v1",
                max_tokens_to_sample=100,
                stop_sequences=[anthropic.HUMAN_PROMPT]
            )
            print("\n✅ API call successful!")
            print(f"Response: {response['completion']}")
            update_claude_engine("claude-v1")
            return
        except Exception as e:
            print(f"\n❌ claude-v1 failed: {e}")
        
        # Try alternative models
        for model in ["claude-v1.3", "claude-v1.3-100k", "claude-instant-v1", "claude-instant-v1.1"]:
            print(f"\nTrying with model {model}...")
            try:
                response = client.completion(
                    prompt=f"{anthropic.HUMAN_PROMPT} Say hello! {anthropic.AI_PROMPT}",
                    model=model,
                    max_tokens_to_sample=100,
                    stop_sequences=[anthropic.HUMAN_PROMPT]
                )
                print(f"\n✅ Success with model {model}!")
                print(f"Response: {response['completion']}")
                update_claude_engine(model)
                return
            except Exception as e:
                print(f"❌ {model} failed: {e}")
    
    except Exception as e:
        print(f"\n❌ Client initialization failed: {e}")
        print("Check if your API key is valid.")

def update_claude_engine(working_model):
    """Update claude_engine.py with the working model name"""
    print(f"\nUpdating claude_engine.py to use model: {working_model}")
    
    try:
        with open("claude_engine.py", "r") as file:
            content = file.read()
        
        # Replace the model name with the working one
        updated_content = content.replace('model="claude-2"', f'model="{working_model}"')
        
        with open("claude_engine.py", "w") as file:
            file.write(updated_content)
        
        print("✅ claude_engine.py updated successfully!")
        print(f"The assistant will now use the {working_model} model.")
    
    except Exception as e:
        print(f"❌ Error updating claude_engine.py: {e}")
        print(f"Please manually update the model name in claude_engine.py to: {working_model}")

if __name__ == "__main__":
    test_anthropic_v0_5_0()
