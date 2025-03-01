import os
import sys
from dotenv import load_dotenv
import anthropic
import pkg_resources

def simple_claude_test():
    """
    Simple test script to identify the API version and make a basic request.
    """
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)
    
    # Get anthropic package version
    anthropic_version = pkg_resources.get_distribution("anthropic").version
    print(f"Anthropic SDK version: {anthropic_version}")
    
    try:
        # Create client - works with any version
        client = anthropic.Anthropic(api_key=api_key)
        
        # Try listing models if available in this version
        try:
            models = client.models.list()
            print("\nAvailable models:")
            for model in models.data:
                print(f"- {model.id}")
            
            # Try with the first model from the list
            if models.data:
                default_model = models.data[0].id
                print(f"\nUsing model: {default_model}")
            else:
                default_model = "claude-2"  # Fallback
                print(f"\nNo models found, using default: {default_model}")
                
        except Exception as model_error:
            # If models.list() isn't available
            print(f"\nCouldn't list models: {model_error}")
            default_model = "claude-2"  # Try with this default
            print(f"Using default model: {default_model}")
        
        # Try a test message with the most common modern method
        print("\nTrying to send a message...")
        try:
            response = client.messages.create(
                model=default_model,
                max_tokens=100,
                system="You are a helpful assistant.",
                messages=[{"role": "user", "content": "Say hello and identify yourself."}]
            )
            print("\n✅ Success using client.messages.create()!")
            print(f"Response: {response.content[0].text}")
            
            print("\nUpdate claude_engine.py to use this method.")
            return "messages.create"
            
        except Exception as messages_error:
            print(f"\n❌ messages.create() failed: {messages_error}")
            
            # Try completion method for older versions
            print("\nTrying older completion method...")
            try:
                prompt = f"{anthropic.HUMAN_PROMPT} Say hello and identify yourself. {anthropic.AI_PROMPT}"
                response = client.completion(
                    prompt=prompt,
                    model=default_model,
                    max_tokens_to_sample=100,
                    stop_sequences=[anthropic.HUMAN_PROMPT]
                )
                print("\n✅ Success using client.completion()!")
                print(f"Response: {response['completion']}")
                
                print("\nUpdate claude_engine.py to use this method.")
                return "completion"
                
            except Exception as completion_error:
                print(f"\n❌ completion() failed: {completion_error}")
                
                # If none of the methods work, try the completions endpoint
                print("\nTrying completions endpoint...")
                try:
                    response = client.completions.create(
                        model=default_model,
                        prompt=f"{anthropic.HUMAN_PROMPT} Say hello and identify yourself. {anthropic.AI_PROMPT}",
                        max_tokens_to_sample=100,
                        stop_sequences=[anthropic.HUMAN_PROMPT]
                    )
                    print("\n✅ Success using client.completions.create()!")
                    print(f"Response: {response.completion}")
                    
                    print("\nUpdate claude_engine.py to use this method.")
                    return "completions.create"
                    
                except Exception as completions_error:
                    print(f"\n❌ completions.create() failed: {completions_error}")
    
    except Exception as e:
        print(f"\n❌ Failed to initialize client: {e}")
    
    print("\nAll methods failed. Check Anthropic documentation for your SDK version.")
    return None

if __name__ == "__main__":
    simple_claude_test()
