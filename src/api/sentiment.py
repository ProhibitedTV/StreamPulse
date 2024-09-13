"""
api/sentiment.py

This module is responsible for performing sentiment analysis using a local Ollama instance.
It includes functions to fetch available models, perform sentiment analysis, and update a 
PyQt5-based user interface (UI) with the results. The module handles errors gracefully, logs 
actions and issues, and provides feedback using a text-to-speech (TTS) engine.

Functions:
    list_models - Fetches and returns a list of available models from Ollama.
    analyze_text - Sends a sentiment analysis request to Ollama and updates the UI with the result.
    update_ui - Ensures the PyQt5 UI is updated to reflect sentiment analysis results.
"""

import requests
import logging
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
from api.tts_engine import add_to_tts_queue  # Import for TTS notifications

# Initialize logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def list_models():
    """
    Fetches and returns a list of available models from the local Ollama instance.
    
    Handles connection errors, timeouts, and other issues gracefully, logging 
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
    Sends a request to the local Ollama instance for text sentiment analysis and updates the PyQt5 UI.

    :param text: The input text for analysis.
    :param root: The PyQt5 root QWidget instance, used to update the UI.
    :param label: The PyQt5 QLabel widget where the sentiment result will be displayed.
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
        
        # Update the UI with the result
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
    Ensures that the PyQt5 UI is updated with the sentiment result.

    PyQt5 operates with event loops, so we need to ensure that UI updates occur 
    within the main thread using QMetaObject.invokeMethod to safely update widgets 
    outside the thread performing the sentiment analysis.

    :param root: The PyQt5 parent QWidget object.
    :param label: The QLabel widget where the result will be displayed.
    :param text: The text to display in the QLabel.
    """
    QMetaObject.invokeMethod(label, "setText", Q_ARG(str, text))
