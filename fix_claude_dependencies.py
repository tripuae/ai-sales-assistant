import os
import sys
import subprocess

def fix_environment():
    """Fix the Python environment to work with Claude API"""
    print("===== Fixing Claude API dependencies =====")
    
    # Uninstall problematic packages
    print("\nUninstalling conflicting packages...")
    packages_to_remove = ["anthropic", "pydantic", "httpx", "httpcore"]
    for package in packages_to_remove:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", package],
            check=False
        )
    
    # Install packages in the correct order with compatible versions
    print("\nInstalling compatible versions...")
    
    # Install pydantic v1 first (which has ModelField in pydantic.fields)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pydantic==1.10.8"],
        check=True
    )
    
    # Install httpx with a compatible version
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "httpx==0.23.3"],
        check=True
    )
    
    # Install anthropic with a version known to work with pydantic v1
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "anthropic==0.2.8"],
        check=True
    )
    
    # Check installed versions
    print("\nVerifying installed packages:")
    for package in ["anthropic", "pydantic", "httpx"]:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                print(f"{package}: {line.split(':', 1)[1].strip()}")
    
    print("\nCreating simple test script...")
    create_claude_test_script()
    
    print("\n===== Fix complete! =====")
    print("To test if Claude is working correctly, run:")
    print("python test_claude_setup.py")
    print("\nIf that works, try your main application:")
    print("python claude_main.py")

def create_claude_test_script():
    """Create a simple test script to verify Claude API works"""
    test_script = """
# filepath: /Users/tripuae/Desktop/TripUAE-Assistant/test_claude_setup.py
import os
import anthropic
from dotenv import load_dotenv

def test_claude_api():
    # Load .env file if it exists
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        return False
        
    print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")
    
    try:
        # Create client
        client = anthropic.Client(api_key=api_key)
        print("✅ Client created successfully")
        
        # Try a simple completion
        print("Sending test request to Claude API...")
        prompt = f"{anthropic.HUMAN_PROMPT} Tell me a short fact about Dubai. {anthropic.AI_PROMPT}"
        
        response = client.completion(
            prompt=prompt,
            model="claude-2",  # Try with claude-2 model
            max_tokens_to_sample=100,
            stop_sequences=[anthropic.HUMAN_PROMPT]
        )
        
        print("✅ API call successful!")
        print(f"\\nResponse from Claude:\\n")
        print(response["completion"].strip())
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
if __name__ == "__main__":
    test_claude_api()
"""
    
    with open("/Users/tripuae/Desktop/TripUAE-Assistant/test_claude_setup.py", "w") as f:
        f.write(test_script)

if __name__ == "__main__":
    fix_environment()
