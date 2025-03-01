#!/usr/bin/env python3
"""
Test script for OpenAI API connection
"""

import os
import sys
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment variables.")
    print("Make sure you have a .env file with your API key.")
    exit(1)

print(f"Found API key: {api_key[:4]}...{api_key[-4:]}")

openai.api_key = api_key

def test_openai_connection():
    """Test connection to OpenAI API with proper error handling"""
    try:
        # Make a simple request
        print("Testing OpenAI API connection...")
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, this is a test."}
            ]
        )
        
        # Get response content
        content = response.choices[0].message.content
        
        print("Success! Received response:")
        print(content)
        print("\nYour OpenAI API key is working correctly.")
        return True
        
    except Exception as e:
        print(f"Error connecting to OpenAI API: {e}")
        print("\nPossible issues:")
        print("1. Your API key might be invalid")
        print("2. You might have no credits left on your OpenAI account")
        print("3. There could be a network/firewall issue")
        print("4. OpenAI service might be experiencing issues")
        return False

if __name__ == "__main__":
    # Run the test and set exit code accordingly
    success = test_openai_connection()
    sys.exit(0 if success else 1)
