import os
from dotenv import load_dotenv
import openai

def test_openai_connection():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: No OpenAI API key found in .env file!")
        return
    
    print(f"API Key (first 5 chars): {api_key[:5]}...")
    
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}]
        )
        print(f"OpenAI test SUCCESS! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"OpenAI test FAILED: {str(e)}")

if __name__ == "__main__":
    print("Testing OpenAI connection...")
    test_openai_connection()