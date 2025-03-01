import os
from dotenv import load_dotenv
import openai

def test_openai_connection():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: No OpenAI API key found in .env file!")
        return False
    
    print(f"API Key (first 5 chars): {api_key[:5]}...")
    
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4.5-preview",  # Specify the exact model name
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Verify that you are running on the GPT-4.5 preview model. Can you confirm this?"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        print("Model Response Test:")
        print(f"Model Used: {response.model}")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"OpenAI test FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing OpenAI connection with GPT-4.5 preview...")
    test_openai_connection()