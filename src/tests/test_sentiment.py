import unittest
from unittest.mock import patch
from api.sentiment import analyze_text

class TestSentimentAnalysis(unittest.TestCase):
    """
    Unit test class for testing text analysis using the Ollama API.
    """

    @patch('api.sentiment.requests.post')
    def test_analyze_sentiment_positive(self, mock_post):
        """
        Test for positive sentiment analysis.
        """
        mock_response = {"response": "positive"}
        mock_post.return_value.json.return_value = mock_response

        result = analyze_text("This is a great day!", model="sentiment_model")
        self.assertEqual(result, "positive")

    @patch('api.sentiment.requests.post')
    def test_analyze_sentiment_error(self, mock_post):
        """
        Test for an error during sentiment analysis.
        """
        mock_post.side_effect = Exception("Connection error")
        
        result = analyze_text("This is a bad day!", model="sentiment_model")
        self.assertEqual(result, "error")

    @patch('api.sentiment.requests.post')
    def test_translation_analysis(self, mock_post):
        """
        Test for translation analysis with a different model.
        """
        mock_response = {"response": "ceci est une journée merveilleuse"}
        mock_post.return_value.json.return_value = mock_response

        result = analyze_text("This is a wonderful day!", model="translation_model", prompt_template="Translate the following text: {text}")
        self.assertEqual(result, "ceci est une journée merveilleuse")

if __name__ == '__main__':
    unittest.main()
