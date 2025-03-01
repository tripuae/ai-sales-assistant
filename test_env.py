import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Check if the API key exists
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    # Show only first 5 and last 4 characters for security
    print(f"API key found: {api_key[:5]}...{api_key[-4:]}")
else:
    print("API key not found in .env file")