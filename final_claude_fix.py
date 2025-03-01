import os
import sys
import subprocess

def final_fix():
    """Apply the final fix to get Claude working"""
    print("===== Final Claude API Fix =====")

    # Install a version of the Anthropic SDK that supports the version header
    print("\nInstalling compatible Anthropic SDK version...")
    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", "anthropic"],
        check=True
    )
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "anthropic==0.4.1"],
        check=True
    )
    
    print("\nCreating updated claude_engine.py...")
    create_updated_engine()
    
    print("\n===== Fix complete! =====")
    print("Now try running:")
    print("python claude_main.py")

def create_updated_engine():
    """Create an updated Claude engine file that works with the API version header requirement"""
    code = '''
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
        """Initialize the Claude Assistant.
        
        Args:
            price_db: Database containing pricing information for tours
        """
        # Store price database for reference in responses
        self.price_db = price_db
        
        # Load API key from environment variables
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
        # Initialize Anthropic client with API version header
        self.client = anthropic.Client(
            api_key=self.api_key,
            # Add the required API version header
            default_headers={"anthropic-version": "2023-06-01"}
        )
        
        print("Using Anthropic API with Claude-2")
        
        # System message defining the assistant's role and capabilities
        self.system_message = """
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        """
    
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API.
        
        Args:
            context: The conversation context containing message history
            user_message: The latest message from the user
            
        Returns:
            str: The generated response from Claude
        """
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
            
            # Make API call to Claude with API version header
            response = self.client.completion(
                prompt=prompt,
                model="claude-2",
                max_tokens_to_sample=1000,
                stop_sequences=[anthropic.HUMAN_PROMPT],
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
    
    with open("claude_engine.py", 'w') as f:
        f.write(code)

if __name__ == "__main__":
    final_fix()
