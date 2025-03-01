
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
        self.messages.append({"role": role, "content": content})

class ClaudeAssistant:
    def __init__(self, price_db):
        """Initialize the Claude Assistant."""
        self.price_db = price_db
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        print("Using Claude Direct API with Messages endpoint")
        print("Model: claude-3-7-sonnet-20250219")
        
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
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in context.messages]
            
            # Call Claude API directly using requests
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-7-sonnet-20250219",
                    "system": self.system_message,
                    "messages": messages,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code != 200:
                error_msg = f"API error: {response.status_code} - {response.text}"
                print(error_msg)
                return f"Sorry, I encountered an error: {error_msg}"
                
            # Extract response text
            data = response.json()
            response_text = data.get('content', [{'text': 'No response'}])[0].get('text')
            
            # Add assistant response to context
            context.add_message("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return error_message
