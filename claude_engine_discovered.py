
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

    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Format conversation history into prompt
            prompt = "\n\n".join([
                f"{'Human' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
                for msg in context.messages
            ])
            if prompt:
                prompt += "\n\n"
            prompt += f"Human: {user_message}\n\nAssistant:"
            
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
