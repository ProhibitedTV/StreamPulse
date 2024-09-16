"""
api/sentiment.py

This module is responsible for performing sentiment and political bias analysis using a local Ollama instance,
with the operations running asynchronously to avoid blocking the main PyQt5 interface.

The module includes functions for fetching available models from Ollama, analyzing text for sentiment and political bias,
and updating the user interface (UI) based on the analysis results. It integrates with a text-to-speech (TTS) engine to 
provide vocal feedback. 

Key Functions:
    - list_models: Asynchronously fetches the list of available models from Ollama.
    - analyze_text: Asynchronously analyzes text for sentiment and political bias, updating the UI and providing TTS feedback.
    - update_ui: Updates the PyQt5 UI with the sentiment and bias analysis result.

Logging is used to record all actions and potential errors, ensuring easy debugging and monitoring of the analysis process.

Dependencies:
    - aiohttp: For asynchronous HTTP requests.
    - asyncio: To manage asynchronous tasks.
    - PyQt5: For updating the graphical user interface.
    - TTS Engine: Integrated for adding text-to-speech feedback.
"""

import aiohttp
import logging
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
from api.tts_engine import add_to_tts_queue  # Import for TTS notifications

# Initialize logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def list_models():
    """
    Asynchronously fetches and returns a list of available models from the local Ollama instance.

    Handles connection errors, timeouts, and other issues gracefully, logging 
    all relevant actions and errors.

    :return: A list of model names or 'error' if an issue occurs.
    """
    url = "http://localhost:11434/api/tags"

    try:
        logging.info("Attempting to fetch available models from Ollama...")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP Error: {response.status}")
                models_data = await response.json()
                models = [model['name'] for model in models_data.get('models', [])]
                logging.info(f"Available models fetched successfully: {models}")
                return models

    except aiohttp.ClientError as e:
        error_message = f"Error fetching models from Ollama: {e}"
        logging.error(error_message)
        await add_to_tts_queue(error_message)
        return "error"

    except Exception as e:
        error_message = f"Unexpected error occurred during model fetching: {e}"
        logging.error(error_message)
        await add_to_tts_queue("Unexpected error occurred while fetching models.")
        return "error"


async def analyze_text(text, root, label, model="llama3:latest", prompt_template=None, stream=False):
    """
    Asynchronously sends a request to the local Ollama instance for text analysis (sentiment and political bias)
    and updates the PyQt5 UI.

    :param text: The input text for analysis.
    :param root: The PyQt5 root QWidget instance, used to update the UI.
    :param label: The PyQt5 QLabel widget where the sentiment and bias result will be displayed.
    :param model: The model to use for analysis (default is 'llama3:latest').
    :param prompt_template: The prompt template to send to the model.
    :param stream: Boolean indicating if streaming mode should be enabled. Default is False.
    :return: The analysis result from Ollama or 'neutral'/'error'/'model_error' in case of issues.
    """
    if not prompt_template:
        prompt_template = (
            "Analyze the following text for sentiment (positive, negative, or neutral) and political bias "
            "(left-wing or right-wing): {text}"
        )

    logging.info(f"Starting sentiment and bias analysis for text: {text[:50]}...")

    # Fetch available models asynchronously
    available_models = await list_models()
    if available_models == "error":
        error_message = "Failed to retrieve model list."
        logging.error(error_message)
        await add_to_tts_queue(error_message)
        update_ui(root, label, error_message)
        return "error"

    if model not in available_models:
        error_message = f"Model '{model}' not found. Available models: {available_models}"
        logging.error(error_message)
        await add_to_tts_queue(error_message)
        update_ui(root, label, error_message)
        return "model_error"

    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt_template.format(text=text),
        "stream": stream
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP Error: {response.status}")
                result = (await response.json()).get('response', 'neutral').strip().lower()
                logging.info(f"Sentiment and bias analysis result: {result}")
                try:
                    await add_to_tts_queue(f"Sentiment and bias analysis result: {result}")
                except Exception as e:
                    logging.error(f"Error adding text to TTS queue: {e}")
                update_ui(root, label, f"Sentiment and bias analysis result: {result}")
                return result

    except aiohttp.ClientError as e:
        error_message = f"Error communicating with Ollama: {e}"
        logging.error(error_message)
        try:
            await add_to_tts_queue("Error communicating with Ollama.")
        except Exception as e:
            logging.error(f"Error adding error message to TTS queue: {e}")
        update_ui(root, label, error_message)
        return "error"

    except Exception as e:
        error_message = f"Unexpected error during sentiment and bias analysis: {e}"
        logging.error(error_message)
        try:
            await add_to_tts_queue(error_message)
        except Exception as e:
            logging.error(f"Error adding error message to TTS queue: {e}")
        update_ui(root, label, error_message)
        return "error"


def update_ui(root, label, text):
    """
    Ensures that the PyQt5 UI is updated with the sentiment and bias result.

    PyQt5 operates with event loops, so we need to ensure that UI updates occur
    within the main thread using QMetaObject.invokeMethod to safely update widgets
    outside the thread performing the sentiment analysis.

    :param root: The PyQt5 parent QWidget object.
    :param label: The QLabel widget where the result will be displayed.
    :param text: The text to display in the QLabel.
    """
    QMetaObject.invokeMethod(label, "setText", Q_ARG(str, text))
