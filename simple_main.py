import logging
from database_schema import PriceDatabase
from data_loader import create_database
from conversation_engine import ResponseGenerator, ConversationContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def interactive_console_mode(response_generator):
    """Run an interactive console session with the sales assistant."""
    print("TripUAE Sales Assistant - Simple Mode")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    # Create conversation context
    context = ConversationContext()
    
    # Initial greeting
    response = response_generator.generate_response(context, "")
    print(f"Assistant: {response}\n")
    
    # Main interaction loop
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("\nSession ended.")
            break
        response = response_generator.generate_response(context, user_input)
        print(f"\nAssistant: {response}\n")

def main():
    # Create price database
    price_db = create_database()
    
    # Create response generator - NO advanced integrations
    response_generator = ResponseGenerator(price_db, use_chatgpt=False, use_llama_index=False)
    
    # Run interactive mode
    interactive_console_mode(response_generator)

if __name__ == "__main__":
    main()