"""
Test script for the enhanced Tourism AI Sales Assistant
This script allows interactive testing of the conversation engine
"""

import logging
import sys
import traceback
from typing import Optional, Dict, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run an interactive test of the enhanced conversation engine"""
    print("TripUAE Enhanced Sales Assistant - Interactive Test")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    # Import required modules with better error messages
    try:
        from database_schema import PriceDatabase
        from data_loader import create_database
        from conversation_engine import ResponseGenerator, ConversationContext
    except ImportError as e:
        module_name = str(e).split("'")[-2] if "'" in str(e) else str(e)
        logger.error(f"Could not import module: {module_name}")
        print(f"ERROR: Missing required module: {module_name}")
        print("Please ensure all required modules are installed and in the correct path.")
        return
    
    # Create the price database with better error handling
    try:
        price_db = create_database()
        if not price_db:
            logger.error("Database creation returned None")
            print("ERROR: Failed to create price database. Check your data files.")
            return
    except Exception as e:
        logger.error(f"Database creation failed: {e}")
        print(f"ERROR: Could not initialize the database: {e}")
        return
            
    # Create response generator with proper parameter checking
    try:
        # Check if ResponseGenerator accepts use_chatgpt parameter
        import inspect
        try:
            response_gen_params = inspect.signature(ResponseGenerator.__init__).parameters
            if 'use_chatgpt' in response_gen_params:
                logger.info("Creating ResponseGenerator with use_chatgpt=False")
                response_generator = ResponseGenerator(price_db, use_chatgpt=False)
            else:
                logger.info("Creating ResponseGenerator without use_chatgpt parameter")
                response_generator = ResponseGenerator(price_db)
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not inspect ResponseGenerator signature: {e}")
            # Fallback to basic instantiation
            response_generator = ResponseGenerator(price_db)
    except Exception as e:
        logger.error(f"Failed to initialize ResponseGenerator: {e}")
        print(f"ERROR: Could not create response generator: {e}")
        return
    
    # Create conversation context with validation
    try:
        context = ConversationContext()
        # Validate context has necessary attributes/methods
        if not hasattr(context, 'state'):
            logger.warning("ConversationContext lacks 'state' attribute")
    except Exception as e:
        logger.error(f"Failed to initialize ConversationContext: {e}")
        print(f"ERROR: Could not create conversation context: {e}")
        return
    
    # Get initial greeting with fallback
    try:
        # Empty string might cause issues, try with a proper greeting
        response = response_generator.generate_response(context, "Hello")
        print(f"Assistant: {response}\n")
    except Exception as e:
        logger.error(f"Error generating initial response: {e}")
        response = "Hello! I'm the TripUAE Assistant. How can I help you today?"
        print(f"Assistant: {response}\n")
    
    # Main interaction loop
    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended due to keyboard interrupt.")
            break
                
        if user_input.lower() in ["exit", "quit"]:
            print("\nSession ended.")
            break
        
        # Skip empty inputs
        if not user_input.strip():
            print("Please enter a question or request.")
            continue
        
        # Generate response with detailed error handling
        try:
            response = response_generator.generate_response(context, user_input)
            print(f"\nAssistant: {response}\n")
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            print(f"\nAssistant: I'm sorry, I encountered an error processing your request.")
            print(f"Debug - Error details: {str(e)}\n")
        
        # Print current context state in a structured way
        print_debug_context(context)

def print_debug_context(context: Any) -> None:
    """Print debug information about the current context in a structured way"""
    print("Debug - Current Context:")
    
    # Safe attribute access helper
    def safe_get(obj: Any, attr: str, default: Any = "Not set") -> Any:
        """Safely get an attribute value from an object"""
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            return value if value is not None else default
        return default
    
    # Print state information
    if hasattr(context, 'state') and context.state is not None:
        state_value = safe_get(context.state, 'value') if hasattr(context.state, 'value') else "Unknown"
        print(f"Debug - State: {state_value}")
    else:
        print("Debug - State: Not available")
    
    # Print customer information if available
    if hasattr(context, 'customer') and context.customer is not None:
        customer = context.customer
        print(f"Debug - Emirate: {safe_get(customer, 'emirate')}")
        print(f"Debug - Group Size: {safe_get(customer, 'group_size')}")
        print(f"Debug - Interests: {safe_get(customer, 'interests', [])}")
        print(f"Debug - Selected Tour: {safe_get(customer, 'selected_tour')}")
        
        objections = safe_get(customer, 'objections_raised', [])
        if objections:
            print(f"Debug - Objections: {objections}")
    else:
        print("Debug - Customer data not available")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)