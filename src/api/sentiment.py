import requests
import logging

logging.basicConfig(level=logging.INFO)

def list_models():
    """
    Fetches and returns a list of available models from the local Ollama instance.

    :return: A list of model names or 'error' if an issue occurs.
    """
    url = "http://localhost:11434/api/models"
    try:
        response = requests.get(url)
        response.raise_for_status()
        models = response.json().get('models', [])
        return models
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching models from Ollama: {e}")
        return "error"


def analyze_text(text, model="sentiment_model", prompt_template="Analyze the sentiment: {text}", stream=False):
    """
    Send a request to the local Ollama instance for text analysis using various models.

    :param text: The input text for analysis.
    :param model: The model to use for analysis (default is 'sentiment_model').
    :param prompt_template: The prompt template to send to the model.
    :param stream: Boolean indicating if streaming mode should be enabled. Default is False.
    :return: The analysis result from Ollama or 'neutral'/'error' in case of issues.
    """
    # Check if the selected model is available
    available_models = list_models()
    if model not in available_models:
        logging.error(f"Model '{model}' not found. Available models: {available_models}")
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
        return result
    except requests.exceptions.RequestException as e:
        logging.error(f"Error communicating with Ollama: {e}")
        return "error"
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return "error"


# Example usage for sentiment analysis
result = analyze_text("This is a wonderful day!", model="sentiment_model")
print(f"Sentiment result: {result}")

# Example usage for a different model, like a summarization or translation model
result = analyze_text("Translate this text to French.", model="translation_model", prompt_template="Translate the following text: {text}")
print(f"Translation result: {result}")
