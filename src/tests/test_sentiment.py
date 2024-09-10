import unittest
from unittest.mock import patch, MagicMock
from api.sentiment import analyze_text, list_models, update_ui

class TestSentimentAnalysis(unittest.TestCase):
    
    @patch('api.sentiment.requests.get')
    def test_list_models_success(self, mock_get):
        """Test that list_models returns models on a successful API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'models': [{'name': 'llama3:latest'}, {'name': 'another_model'}]
        }
        mock_get.return_value = mock_response
        
        models = list_models()
        self.assertEqual(models, ['llama3:latest', 'another_model'])

    @patch('api.sentiment.requests.get')
    def test_list_models_connection_error(self, mock_get):
        """Test that list_models handles connection errors gracefully."""
        mock_get.side_effect = requests.ConnectionError
        result = list_models()
        self.assertEqual(result, 'error')

    @patch('api.sentiment.requests.get')
    def test_list_models_timeout(self, mock_get):
        """Test that list_models handles timeouts gracefully."""
        mock_get.side_effect = requests.Timeout
        result = list_models()
        self.assertEqual(result, 'error')

    @patch('api.sentiment.requests.post')
    @patch('api.sentiment.list_models', return_value=["llama3:latest"])
    @patch('api.sentiment.update_ui')
    def test_analyze_text_success(self, mock_update_ui, mock_list_models, mock_post):
        """Test that analyze_text returns the correct sentiment result on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'positive'}
        mock_post.return_value = mock_response

        root = MagicMock()
        label = MagicMock()
        
        result = analyze_text("This is a test text", root, label)
        self.assertEqual(result, 'positive')
        mock_update_ui.assert_called_with(root, label, "Sentiment analysis result: positive")

    @patch('api.sentiment.requests.post')
    @patch('api.sentiment.list_models', return_value=["llama3:latest"])
    @patch('api.sentiment.update_ui')
    def test_analyze_text_connection_error(self, mock_update_ui, mock_list_models, mock_post):
        """Test that analyze_text handles connection errors."""
        mock_post.side_effect = requests.ConnectionError
        
        root = MagicMock()
        label = MagicMock()

        result = analyze_text("This is a test text", root, label)
        self.assertEqual(result, 'error')
        mock_update_ui.assert_called_with(root, label, "Error connecting to Ollama. Ensure the server is running.")

    @patch('api.sentiment.requests.post')
    @patch('api.sentiment.list_models', return_value=["llama3:latest"])
    @patch('api.sentiment.update_ui')
    def test_analyze_text_timeout(self, mock_update_ui, mock_list_models, mock_post):
        """Test that analyze_text handles timeouts."""
        mock_post.side_effect = requests.Timeout
        
        root = MagicMock()
        label = MagicMock()

        result = analyze_text("This is a test text", root, label)
        self.assertEqual(result, 'error')
        mock_update_ui.assert_called_with(root, label, "Timeout during sentiment analysis. Check your network or server.")

    @patch('api.sentiment.requests.post')
    @patch('api.sentiment.list_models', return_value=["llama3:latest"])
    @patch('api.sentiment.update_ui')
    def test_analyze_text_model_error(self, mock_update_ui, mock_list_models, mock_post):
        """Test that analyze_text handles missing models."""
        mock_list_models.return_value = ["other_model"]
        
        root = MagicMock()
        label = MagicMock()

        result = analyze_text("This is a test text", root, label, model="llama3:latest")
        self.assertEqual(result, 'model_error')
        mock_update_ui.assert_called_with(root, label, "Model 'llama3:latest' not found. Available models: ['other_model']")

    @patch('api.sentiment.requests.post')
    @patch('api.sentiment.list_models', return_value=["llama3:latest"])
    @patch('api.sentiment.update_ui')
    def test_analyze_text_request_exception(self, mock_update_ui, mock_list_models, mock_post):
        """Test that analyze_text handles request exceptions."""
        mock_post.side_effect = requests.RequestException("Request failed")
        
        root = MagicMock()
        label = MagicMock()

        result = analyze_text("This is a test text", root, label)
        self.assertEqual(result, 'error')
        mock_update_ui.assert_called_with(root, label, "Error communicating with Ollama.")

    def test_update_ui(self):
        """Test that the update_ui function updates the label in the Tkinter UI."""
        root = MagicMock()
        label = MagicMock()

        update_ui(root, label, "Test sentiment result")
        root.after.assert_called_once_with(0, label.config, text="Test sentiment result")


if __name__ == '__main__':
    unittest.main()
