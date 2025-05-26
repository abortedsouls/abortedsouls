import os
import google.generativeai as genai

class DataChristChatbot:
    def __init__(self):
        """
        Initializes the DataChristChatbot.
        Retrieves the Gemini API key from the environment variables
        and configures the Gemini API client.
        Raises:
            ValueError: If the GEMINI_API_KEY environment variable is not set.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        # For now, we will use the Gemini 1.0 Pro model.
        # We can change this later if needed.
        self.model = genai.GenerativeModel('gemini-1.0-pro')

    def send_message(self, message: str) -> str:
        """
        Sends a message to the Gemini API and returns the response.

        Args:
            message: The user's message.

        Returns:
            The API's response as a string.
        Raises:
            Exception: If the API call fails.
        """
        try:
            if not message:
                # Returning an error message or raising an exception are both valid.
                # For now, returning an error message for simplicity.
                return "Error: Message cannot be empty."
            response = self.model.generate_content(message)
            return response.text
        except Exception as e:
            # Basic error handling for API call failures
            # Log the error for debugging in a real application
            # print(f"Error sending message to Gemini API: {e}")
            return f"Error sending message to Gemini API: {e}"

if __name__ == '__main__':
    # Example usage (requires GEMINI_API_KEY to be set in the environment)
    try:
        chatbot = DataChristChatbot()
        response = chatbot.send_message("Hello, how are you?")
        print(response)
        response_empty = chatbot.send_message("")
        print(response_empty)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
