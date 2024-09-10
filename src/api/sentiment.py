import requests
import logging
from api.tts_engine import add_to_tts_queue

logging.basicConfig(level=logging.INFO)

def list_models():
    """
    Fetches and returns a list of available models from the local Ollama instance.

    :return: A list of model names or 'error' if an issue occurs.
    """
    url = "http://localhost:11434/api/tags"
    try:
        response = requests.get(url)
        response.raise_for_status()
        models = [model['name'] for model in response.json().get('models', [])]
        logging.info(f"Available models: {models}")
        return models
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching models from Ollama: {e}")
        add_to_tts_queue("Error fetching models from Ollama.")
        return "error"

def analyze_text(text, model="llama3:latest", prompt_template="Analyze the sentiment: {text}", stream=False):
    """
    Send a request to the local Ollama instance for text analysis using various models.

    :param text: The input text for analysis.
    :param model: The model to use for analysis (default is 'llama3:latest').
    :param prompt_template: The prompt template to send to the model.
    :param stream: Boolean indicating if streaming mode should be enabled. Default is False.
    :return: The analysis result from Ollama or 'neutral'/'error' in case of issues.
    """
    # Check if the selected model is available
    available_models = list_models()
    if available_models == "error":
        add_to_tts_queue("Failed to retrieve model list.")
        return "error"

    if model not in available_models:
        error_message = f"Model '{model}' not found. Available models: {available_models}"
        logging.error(error_message)
        add_to_tts_queue(error_message)
        return "model_error"
    
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt_template.format(text=text),
        "stream": stream
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json().get('response', 'neutral').strip().lower()
        logging.info(f"Sentiment analysis result: {result}")
        add_to_tts_queue(f"Sentiment analysis result: {result}")
        return result
    except requests.exceptions.RequestException as e:
        error_message = f"Error communicating with Ollama: {e}"
        logging.error(error_message)
        add_to_tts_queue(error_message)
        return "error"
    except Exception as e:
        error_message = f"Unexpected error: {e}"
        logging.error(error_message)
        add_to_tts_queue(error_message)
        return "error"
