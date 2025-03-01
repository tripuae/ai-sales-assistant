import os
import sys
import subprocess

def check_and_upgrade():
    """Check and upgrade the environment if needed"""
    print("===== Alternative Claude Implementation =====")
    
    # First, check if we need to upgrade the anthropic package
    print("Checking anthropic package version...")
    try:
        current_version = subprocess.run(
            [sys.executable, "-m", "pip", "show", "anthropic"],
            capture_output=True,
            text=True,
            check=True
        ).stdout
        print(current_version)
        
        # Upgrade to the latest version
        print("\nUpgrading to latest anthropic package...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "anthropic"],
            check=True
        )
    except Exception as e:
        print(f"Error checking/upgrading package: {e}")
    
    # Create a new approach using langchain
    try:
        print("\nChecking if langchain packages are installed...")
        
        # Try to import necessary langchain packages
        try:
            import langchain
            print("✅ Langchain is already installed")
        except ImportError:
            print("Installing langchain...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "langchain"],
                check=True
            )
        
        try:
            import langchain_anthropic
            print("✅ langchain-anthropic is already installed")
        except ImportError:
            print("Installing langchain-anthropic...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "langchain-anthropic"],
                check=True
            )
        
        # Create the alternative implementation
        create_langchain_implementation()
        
    except Exception as e:
        print(f"Error setting up langchain: {e}")
        
    print("\nSetup complete!")

def create_langchain_implementation():
    """Create an alternative implementation using langchain"""
    filepath = "/Users/tripuae/Desktop/TripUAE-Assistant/langchain_claude_engine.py"
    
    code = '''
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/langchain_claude_engine.py
import os
from typing import List, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain.schema import SystemMessage, HumanMessage

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
            
        # Initialize Anthropic client via langchain
        # Try different models in order of preference
        models_to_try = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240229",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "claude-2.0",
            "claude-instant-1"
        ]
        
        self.model = None
        for model in models_to_try:
            try:
                print(f"Trying model: {model}")
                self.model = ChatAnthropic(
                    model=model,
                    anthropic_api_key=self.api_key,
                    temperature=0.7
                )
                # If we get here, the model is valid
                print(f"✅ Using model: {model}")
                break
            except Exception as e:
                print(f"❌ Model {model} failed: {str(e)}")
        
        if not self.model:
            raise ValueError("No working Claude model found")
            
        # System message
        self.system_message = """
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        """
    
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
            # Format messages for langchain
            langchain_messages = [
                SystemMessage(content=self.system_message)
            ]
            
            # Add conversation history
            for msg in context.messages:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                else:
                    langchain_messages.append(SystemMessage(content=msg["content"]))
            
            # Add current message
            langchain_messages.append(HumanMessage(content=user_message))
            
            # Call API through langchain
            response = self.model.invoke(langchain_messages)
            
            # Get response text
            response_text = response.content
            
            # Add messages to context
            context.add_message("user", user_message)
            context.add_message("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return error_message
'''
    
    # Write the file
    with open(filepath, 'w') as f:
        f.write(code)
    
    print(f"\n✅ Created langchain implementation at: {filepath}")
    print("\nTo use this implementation:")
    print("1. Copy this file: cp langchain_claude_engine.py claude_engine.py")
    print("2. Run your main script: python claude_main.py")
    
    # Also create a test script
    test_filepath = "/Users/tripuae/Desktop/TripUAE-Assistant/test_langchain_claude.py"
    
    test_code = '''
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/test_langchain_claude.py
import os
from dotenv import load_dotenv
from langchain_claude_engine import ClaudeAssistant, ConversationContext

def main():
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set in environment or .env file")
        return
        
    print(f"API key found: {api_key[:5]}...{api_key[-4:]}")
    
    # Create assistant and context
    try:
        assistant = ClaudeAssistant(price_db=None)
        context = ConversationContext()
        
        # Test with a simple message
        test_message = "Hello, which AI model are you using?"
        print(f"\\nSending test message: '{test_message}'")
        
        response = assistant.generate_response(context, test_message)
        print(f"\\nResponse: {response}")
        
        print("\\n✅ Langchain Claude implementation is working!")
    except Exception as e:
        print(f"\\n❌ Error testing Langchain Claude: {e}")

if __name__ == "__main__":
    main()
'''
    
    with open(test_filepath, 'w') as f:
        f.write(test_code)
    
    print(f"Created test script at: {test_filepath}")
    print("Run it with: python test_langchain_claude.py")

if __name__ == "__main__":
    check_and_upgrade()
