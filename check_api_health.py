#!/usr/bin/env python3
import os
import sys
import time
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_api_health():
    """Check if the OpenAI API is responsive"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OpenAI API key not found in environment variables")
        return False
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        print("🔍 Testing connection to OpenAI API...")
        start_time = time.time()
        
        # Make a minimal test request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=5
        )
        
        elapsed = time.time() - start_time
        print(f"✅ API connection successful (response time: {elapsed:.2f}s)")
        print(f"✅ API response: {response.choices[0].message.content}")
        
        return True
    except openai.RateLimitError:
        print("❌ ERROR: Rate limit exceeded. Your account might be at quota, or you need to add billing info.")
    except openai.APIConnectionError:
        print("❌ ERROR: Unable to connect to OpenAI API. Check your internet connection and proxy settings.")
    except openai.AuthenticationError:
        print("❌ ERROR: Authentication failed. Your API key might be invalid or expired.")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("OpenAI API Health Check")
    print("======================")
    
    success = check_api_health()
    
    if success:
        print("\n✅ Your OpenAI API connection is working correctly")
        sys.exit(0)
    else:
        print("\n❌ Your OpenAI API connection has issues")
        print("\nTroubleshooting tips:")
        print("1. Check that your OPENAI_API_KEY is correct")
        print("2. Verify that your API key has sufficient quota")
        print("3. Make sure your internet connection is stable")
        print("4. Check if you're using a proxy or VPN that might block the connection")
        sys.exit(1)
