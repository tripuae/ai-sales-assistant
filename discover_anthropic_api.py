import os
import sys
import inspect
import pkgutil
from dotenv import load_dotenv
import anthropic
import json

def discover_anthropic_api():
    """Discover the available API methods in the installed anthropic package"""
    print("===== Discovering Anthropic API =====")
    
    # Get version
    try:
        version = anthropic.__version__
        print(f"Installed Anthropic SDK version: {version}")
    except AttributeError:
        print("Couldn't determine Anthropic SDK version")
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        return
    
    print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")
    
    # Try to find the client class
    if hasattr(anthropic, 'Anthropic'):
        print("\nFound anthropic.Anthropic class")
        client_class = anthropic.Anthropic
    elif hasattr(anthropic, 'Client'):
        print("\nFound anthropic.Client class")
        client_class = anthropic.Client
    else:
        print("\n❌ Could not find appropriate client class in anthropic module")
        print_module_contents(anthropic)
        return
    
    # Create client
    try:
        print("\nCreating client...")
        if client_class.__name__ == 'Anthropic':
            client = client_class(api_key=api_key)
        else:
            # Try with default headers if it's the newer Client
            try:
                client = client_class(
                    api_key=api_key,
                    default_headers={"anthropic-version": "2023-06-01"}
                )
            except TypeError:
                # Fall back to simple initialization if default_headers isn't accepted
                client = client_class(api_key=api_key)
        
        print("✅ Client created successfully")
        
        # Explore client attributes and methods
        print("\nExploring client attributes and methods:")
        client_attrs = {attr: type(getattr(client, attr)).__name__ 
                       for attr in dir(client) 
                       if not attr.startswith('_')}
        
        for attr, attr_type in client_attrs.items():
            print(f"- {attr} ({attr_type})")
        
        # Look for completion methods
        completion_methods = []
        if hasattr(client, 'completion'):
            completion_methods.append('client.completion()')
        if hasattr(client, 'completions') and hasattr(client.completions, 'create'):
            completion_methods.append('client.completions.create()')
        if hasattr(client, 'complete'):
            completion_methods.append('client.complete()')
        if hasattr(client, 'messages') and hasattr(client.messages, 'create'):
            completion_methods.append('client.messages.create()')
        
        print(f"\nFound potential completion methods: {completion_methods}")
        
        # Generate appropriate claude_engine.py based on discovered API
        create_appropriate_claude_engine(client_class, completion_methods)
        
    except Exception as e:
        print(f"❌ Error during API discovery: {e}")

def print_module_contents(module):
    """Print the contents of a module to help with debugging"""
    print("\nModule contents:")
    for attr_name in dir(module):
        if not attr_name.startswith('_'):
            attr = getattr(module, attr_name)
            print(f"- {attr_name} ({type(attr).__name__})")

def create_appropriate_claude_engine(client_class, completion_methods):
    """Create an appropriate claude_engine.py based on discovered API"""
    filepath = "/Users/tripuae/Desktop/TripUAE-Assistant/claude_engine_discovered.py"
    
    # Standard imports and context class
    base_code = '''
import os
import anthropic
from typing import List, Dict, Any

class ConversationContext:
    def __init__(self):
        """Initialize an empty conversation context with no messages."""
        self.messages = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation context.
        
        Args:
            role: The role of the message sender (user/assistant)
            content: The content of the message
        """
        self.messages.append({"role": role, "content": content})
'''
    
    # Different initialization based on client class
    if client_class.__name__ == 'Anthropic':
        init_code = '''
class ClaudeAssistant:
    def __init__(self, price_db):
        """Initialize the Claude Assistant."""
        self.price_db = price_db
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        print("Using Anthropic API with Claude")
        
        # System message
        self.system_message = """
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        """
'''
    else:
        init_code = '''
class ClaudeAssistant:
    def __init__(self, price_db):
        """Initialize the Claude Assistant."""
        self.price_db = price_db
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
        # Initialize Anthropic client with version header
        self.client = anthropic.Client(
            api_key=self.api_key,
            default_headers={"anthropic-version": "2023-06-01"}
        )
        
        print("Using Anthropic API with Claude-2")
        
        # System message
        self.system_message = """
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        """
'''
    
    # Generate response method based on available completion methods
    if 'client.messages.create()' in completion_methods:
        generate_response_code = '''
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Add user message to context
            context.add_message("user", user_message)
            
            # Convert context messages for API
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in context.messages]
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-2",
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
'''
    elif 'client.completions.create()' in completion_methods:
        generate_response_code = '''
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Format conversation history into prompt
            prompt = "\\n\\n".join([
                f"{'Human' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
                for msg in context.messages
            ])
            if prompt:
                prompt += "\\n\\n"
            prompt += f"Human: {user_message}\\n\\nAssistant:"
            
            # Make API call
            response = self.client.completions.create(
                prompt=prompt,
                model="claude-2",
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
'''
    elif 'client.completion()' in completion_methods:
        generate_response_code = '''
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Format conversation history into prompt
            prompt = ""
            
            # Add previous messages to the prompt
            for msg in context.messages:
                if msg["role"] == "user":
                    prompt += f"{anthropic.HUMAN_PROMPT} {msg['content']} "
                else:
                    prompt += f"{anthropic.AI_PROMPT} {msg['content']} "
            
            # Add current user message
            prompt += f"{anthropic.HUMAN_PROMPT} {user_message} {anthropic.AI_PROMPT}"
            
            # Make API call to Claude
            response = self.client.completion(
                prompt=prompt,
                model="claude-2",
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
'''
    else:
        # Generic fallback if we couldn't identify a specific completion method
        generate_response_code = '''
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # This is a placeholder method because we couldn't identify the right API call
            # You'll need to replace this with the correct API call for your version
            raise NotImplementedError(
                "Could not identify the correct API method to call. "
                "Please check the anthropic package documentation for your version."
            )
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return error_message
'''
    
    # Combine all code sections
    full_code = base_code + init_code + generate_response_code
    
    # Write to file
    with open(filepath, 'w') as f:
        f.write(full_code)
    
    print(f"\n✅ Created custom claude_engine.py at: {filepath}")
    print("To use this file, run: cp claude_engine_discovered.py claude_engine.py")

if __name__ == "__main__":
    discover_anthropic_api()
