import os
import sys
from typing import List, Dict, Any
import inspect

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
        
        # Import anthropic inside method to avoid global import issues
        try:
            import anthropic
            self.anthropic = anthropic
            
            # Print metadata to help with debugging
            print(f"Anthropic module found at: {anthropic.__file__}")
            if hasattr(anthropic, '__version__'):
                print(f"Anthropic version: {anthropic.__version__}")
            
            # Get API key from environment
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
            # Determine client class type and instantiate
            if hasattr(anthropic, 'Anthropic'):
                print("Using Anthropic.Anthropic client")
                self.client = anthropic.Anthropic(api_key=self.api_key)
            elif hasattr(anthropic, 'Client'):
                print("Using Anthropic.Client client")
                # Try with version header
                try:
                    self.client = anthropic.Client(
                        api_key=self.api_key,
                        default_headers={"anthropic-version": "2023-06-01"}
                    )
                except TypeError:
                    # Fall back without version header
                    self.client = anthropic.Client(api_key=self.api_key)
            else:
                raise ValueError("Could not find Anthropic or Client class in anthropic module")
            
            # Print available methods for debugging
            print("\nAvailable client methods:")
            for name, obj in inspect.getmembers(self.client):
                if not name.startswith('_'):  # Skip private methods
                    print(f"- {name}")
            
            # System message
            self.system_message = """
            You are a helpful tourism assistant for TripUAE, a company in Dubai.
            You provide information about Desert Safari, Dubai City Tour, and Night Cruise tours.
            Be friendly and helpful, and provide accurate pricing information when asked.
            """
            
        except ImportError:
            print("Error: anthropic package not installed")
            print("Try installing it with: pip install anthropic")
            sys.exit(1)
    
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            print(f"Generating response for: {user_message}")
            
            # Try different API methods that might be available
            if hasattr(self.client, 'completion'):
                return self._generate_with_completion(context, user_message)
            elif hasattr(self.client, 'completions') and hasattr(self.client.completions, 'create'):
                return self._generate_with_completions_create(context, user_message)
            elif hasattr(self.client, 'messages') and hasattr(self.client.messages, 'create'):
                return self._generate_with_messages_create(context, user_message)
            elif hasattr(self.client, 'complete'):
                return self._generate_with_complete(context, user_message)
            else:
                # Try to directly access methods that might be added dynamically
                method_names = dir(self.client)
                api_methods = [m for m in method_names if not m.startswith('_') and 
                              (m.endswith('create') or 'complet' in m.lower())]
                
                if api_methods:
                    print(f"Found potential API methods: {api_methods}")
                    return f"Sorry, I found potential API methods ({', '.join(api_methods)}) but don't know how to use them yet."
                else:
                    return "Sorry, I couldn't find any suitable API methods in the client object."
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return error_message
    
    def _generate_with_completion(self, context: ConversationContext, user_message: str):
        """Use client.completion() method"""
        # Format the conversation history
        prompt = ""
        for msg in context.messages:
            if msg["role"] == "user":
                prompt += f"{self.anthropic.HUMAN_PROMPT} {msg['content']} "
            else:
                prompt += f"{self.anthropic.AI_PROMPT} {msg['content']} "
        
        # Add current user message
        prompt += f"{self.anthropic.HUMAN_PROMPT} {user_message} {self.anthropic.AI_PROMPT}"
        
        # Call API
        response = self.client.completion(
            prompt=prompt,
            model="claude-2",
            max_tokens_to_sample=1000,
            stop_sequences=[self.anthropic.HUMAN_PROMPT]
        )
        
        # Extract response
        response_text = response["completion"].strip()
        
        # Add messages to context
        context.add_message("user", user_message)
        context.add_message("assistant", response_text)
        
        return response_text
    
    def _generate_with_completions_create(self, context: ConversationContext, user_message: str):
        """Use client.completions.create() method"""
        # Format conversation
        prompt = "\n\n".join([
            f"{'Human' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
            for msg in context.messages
        ])
        if prompt:
            prompt += "\n\n"
        prompt += f"Human: {user_message}\n\nAssistant:"
        
        # Call API
        response = self.client.completions.create(
            prompt=prompt,
            model="claude-2",
            max_tokens_to_sample=1000,
            stop_sequences=["Human:"]
        )
        
        # Process response
        response_text = response.completion.strip()
        context.add_message("user", user_message)
        context.add_message("assistant", response_text)
        return response_text
    
    def _generate_with_messages_create(self, context: ConversationContext, user_message: str):
        """Use client.messages.create() method"""
        # Add message to context
        context.add_message("user", user_message)
        
        # Format messages
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in context.messages]
        
        # Call API
        response = self.client.messages.create(
            model="claude-2",
            system=self.system_message,
            messages=messages,
            max_tokens=1000
        )
        
        # Process response
        response_text = response.content[0].text
        context.add_message("assistant", response_text)
        return response_text
    
    def _generate_with_complete(self, context: ConversationContext, user_message: str):
        """Use client.complete() method"""
        # Format conversation
        prompt = ""
        for msg in context.messages:
            if msg["role"] == "user":
                prompt += f"{self.anthropic.HUMAN_PROMPT} {msg['content']} "
            else:
                prompt += f"{self.anthropic.AI_PROMPT} {msg['content']} "
        
        # Add current message
        prompt += f"{self.anthropic.HUMAN_PROMPT} {user_message} {self.anthropic.AI_PROMPT}"
        
        # Call API
        response = self.client.complete(
            prompt=prompt,
            model="claude-2",
            max_tokens_to_sample=1000,
            stop_sequences=[self.anthropic.HUMAN_PROMPT]
        )
        
        # Process response
        if isinstance(response, dict):
            response_text = response.get("completion", "No completion found in response")
        else:
            response_text = str(response)
            
        # Update context
        context.add_message("user", user_message)
        context.add_message("assistant", response_text)
        return response_text
