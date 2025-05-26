import sys
# Adjusting path for sibling module import if necessary,
# though for direct execution within the 'app' directory or if 'datachrist' is in PYTHONPATH,
# 'from chatbot import DataChristChatbot' should work.
# If running from the root 'datachrist' directory as 'python -m app.cli',
# then 'from .chatbot import DataChristChatbot' is more robust.
try:
    from chatbot import DataChristChatbot
except ImportError:
    # This fallback allows running the script directly from the 'app' directory for development
    # or if the 'datachrist' package is not installed/recognized in the current PYTHONPATH.
    sys.path.append('..') # Assuming cli.py is in app/ and chatbot.py is in app/
    from chatbot import DataChristChatbot


def run_cli():
    """
    Runs the command-line interface for the DataChristChatbot.
    """
    try:
        chatbot = DataChristChatbot()
        print("DataChrist Chatbot CLI started. Type 'quit' to exit.")
    except ValueError as e:
        print(f"Error initializing chatbot: {e}")
        print("Please ensure the GEMINI_API_KEY environment variable is set.")
        return # Exit if chatbot cannot be initialized

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Exiting chatbot CLI. Goodbye!")
            break

        if not user_input.strip():
            print("Bot: Please enter a message.")
            continue

        try:
            response = chatbot.send_message(user_input)
            print(f"Bot: {response}")
        except Exception as e:
            # This catches errors from send_message, like API connection issues
            print(f"Error sending message or receiving response: {e}")
            # Optionally, decide if the CLI should exit on such errors or allow retries
            # For now, it continues the loop

if __name__ == "__main__":
    run_cli()
