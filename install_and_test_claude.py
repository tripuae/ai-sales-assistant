import os
import sys
import subprocess
from dotenv import load_dotenv

def install_anthropic_v030():
    """Install Anthropic v0.3.0 which has better compatibility with certain API keys"""
    try:
        print("Installing anthropic==0.3.0...")
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "anthropic"],
            check=True
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "anthropic==0.3.0"],
            check=True
        )
        print("✅ Installation complete.")
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False
    return True

def test_models():
    """Test various model names to find one that works"""
    # Need to import here after installation
    import anthropic
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        return None
    
    print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")
    
    # Create client
    try:
        client = anthropic.Client(api_key=api_key)
        print("✅ Client created successfully")
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return None
    
    # List of models to try (ordered by likelihood of working with older API versions)
    models_to_try = [
        "claude-v1", 
        "claude-1", 
        "claude-1.0", 
        "claude-1.2", 
        "claude-1.3",
        "claude-instant-v1", 
        "claude-instant-1.0",
        "claude-instant-1.1",
        "claude-2",
        "claude-2.0"
    ]
    
    # Try each model
    for model in models_to_try:
        print(f"\nTrying model: {model}...")
        try:
            prompt = f"{anthropic.HUMAN_PROMPT} Hello, who are you? {anthropic.AI_PROMPT}"
            response = client.completion(
                prompt=prompt,
                model=model,
                max_tokens_to_sample=100,
                stop_sequences=[anthropic.HUMAN_PROMPT]
            )
            print(f"✅ Success with {model}!")
            print(f"Response: {response['completion'].strip()}")
            return model
        except Exception as e:
            print(f"❌ Failed with {model}: {str(e)}")
    
    print("\n❌ No models worked.")
    return None

def update_claude_engine(model_name):
    """Update claude_engine.py with the working model name"""
    if not model_name:
        return False
        
    try:
        filepath = "/Users/tripuae/Desktop/TripUAE-Assistant/claude_engine.py"
        with open(filepath, "r") as f:
            content = f.read()
        
        # Replace all model references with the working model
        updated_content = content.replace('model="claude-2"', f'model="{model_name}"')
        updated_content = updated_content.replace('model="claude-3-sonnet"', f'model="{model_name}"')
        
        with open(filepath, "w") as f:
            f.write(updated_content)
        
        print(f"\n✅ Updated claude_engine.py to use model: {model_name}")
        return True
    except Exception as e:
        print(f"\n❌ Failed to update claude_engine.py: {e}")
        return False

def create_simple_example(model_name):
    """Create a simple example script showing how to use the working model"""
    if not model_name:
        return False
        
    filepath = "/Users/tripuae/Desktop/TripUAE-Assistant/working_claude_example.py"
    
    try:
        with open(filepath, "w") as f:
            f.write(f"""
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/working_claude_example.py
import os
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY environment variable not set.")
    exit(1)

# Create client
client = anthropic.Client(api_key=api_key)

# Create a completion
prompt = f"{{anthropic.HUMAN_PROMPT}} Tell me about Dubai's tourist attractions {{anthropic.AI_PROMPT}}"
response = client.completion(
    prompt=prompt,
    model="{model_name}",
    max_tokens_to_sample=300,
    stop_sequences=[anthropic.HUMAN_PROMPT]
)

print("\\nResponse from Claude:\\n")
print(response["completion"].strip())
""")
        print(f"\n✅ Created working example at: {filepath}")
        print("You can run this example with: python working_claude_example.py")
        return True
    except Exception as e:
        print(f"\n❌ Failed to create example: {e}")
        return False

def main():
    """Main function to install and test Claude"""
    # Install anthropic v0.3.0
    if not install_anthropic_v030():
        return
    
    # Test models and find a working one
    working_model = test_models()
    
    if working_model:
        # Update claude_engine.py
        update_claude_engine(working_model)
        
        # Create simple example
        create_simple_example(working_model)
        
        print(f"\n✅ Success! You can now use Claude with model: {working_model}")
        print("Try running: python claude_main.py")
    else:
        print("\n❌ Could not find a working model.")
        print("Please check your API key permissions or contact Anthropic support.")

if __name__ == "__main__":
    main()
