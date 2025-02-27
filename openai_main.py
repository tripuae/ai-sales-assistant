from simple_openai_engine import OpenAIAssistant, ConversationContext
from data_loader import create_database

def main():
    print("TripUAE OpenAI Assistant")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    # Create the database and assistant
    price_db = create_database()
    assistant = OpenAIAssistant(price_db)
    
    # Create conversation context
    context = ConversationContext()
    
    # Initial greeting
    greeting = "Hello! Welcome to TripUAE. How can I help you with your tour inquiries today?"
    context.add_message("assistant", greeting)
    print(f"Assistant: {greeting}\n")
    
    # Main interaction loop
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("\nSession ended.")
            break
        
        response = assistant.generate_response(context, user_input)
        print(f"\nAssistant: {response}\n")

if __name__ == "__main__":
    main()