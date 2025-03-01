
# Add this error handling around your bot initialization/operation:

try:
    # Bot initialization code
    # ...

    # Test OpenAI connectivity before starting
    logger.info("Testing OpenAI API connectivity...")
    test_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",  # Use gpt-3.5-turbo for the test as it's widely available
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    logger.info("OpenAI API connection successful!")
    
    # Start the bot
    # ...
except openai.AuthenticationError:
    logger.critical("OpenAI API key is invalid! Please check your .env file.")
    exit(1)
except openai.RateLimitError:
    logger.critical("OpenAI rate limit exceeded! Please try again later.")
    exit(1)
except Exception as e:
    logger.critical(f"Error during startup: {str(e)}")
    exit(1)
