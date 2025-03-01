import os
import sys
import inspect
from dotenv import load_dotenv
import anthropic

def test_minimal_anthropic():
    """
    Create a minimal test to determine the correct API usage for your Anthropic SDK version.
    """
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        return
    
    print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")
    
    # Create client - will work with any version
    client = None
    try:
        # Check if Client class exists (older SDK)
        if hasattr(anthropic, 'Client'):
            print("\nCreating client using anthropic.Client...")
            client = anthropic.Client(api_key=api_key)
            print("✅ Client created successfully using anthropic.Client")
        # Check if Anthropic class exists (newer SDK)
        elif hasattr(anthropic, 'Anthropic'):
            print("\nCreating client using anthropic.Anthropic...")
            client = anthropic.Anthropic(api_key=api_key)
            print("✅ Client created successfully using anthropic.Anthropic")
        else:
            print("❌ Could not find appropriate client class in anthropic module")
            return
    except Exception as e:
        print(f"❌ Error creating client: {e}")
        return
    
    # Inspect what methods and attributes are available
    print("\nAvailable client attributes and methods:")
    client_attrs = [attr for attr in dir(client) if not attr.startswith('_')]
    for attr in client_attrs:
        print(f"- {attr}")
    
    # Try to make a simple API call based on available methods
    success = False
    
    # Try completions.create method (newest API)
    if hasattr(client, 'completions') and hasattr(client.completions, 'create'):
        print("\nTrying client.completions.create()...")
        try:
            response = client.completions.create(
                prompt=f"Human: Say hello\n\nAssistant:",
                model="claude-instant-1",
                max_tokens_to_sample=100,
                stop_sequences=["Human:"]
            )
            print(f"✅ Success! Response: {response.completion}")
            
            # Update the engine file
            create_claude_engine_file("completions", response)
            success = True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Try messages.create method
    if not success and hasattr(client, 'messages') and hasattr(client.messages, 'create'):
        print("\nTrying client.messages.create()...")
        try:
            response = client.messages.create(
                model="claude-instant-1",
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=100
            )
            print(f"✅ Success! Response: {response.content[0].text}")
            
            # Update the engine file
            create_claude_engine_file("messages", response)
            success = True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Try direct completion method (old API)
    if not success and hasattr(client, 'completion'):
        print("\nTrying client.completion()...")
        try:
            response = client.completion(
                prompt="Human: Say hello\n\nAssistant:",
                model="claude-instant-1",
                max_tokens_to_sample=100,
                stop_sequences=["Human:"]
            )
            print(f"✅ Success! Response: {response['completion']}")
            
            # Update the engine file
            create_claude_engine_file("completion", response)
            success = True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    if not success:
        print("\n❌ All API call attempts failed.")
        print("Please check Anthropic documentation for your specific SDK version.")
        print("Your anthropic package may need to be updated or replaced.")
        print("\nConsider installing a specific version: pip install anthropic==0.3.0")
        
def create_claude_engine_file(method_type, sample_response):
    """Create a working claude_engine.py file based on what works"""
    filepath = "/Users/tripuae/Desktop/TripUAE-Assistant/claude_engine_working.py"
    
    if method_type == "completions":
        code = """
import os
import anthropic
from typing import List, Dict, Any

class ConversationContext:
    def __init__(self):
        """Initialize an empty conversation context with no messages."""
        self.messages = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation context."""
        self.messages.append({"role": role, "content": content})

class ClaudeAssistant:
    def __init__(self, price_db):
        """Initialize the Claude Assistant."""
        self.price_db = price_db
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.system_message = \"\"\"
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        \"\"\"
    
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Format the conversation history and user message into a prompt
            prompt = "\\n\\n".join([
                f"{'Human' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
                for msg in context.messages
            ])
            if prompt:
                prompt += "\\n\\n"
            prompt += f"Human: {user_message}\\n\\nAssistant:"
            
            # Make API call using completions.create
            response = self.client.completions.create(
                prompt=prompt,
                model="claude-instant-1",  # Use available model
                max_tokens_to_sample=1000,
                stop_sequences=["Human:"]
            )
            
            # Extract response text
            response_text = response.completion.strip()
            
            # Add messages to context
            context.add_message("user", user_message)
            context.add_message("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return error_message
        """
    
    elif method_type == "messages":
        code = """
import os
import anthropic
from typing import List, Dict, Any

class ConversationContext:
    def __init__(self):
        """Initialize an empty conversation context with no messages."""
        self.messages = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation context."""
        self.messages.append({"role": role, "content": content})

class ClaudeAssistant:
    def __init__(self, price_db):
        """Initialize the Claude Assistant."""
        self.price_db = price_db
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.system_message = \"\"\"
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        \"\"\"
    
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Add user message to context
            context.add_message("user", user_message)
            
            # Convert context messages to the format expected by the API
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in context.messages]
            
            # Make API call using messages.create
            response = self.client.messages.create(
                model="claude-instant-1",  # Use available model
                system=self.system_message,
                messages=messages,
                max_tokens=1000
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Add assistant response to context
            context.add_message("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return error_message
        """
    
    elif method_type == "completion":
        code = """
import os
import anthropic
from typing import List, Dict, Any

class ConversationContext:
    def __init__(self):
        """Initialize an empty conversation context with no messages."""
        self.messages = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation context."""
        self.messages.append({"role": role, "content": content})

class ClaudeAssistant:
    def __init__(self, price_db):
        """Initialize the Claude Assistant."""
        self.price_db = price_db
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Client(api_key=self.api_key)
        self.system_message = \"\"\"
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        \"\"\"
    
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Format the conversation history and user message into a prompt
            prompt = ""
            for msg in context.messages:
                if msg["role"] == "user":
                    prompt += f"{anthropic.HUMAN_PROMPT} {msg['content']} "
                else:
                    prompt += f"{anthropic.AI_PROMPT} {msg['content']} "
            
            prompt += f"{anthropic.HUMAN_PROMPT} {user_message} {anthropic.AI_PROMPT}"
            
            # Make API call using completion
            response = self.client.completion(
                prompt=prompt,
                model="claude-instant-1", # Use available model
                max_tokens_to_sample=1000,
                stop_sequences=[anthropic.HUMAN_PROMPT]
            )
            
            # Extract response text
            response_text = response["completion"].strip()
            
            # Add messages to context
            context.add_message("user", user_message)
            context.add_message("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return error_message
        """
    
    with open(filepath, 'w') as f:
        f.write(code)
    
    print(f"\n✅ Created working Claude engine file at: {filepath}")
    print("To use this file, run: cp claude_engine_working.py claude_engine.py")

if __name__ == "__main__":
    test_minimal_anthropic()
