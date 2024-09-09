import unittest, requests
from unittest.mock import patch
from requests.exceptions import JSONDecodeError
from src.api.sentiment import analyze_text


class TestSentimentAnalysis(unittest.TestCase):
    def check_model_availability(self, model_name):
        """
        Check if the provided model is available in Ollama's model list.
        """
        try:
            response = requests.get('http://localhost:11434/api/tags')
            available_models = response.json().get("models", [])
            model_names = [model["name"] for model in available_models]
            self.assertIn(model_name, model_names, f"Model '{model_name}' is not available in the model list.")
        except (requests.exceptions.RequestException, JSONDecodeError) as e:
            self.fail(f"Failed to check model availability: {e}")

    @patch('src.api.sentiment.requests.post')
    def test_analyze_sentiment_positive(self, mock_post):
        """
        Test for positive sentiment analysis.
        """
        mock_response = {"response": "positive"}
        mock_post.return_value.json.return_value = mock_response

        # Replace 'sentiment_model' with 'llama3:latest' or any existing model
        self.check_model_availability("llama3:latest")
        result = analyze_text("This is a great day!", model="llama3:latest")
        self.assertEqual(result, "positive")

    @patch('src.api.sentiment.requests.post')
    def test_analyze_sentiment_error(self, mock_post):
        """
        Test for an error during sentiment analysis.
        """
        mock_post.side_effect = Exception("Connection error")
        
        # Replace 'sentiment_model' with 'llama3:latest' or any existing model
        self.check_model_availability("llama3:latest")
        result = analyze_text("This is a bad day!", model="llama3:latest")
        self.assertEqual(result, "error")

    @patch('src.api.sentiment.requests.post')
    def test_translation_analysis(self, mock_post):
        """
        Test for translation analysis with a different model.
        """
        mock_response = {"response": "ceci est une journée merveilleuse"}
        mock_post.return_value.json.return_value = mock_response

        # Replace 'translation_model' with an actual model like 'llama3:latest'
        self.check_model_availability("llama3:latest")
        result = analyze_text("This is a wonderful day!", model="llama3:latest", prompt_template="Translate the following text: {text}")
        self.assertEqual(result, "ceci est une journée merveilleuse")


if __name__ == '__main__':
    unittest.main()
