import requests
import logging
from api.tts_engine import add_to_tts_queue

# Initialize logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def list_models():
    """
    Fetches and returns a list of available models from the local Ollama instance.
    
    Handles connection errors, timeouts, and other issues gracefully, and logs 
    all relevant actions and errors.
    
    :return: A list of model names or 'error' if an issue occurs.
    """
    url = "http://localhost:11434/api/tags"
    
    try:
        logging.info("Attempting to fetch available models from Ollama...")
        response = requests.get(url)
        response.raise_for_status()  # Raise error for non-2xx responses
        
        models = [model['name'] for model in response.json().get('models', [])]
        logging.info(f"Available models fetched successfully: {models}")
        return models

    except requests.ConnectionError:
        error_message = "Ollama server not found. Ensure Ollama is installed and running on localhost:11434."
        logging.error(error_message)
        add_to_tts_queue(error_message)
        return "error"

    except requests.Timeout:
        error_message = "Ollama server timeout. Check the server or network status."
        logging.error(error_message)
        add_to_tts_queue(error_message)
        return "error"

    except requests.RequestException as e:
        error_message = f"RequestException while fetching models: {e}"
        logging.error(error_message)
        add_to_tts_queue("Error fetching models from Ollama.")
        return "error"

    except Exception as e:
        error_message = f"Unexpected error occurred during model fetching: {e}"
        logging.error(error_message)
        add_to_tts_queue("Unexpected error occurred while fetching models.")
        return "error"

def analyze_text(text, root, label, model="llama3:latest", prompt_template="Analyze the sentiment: {text}", stream=False):
    """
    Send a request to the local Ollama instance for text sentiment analysis and update the UI.

    :param text: The input text for analysis.
    :param root: The root Tkinter instance, used to update the UI on the main thread.
    :param label: The Tkinter label where the sentiment result will be displayed.
    :param model: The model to use for analysis (default is 'llama3:latest').
    :param prompt_template: The prompt template to send to the model.
    :param stream: Boolean indicating if streaming mode should be enabled. Default is False.
    :return: The analysis result from Ollama or 'neutral'/'error'/'model_error' in case of issues.
    """
    logging.info(f"Starting sentiment analysis for text: {text[:50]}...")  # Log part of the text for reference

    # Fetch the available models
    available_models = list_models()
    if available_models == "error":
        error_message = "Failed to retrieve model list."
        logging.error(error_message)
        add_to_tts_queue(error_message)
        update_ui(root, label, error_message)
        return "error"

    # Validate the chosen model
    if model not in available_models:
        error_message = f"Model '{model}' not found. Available models: {available_models}"
        logging.error(error_message)
        add_to_tts_queue(error_message)
        update_ui(root, label, error_message)
        return "model_error"

    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt_template.format(text=text),
        "stream": stream
    }

    try:
        logging.info(f"Sending sentiment analysis request to model '{model}'...")
        response = requests.post(url, json=data)
        response.raise_for_status()

        # Extract and clean the result
        result = response.json().get('response', 'neutral').strip().lower()
        logging.info(f"Sentiment analysis result: {result}")
        add_to_tts_queue(f"Sentiment analysis result: {result}")
        
        # Update the UI with the result on the main thread
        update_ui(root, label, f"Sentiment analysis result: {result}")
        return result

    except requests.ConnectionError:
        error_message = "Error connecting to Ollama. Ensure the server is running."
        logging.error(error_message)
        add_to_tts_queue(error_message)
        update_ui(root, label, error_message)
        return "error"

    except requests.Timeout:
        error_message = "Timeout during sentiment analysis. Check your network or server."
        logging.error(error_message)
        add_to_tts_queue(error_message)
        update_ui(root, label, error_message)
        return "error"

    except requests.RequestException as e:
        error_message = f"Error communicating with Ollama: {e}"
        logging.error(error_message)
        add_to_tts_queue("Error communicating with Ollama.")
        update_ui(root, label, error_message)
        return "error"

    except Exception as e:
        error_message = f"Unexpected error during sentiment analysis: {e}"
        logging.error(error_message)
        add_to_tts_queue(error_message)
        update_ui(root, label, error_message)
        return "error"

def update_ui(root, label, text):
    """
    Ensures that the UI is updated in the main thread to avoid Tkinter threading issues.
    
    :param root: The Tkinter root object.
    :param label: The label widget to be updated with the result text.
    :param text: The text to display in the label.
    """
    root.after(0, lambda: label.config(text=text))
