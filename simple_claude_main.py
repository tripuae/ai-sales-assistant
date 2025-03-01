from simple_claude_engine import ClaudeAssistant, ConversationContext
from data_loader import create_database

def main():
    """
    Main function that initializes the assistant and handles the conversation loop.
    """
    # Initialize the price database
    price_db = create_database()
    
    # Create assistant instance
    assistant = ClaudeAssistant(price_db)
    
    # Create conversation context
    context = ConversationContext()
    
    # Initial greeting
    print("\nWelcome to TripUAE Assistant! How can I help you today?")
    print("(Type 'exit' or 'quit' to end the conversation)")
    
    # Conversation loop
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for using TripUAE Assistant. Have a great day!")
            break
        
        # Generate and print response
        response = assistant.generate_response(context, user_input)
        print(f"\nAssistant: {response}")

if __name__ == "__main__":
    main()
