import os
import sys
import json
import re
from dotenv import load_dotenv

def find_available_claude_models():
    """
    Try different Claude model names to find one that works with your API key.
    """
    print("===== Claude Model Finder =====")
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)
    
    print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")
    
    # Import anthropic here to ensure we use the installed version
    import anthropic
    print(f"Using Anthropic SDK version: {getattr(anthropic, '__version__', 'unknown')}")
    
    # Create client
    client = anthropic.Anthropic(api_key=api_key)
    print("✅ Client created successfully")
    
    # Models to try (ordered by likelihood of being available)
    model_candidates = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240229",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-3",
        "claude-2.1",
        "claude-2.0",
        "claude-2",
        "claude-instant-1.2",
        "claude-instant-1.1",
        "claude-instant-1.0",
        "claude-instant-1",
        "claude-1.3",
        "claude-1.2",
        "claude-1.1",
        "claude-1.0",
        "claude-1",
        "claude-v1"
    ]
    
    # Try each model
    working_models = []
    for model in model_candidates:
        print(f"\nTrying model: {model}")
        
        try:
            # Simple test message to check if model works
            messages = [{"role": "user", "content": "Say hello briefly"}]
            
            # Check if models.list endpoint exists to detect available models
            if hasattr(client, 'models') and hasattr(client.models, 'list'):
                try:
                    response = client.models.list()
                    available_models = [m.id for m in response.data]
                    print(f"Available models from API: {available_models}")
                    
                    # Only continue with models that are available according to API
                    if model not in available_models:
                        print(f"Model {model} not in available models list, skipping")
                        continue
                except Exception as e:
                    print(f"Error listing models: {e}")
                    # Continue with manual checks if models.list failed
            
            # Try creating a message with this model
            try:
                response = client.messages.create(
                    model=model,
                    messages=messages,
                    max_tokens=10
                )
                print(f"✅ Success with model {model}!")
                working_models.append({
                    "name": model,
                    "method": "messages.create",
                    "test_response": response.content[0].text[:50] + "..."
                })
            except Exception as msg_error:
                print(f"messages.create failed: {msg_error}")
                
                # Try completions method if messages failed
                try:
                    prompt = f"{anthropic.HUMAN_PROMPT} Say hello briefly {anthropic.AI_PROMPT}"
                    response = client.completions.create(
                        model=model,
                        prompt=prompt,
                        max_tokens_to_sample=10,
                        stop_sequences=[anthropic.HUMAN_PROMPT]
                    )
                    print(f"✅ Success with model {model} using completions.create!")
                    working_models.append({
                        "name": model,
                        "method": "completions.create",
                        "test_response": response.completion[:50] + "..."
                    })
                except Exception as comp_error:
                    print(f"completions.create failed: {comp_error}")
                    
                    # Last resort: try completion method for older APIs
                    try:
                        prompt = f"{anthropic.HUMAN_PROMPT} Say hello briefly {anthropic.AI_PROMPT}"
                        response = client.completion(
                            prompt=prompt,
                            model=model,
                            max_tokens_to_sample=10,
                            stop_sequences=[anthropic.HUMAN_PROMPT]
                        )
                        print(f"✅ Success with model {model} using completion()!")
                        working_models.append({
                            "name": model, 
                            "method": "completion",
                            "test_response": response["completion"][:50] + "..."
                        })
                    except Exception as legacy_error:
                        print(f"completion() failed: {legacy_error}")
        
        except Exception as e:
            print(f"❌ General error with model {model}: {e}")
    
    # Summarize findings
    if working_models:
        print("\n✅ Found working Claude models:")
        for i, model_info in enumerate(working_models, 1):
            print(f"{i}. {model_info['name']} (using {model_info['method']})")
            print(f"   Test response: {model_info['test_response']}")
        
        # Create a working config file
        create_working_claude_config(working_models[0], api_key)
        
        # Create a updated claude_engine file
        create_updated_claude_engine(working_models[0])
        
        return working_models[0]
    else:
        print("\n❌ No working Claude models found.")
        print("Please check your API key permissions.")
        return None

def create_working_claude_config(model_info, api_key):
    """Create a configuration file with working model information"""
    config = {
        "api_key": api_key[:5] + "..." + api_key[-4:],  # Redacted for security
        "model_name": model_info["name"],
        "method": model_info["method"],
        "test_successful": True,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    
    with open("/Users/tripuae/Desktop/TripUAE-Assistant/claude_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Saved working configuration to claude_config.json")

def create_updated_claude_engine(model_info):
    """Create an updated claude_engine.py file with the working model"""
    model_name = model_info["name"]
    method = model_info["method"]
    
    code = f'''
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/claude_engine_updated.py
import os
import anthropic
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
            
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        print("Using Anthropic API with model: {model_name}")
        
        # System message
        self.system_message = """
        You are a helpful and knowledgeable tourism assistant for TripUAE, a tourism company based in Dubai, UAE.
        You can provide information about their tours including Desert Safari, Dubai City Tour, and Night Cruise.
        Be friendly, informative, and helpful. Always provide accurate pricing information when asked about costs.
        """
    
    def generate_response(self, context: ConversationContext, user_message: str):
        """Generate a response using Claude API."""
        try:
'''
    
    # Add appropriate method based on what worked
    if method == "messages.create":
        code += '''
            # Add user message to context
            context.add_message("user", user_message)
            
            # Format messages for API
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in context.messages]
            
            # Call Claude API using messages.create
            response = self.client.messages.create(
                model="''' + model_name + '''",
                system=self.system_message,
                messages=messages,
                max_tokens=1000
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Add assistant response to context
            context.add_message("assistant", response_text)
            
            return response_text
'''
    elif method == "completions.create":
        code += '''
            # Format conversation history into prompt
            prompt = "\\n\\n".join([
                f"{'Human' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
                for msg in context.messages
            ])
            if prompt:
                prompt += "\\n\\n"
            prompt += f"Human: {user_message}\\n\\nAssistant:"
            
            # Call Claude API using completions.create
            response = self.client.completions.create(
                prompt=prompt,
                model="''' + model_name + '''",
                max_tokens_to_sample=1000,
                stop_sequences=["Human:"]
            )
            
            # Extract response text
            response_text = response.completion.strip()
            
            # Add messages to context
            context.add_message("user", user_message)
            context.add_message("assistant", response_text)
            
            return response_text
'''
    else:  # completion method
        code += '''
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
            
            # Call Claude API using completion
            response = self.client.completion(
                prompt=prompt,
                model="''' + model_name + '''",
                max_tokens_to_sample=1000,
                stop_sequences=[anthropic.HUMAN_PROMPT]
            )
            
            # Extract response text
            response_text = response["completion"].strip()
            
            # Add messages to context
            context.add_message("user", user_message)
            context.add_message("assistant", response_text)
            
            return response_text
'''
    
    # Add exception handling
    code += '''            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return error_message
'''
    
    # Write the file
    with open("/Users/tripuae/Desktop/TripUAE-Assistant/claude_engine_updated.py", "w") as f:
        f.write(code)
    
    print(f"\n✅ Created updated Claude engine file at claude_engine_updated.py")
    print("To use this file, run: cp claude_engine_updated.py claude_engine.py")

if __name__ == "__main__":
    find_available_claude_models()
