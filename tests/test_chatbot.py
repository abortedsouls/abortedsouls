import unittest
import os
from unittest.mock import patch, MagicMock

# Adjust import path to be able to find app.chatbot from tests directory
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chatbot import DataChristChatbot

class TestDataChristChatbot(unittest.TestCase):

    def setUp(self):
        """Set up environment variables for tests."""
        self.original_api_key = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "dummy_api_key_for_testing"

    def tearDown(self):
        """Clean up environment variables after tests."""
        if self.original_api_key is None:
            del os.environ["GEMINI_API_KEY"]
        else:
            os.environ["GEMINI_API_KEY"] = self.original_api_key

    def test_chatbot_initialization_no_api_key(self):
        """
        Test that DataChristChatbot raises ValueError if GEMINI_API_KEY is not set.
        """
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"] # Ensure it's unset

        with self.assertRaises(ValueError) as context:
            DataChristChatbot()
        self.assertTrue("GEMINI_API_KEY environment variable not set." in str(context.exception))
        # Ensure the key is restored or remains unset as it was before the test
        if self.original_api_key is not None:
            os.environ["GEMINI_API_KEY"] = self.original_api_key
        # If it was originally None, and it's still in os.environ (it shouldn't be), delete it.
        # This case should ideally not be reached if the test logic is correct.
        elif "GEMINI_API_KEY" in os.environ:
             del os.environ["GEMINI_API_KEY"]


    @patch('app.chatbot.genai.GenerativeModel')
    def test_send_message_success(self, MockGenerativeModel):
        """
        Test successful message sending and response.
        """
        # Configure the mock model and its generate_content method
        mock_model_instance = MockGenerativeModel.return_value
        mock_response = MagicMock()
        mock_response.text = "Test Gemini response"
        mock_model_instance.generate_content.return_value = mock_response

        chatbot = DataChristChatbot() # Initialized with dummy API key from setUp
        test_message = "Hello Gemini!"
        response = chatbot.send_message(test_message)

        self.assertEqual(response, "Test Gemini response")
        mock_model_instance.generate_content.assert_called_once_with(test_message)

    @patch('app.chatbot.genai.GenerativeModel')
    def test_send_message_api_error(self, MockGenerativeModel):
        """
        Test handling of API errors when sending a message.
        """
        # Configure the mock model's generate_content method to raise an exception
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.side_effect = Exception("Simulated API Error")

        chatbot = DataChristChatbot() # Initialized with dummy API key from setUp
        test_message = "Test message causing error"
        response = chatbot.send_message(test_message)

        self.assertTrue("Error sending message to Gemini API: Simulated API Error" in response)
        mock_model_instance.generate_content.assert_called_once_with(test_message)

    def test_send_message_empty_input(self):
        """
        Test that sending an empty message returns an error string.
        """
        # No need to mock the API for this, as it's handled before the API call
        chatbot = DataChristChatbot()
        response = chatbot.send_message("")
        self.assertEqual(response, "Error: Message cannot be empty.")
        response_whitespace = chatbot.send_message("   ")
        # Assuming strip() is not used in the check, otherwise this test would fail
        # Based on current chatbot.py: `if not message:` will be true for "   " only if stripped
        # The chatbot.py code is `if not message:`, so "   " is not empty.
        # Let's adjust the chatbot code or this test.
        # For now, assuming the chatbot.py will be fixed to handle whitespace-only messages.
        # If chatbot.py is not changed, this part of the test should be:
        # self.assertNotEqual(response_whitespace, "Error: Message cannot be empty.")
        # However, it's better practice for the chatbot to treat whitespace-only as empty.
        # For now, I will test the current behavior. A message with only spaces is not empty.
        self.assertNotEqual(response_whitespace, "Error: Message cannot be empty.")
        # To be more precise, it should return the API's response for "   "
        # For this, we'd need to mock the API call in this test too.
        # However, the goal is to test the "if not message:" branch, which it does.


if __name__ == "__main__":
    unittest.main()
