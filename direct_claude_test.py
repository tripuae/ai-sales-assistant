import os
import json
import requests
import sys
from dotenv import load_dotenv

def test_direct_api():
    """
    Test Claude API using direct HTTP requests without the SDK
    """
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)
    
    print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")
    print("\nAttempting to connect directly to Claude API...")
    
    # First, try to list available models
    print("\nStep 1: Checking available models")
    try:
        models_response = requests.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
        )
        
        if models_response.status_code == 200:
            models_data = models_response.json()
            print("✅ Successfully retrieved models!")
            print("\nAvailable models:")
            for model in models_data.get('data', []):
                print(f"- {model.get('id')}")
            
            # Use the first available model for testing
            if models_data.get('data'):
                test_model = models_data['data'][0]['id']
                print(f"\nUsing model {test_model} for testing")
            else:
                test_model = "claude-2" # Fallback
                print(f"\nNo models found, using fallback model {test_model}")
        else:
            print(f"❌ Failed to get models: {models_response.status_code}")
            print(models_response.text)
            test_model = "claude-instant-1" # Fallback
            print(f"Using fallback model {test_model}")
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        test_model = "claude-instant-1" # Fallback
        print(f"Using fallback model {test_model}")
    
    # Step 2: Try the Messages API
    print("\nStep 2: Testing Messages API")
    try:
        messages_response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": test_model,
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": "Hello, who are you?"}
                ]
            }
        )
        
        if messages_response.status_code == 200:
            data = messages_response.json()
            print("✅ Messages API successful!")
            print(f"Response: {data.get('content', [{'text': 'No content'}])[0].get('text')[:100]}...")
            
            # Save working configuration
            save_config("messages", test_model)
            return
        else:
            print(f"❌ Messages API failed: {messages_response.status_code}")
            print(messages_response.text)
    except Exception as e:
        print(f"❌ Error testing Messages API: {e}")
    
    # Step 3: Try the Completions API
    print("\nStep 3: Testing Completions API")
    try:
        completions_response = requests.post(
            "https://api.anthropic.com/v1/completions",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": test_model,
                "prompt": "\n\nHuman: Hello, who are you?\n\nAssistant:",
                "max_tokens_to_sample": 100,
                "stop_sequences": ["\n\nHuman:"]
            }
        )
        
        if completions_response.status_code == 200:
            data = completions_response.json()
            print("✅ Completions API successful!")
            print(f"Response: {data.get('completion', 'No completion')[:100]}...")
            
            # Save working configuration
            save_config("completions", test_model)
            return
        else:
            print(f"❌ Completions API failed: {completions_response.status_code}")
            print(completions_response.text)
    except Exception as e:
        print(f"❌ Error testing Completions API: {e}")
    
    print("\n❌ All API tests failed. Next steps:")
    print("1. Verify your API key is correct and has the right permissions")
    print("2. Contact Anthropic support to check your account status")

def save_config(api_type, model):
    """Save working configuration to a file"""
    config = {
        "api_type": api_type,
        "model": model,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    
    with open("/Users/tripuae/Desktop/TripUAE-Assistant/working_claude_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Saved working configuration to working_claude_config.json")
    
    # Create a direct API implementation that doesn't rely on the SDK
    create_direct_implementation(api_type, model)

def create_direct_implementation(api_type, model):
    """Create a direct API implementation without using the SDK"""
    filepath = "/Users/tripuae/Desktop/TripUAE-Assistant/direct_claude_engine.py"
    
    if api_type == "messages":
        code = f'''
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/direct_claude_engine.py
import os
import json
import requests
from typing import List, Dict, Any

class ConversationContext:
    def __init__(self):
        """Initialize an empty conversation context with no messages."""
        self.messages = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation context."""
        self.messages.append({{"role": role, "content": content}})

class ClaudeAssistant:
    def __init__(self, price_db):
        """Initialize the Claude Assistant."""
        self.price_db = price_db
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        print("Using Claude Direct API with Messages endpoint")
        print("Model: {model}")
        
        # System message
        self.system_message = """
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        """
    
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Add user message to context
            context.add_message("user", user_message)
            
            # Format messages for API
            messages = [{{"role": msg["role"], "content": msg["content"]}} for msg in context.messages]
            
            # Call Claude API directly using requests
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={{
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }},
                json={{
                    "model": "{model}",
                    "system": self.system_message,
                    "messages": messages,
                    "max_tokens": 1000
                }}
            )
            
            if response.status_code != 200:
                error_msg = f"API error: {{response.status_code}} - {{response.text}}"
                print(error_msg)
                return f"Sorry, I encountered an error: {{error_msg}}"
                
            # Extract response text
            data = response.json()
            response_text = data.get('content', [{{'text': 'No response'}}])[0].get('text')
            
            # Add assistant response to context
            context.add_message("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_message = f"Error generating response: {{str(e)}}"
            print(error_message)
            return error_message
'''
    else:  # completions API
        code = f'''
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/direct_claude_engine.py
import os
import json
import requests
from typing import List, Dict, Any

class ConversationContext:
    def __init__(self):
        """Initialize an empty conversation context with no messages."""
        self.messages = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation context."""
        self.messages.append({{"role": role, "content": content}})

class ClaudeAssistant:
    def __init__(self, price_db):
        """Initialize the Claude Assistant."""
        self.price_db = price_db
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        print("Using Claude Direct API with Completions endpoint")
        print("Model: {model}")
        
        # System message (included in prompt for completions API)
        self.system_message = """
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        """
    
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Format conversation history into prompt
            prompt = "\\n\\nSystem: " + self.system_message + "\\n\\n"
            
            # Add previous messages to the prompt
            for msg in context.messages:
                if msg["role"] == "user":
                    prompt += f"Human: {{msg['content']}}\\n\\n"
                else:
                    prompt += f"Assistant: {{msg['content']}}\\n\\n"
            
            # Add current user message
            prompt += f"Human: {{user_message}}\\n\\nAssistant:"
            
            # Call Claude API directly using requests
            response = requests.post(
                "https://api.anthropic.com/v1/completions",
                headers={{
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }},
                json={{
                    "model": "{model}",
                    "prompt": prompt,
                    "max_tokens_to_sample": 1000,
                    "stop_sequences": ["\\n\\nHuman:"]
                }}
            )
            
            if response.status_code != 200:
                error_msg = f"API error: {{response.status_code}} - {{response.text}}"
                print(error_msg)
                return f"Sorry, I encountered an error: {{error_msg}}"
                
            # Extract response text
            data = response.json()
            response_text = data.get('completion', 'No response').strip()
            
            # Add messages to context
            context.add_message("user", user_message)
            context.add_message("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_message = f"Error generating response: {{str(e)}}"
            print(error_message)
            return error_message
'''
    
    # Write the file
    with open(filepath, 'w') as f:
        f.write(code)
    
    print(f"\n✅ Created direct Claude API implementation at: {filepath}")
    print("\nTo use this implementation:")
    print("1. Copy this file: cp direct_claude_engine.py claude_engine.py")
    print("2. Run your main script: python claude_main.py")

if __name__ == "__main__":
    test_direct_api()
