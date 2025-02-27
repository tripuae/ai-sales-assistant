import os
import logging
import openai
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ConversationContext:
    def __init__(self):
        self.messages = []
        
    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        
class OpenAIAssistant:
    def __init__(self, price_db):
        self.price_db = price_db
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_message = """
        You are a friendly tourism assistant for TripUAE, a company offering tours in UAE.
        Available tours include:
        1. Desert Jeep Safari - Starting from $40 for adults, $35 for children
        2. Dubai City Tour - Starting from $40 for adults, $35 for children
        3. Night Cruise in Dubai Marina - Starting from $50 for adults, $45 for children
        
        Respond helpfully to customer inquiries about tours, prices, and bookings.
        You can communicate in English or Russian, depending on the customer's preference.
        Be friendly and professional.
        """
        
    def generate_response(self, context, user_message):
        try:
            # Add the user message to context
            if user_message:
                context.add_message("user", user_message)
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_message}
            ] + context.messages
            
            logger.debug(f"Sending to OpenAI: {messages}")
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using a faster model for quicker responses
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract and save response
            response_text = response.choices[0].message.content
            context.add_message("assistant", response_text)
            logger.debug(f"Got response from OpenAI: {response_text[:30]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error calling OpenAI: {str(e)}", exc_info=True)
            return f"I'm sorry, I'm having trouble connecting to my knowledge base. Error: {str(e)}"

def test_openai():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No OpenAI API key found in .env file!")
        return False
    
    print(f"Testing with API key: {api_key[:5]}...")
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}]
        )
        print(f"OpenAI test successful: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"OpenAI test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_openai()