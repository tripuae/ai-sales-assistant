import os
import argparse
import json
import logging
from typing import Dict, Any, List, Optional

# Import components
from database_schema import PriceDatabase
from data_loader import create_database
from conversation_engine import ResponseGenerator, ConversationContext, CustomerProfile
from whatsapp_integration import initialize_whatsapp_integration, send_test_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def interactive_console_mode(response_generator: ResponseGenerator) -> None:
    """Run an interactive console session with the sales assistant."""
    print("TripUAE Sales Assistant - Interactive Console Mode")
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

def batch_test_mode(response_generator: ResponseGenerator, test_scenarios: List[Dict[str, Any]]) -> None:
    """Run a batch test with predefined scenarios."""
    print("TripUAE Sales Assistant - Batch Test Mode")
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\nScenario {i+1}: {scenario.get('name', 'Unnamed')}")
        print("-" * 50)
        
        # Create conversation context
        context = ConversationContext()
        
        # Set initial customer profile if provided
        if "initial_profile" in scenario:
            context.customer = CustomerProfile.from_dict(scenario["initial_profile"])
        
        # If no initial messages, get a greeting
        if not scenario.get("messages", []):
            response = response_generator.generate_response(context, "")
            print(f"Assistant: {response}\n")
        
        # Process each message
        for msg in scenario.get("messages", []):
            print(f"User: {msg}")
            response = response_generator.generate_response(context, msg)
            print(f"Assistant: {response}\n")
        
        print("-" * 50)
        print(f"Final state: {context.state.value}")
        print(f"Final customer profile: {json.dumps(context.customer.to_dict(), indent=2, ensure_ascii=False)}")
        print("\n")

def setup_whatsapp_mode(twilio_account_sid: str, twilio_auth_token: str, 
                          twilio_whatsapp_number: str, port: int) -> None:
    """Set up and run WhatsApp integration."""
    print("TripUAE Sales Assistant - WhatsApp Mode")
    print(f"Starting WhatsApp integration on port {port}")
    initialize_whatsapp_integration(twilio_account_sid, twilio_auth_token, twilio_whatsapp_number, port)

def main() -> None:
    """Main function for the TripUAE Sales Assistant."""
    parser = argparse.ArgumentParser(description="TripUAE Sales Assistant")
    parser.add_argument("--mode", type=str, choices=["interactive", "batch", "whatsapp"], 
                        default="interactive", help="Mode of operation")
    parser.add_argument("--test-scenarios", type=str, help="Path to test scenarios JSON file")
    parser.add_argument("--twilio-account-sid", type=str, 
                        default=os.environ.get("TWILIO_ACCOUNT_SID"),
                        help="Twilio Account SID")
    parser.add_argument("--twilio-auth-token", type=str, 
                        default=os.environ.get("TWILIO_AUTH_TOKEN"),
                        help="Twilio Auth Token")
    parser.add_argument("--twilio-whatsapp-number", type=str, 
                        default=os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"),
                        help="Twilio WhatsApp Number")
    parser.add_argument("--port", type=int, default=5000, help="Port for WhatsApp webhook server")
    
    args = parser.parse_args()
    
    # -------------------------------------------------------------------------
    # Replace your old ResponseGenerator instantiation with this new code:
    # -------------------------------------------------------------------------
    price_db = create_database()
    # Create the response generator with ChatGPT and LlamaIndex integrations enabled.
    response_generator = ResponseGenerator(price_db, use_chatgpt=True, use_llama_index=False)
    # -------------------------------------------------------------------------
    
    if args.mode == "interactive":
        interactive_console_mode(response_generator)
    elif args.mode == "batch":
        if not args.test_scenarios:
            raise ValueError("Test scenarios file must be provided for batch mode")
        with open(args.test_scenarios, "r", encoding="utf-8") as f:
            test_scenarios = json.load(f)
        batch_test_mode(response_generator, test_scenarios)
    elif args.mode == "whatsapp":
        if not args.twilio_account_sid or not args.twilio_auth_token:
            raise ValueError("Twilio credentials must be provided for WhatsApp mode")
        setup_whatsapp_mode(args.twilio_account_sid, args.twilio_auth_token, args.twilio_whatsapp_number, args.port)

if __name__ == "__main__":
    main()