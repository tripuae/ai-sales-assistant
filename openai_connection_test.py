#!/usr/bin/env python3
"""
OpenAI API connection diagnostics for TripUAE Assistant
This script tests various OpenAI models and connection settings to troubleshoot API issues
"""

import os
import sys
import time
import logging
import requests
from dotenv import load_dotenv
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    logger.error("No OpenAI API key found in environment variables")
    print("ERROR: OPENAI_API_KEY not found in .env file")
    sys.exit(1)

# Mask the API key for logging purposes
masked_key = f"{api_key[:5]}...{api_key[-4:]}"
logger.info(f"Using API key: {masked_key}")

# Configure OpenAI client
openai.api_key = api_key

# Models to test in order of preference
MODELS_TO_TEST = [
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo"
]

def test_internet_connection():
    """Test general internet connectivity"""
    try:
        logger.info("Testing internet connection...")
        response = requests.get("https://api.openai.com", timeout=5)
        logger.info(f"OpenAI API endpoint reachable: Status code {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Internet connection test failed: {str(e)}")
        return False

def test_model(model_name):
    """Test a specific OpenAI model"""
    logger.info(f"Testing model: {model_name}")
    start_time = time.time()
    
    try:
        # Simple completion request
        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, this is a test message."}
            ],
            max_tokens=50,
            timeout=30  # 30 seconds timeout
        )
        
        duration = time.time() - start_time
        logger.info(f"✅ Model {model_name} works! Response time: {duration:.2f}s")
        logger.info(f"Response: {response.choices[0].message.content[:50]}...")
        return True, model_name, duration
    
    except openai.RateLimitError:
        logger.error(f"❌ Rate limit exceeded for {model_name}")
        return False, model_name, None
    
    except openai.AuthenticationError:
        logger.error(f"❌ Authentication error - API key may be invalid")
        return False, model_name, None
    
    except openai.BadRequestError as e:
        logger.error(f"❌ Bad request for {model_name}: {str(e)}")
        return False, model_name, None
        
    except Exception as e:
        logger.error(f"❌ Error with {model_name}: {str(e)}")
        return False, model_name, None

def run_all_tests():
    """Run all tests and determine best working model"""
    print("\n=== TRIPUAE ASSISTANT OPENAI API DIAGNOSTICS ===\n")
    
    # First, check internet connectivity
    if not test_internet_connection():
        print("\n❌ INTERNET CONNECTION ISSUE: Cannot reach OpenAI API endpoint")
        print("Please check your network connection, firewall settings, or proxy configuration")
        return None
    
    # Test each model
    working_models = []
    for model in MODELS_TO_TEST:
        success, model_name, duration = test_model(model)
        if success:
            working_models.append((model_name, duration))
        
        # Add a small delay between tests to avoid rate limiting
        time.sleep(1)
    
    # Show results
    if working_models:
        print("\n✅ WORKING MODELS:")
        for model, duration in working_models:
            print(f"  • {model} - Response time: {duration:.2f}s")
        
        # Get fastest model
        fastest_model = min(working_models, key=lambda x: x[1])[0]
        
        print(f"\n👉 RECOMMENDATION: Use model '{fastest_model}' in your configuration")
        print("\nTo update your code, change the model_name parameter in conversation_engine.py:\n")
        print(f"    model_name=\"{fastest_model}\",")
        
        return fastest_model
    else:
        print("\n❌ NO WORKING MODELS FOUND")
        print("Please check:")
        print("  1. Your API key is correct and has sufficient credits")
        print("  2. Your account has access to the models you're trying to use")
        print("  3. There are no network/firewall issues blocking the connection")
        return None

if __name__ == "__main__":
    best_model = run_all_tests()
    sys.exit(0 if best_model else 1)
