"""
api/sentiment.py

This module provides functions for performing sentiment and political bias analysis using a local Ollama instance,
with operations running asynchronously to avoid blocking the main PyQt5 interface. It allows dynamic model selection
based on the models available from the Ollama instance and updates the user interface (UI) with the analysis results.

Key Features:
    - Dynamically selects the analysis model from available options if a model is not provided or unavailable.
    - Integrates with the TTS engine to provide vocal feedback on the analysis results.
    - Updates the PyQt5 UI asynchronously to avoid blocking the main event loop.

Main Functions:
    - list_models: Asynchronously fetches the list of available models from Ollama, handling errors gracefully.
    - analyze_text: Sends the provided text to the Ollama instance for sentiment and bias analysis, updating the UI 
      with the result, and optionally adding the result to the TTS queue.
    - update_ui: Updates the PyQt5 UI with the sentiment and bias result using thread-safe methods.

Dependencies:
    - aiohttp: For handling asynchronous HTTP requests.
    - PyQt5: To update the graphical user interface.
    - TTS Engine: Integrated to handle text-to-speech feedback for the analysis results.

This module is used in conjunction with a graphical user interface (GUI) to display and vocalize sentiment analysis
of news stories or other text-based content in real-time.
"""

import asyncio
import aiohttp
import logging
import re
from PyQt5.QtCore import QMetaObject, Q_ARG
from api.tts_engine import add_to_tts_queue, tts_is_speaking

# Initialize logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set to track processed stories
processed_story_ids = set()

def clean_text_for_tts(text):
    """
    Cleans up text to make it sound more natural when spoken by the TTS engine.
    - Removes URLs.
    - Shortens or simplifies awkward phrases.

    :param text: The original text for analysis.
    :return: Cleaned text, more appropriate for TTS.
    """
    cleaned_text = re.sub(r'http\S+|www\S+', '', text)  # Remove URLs for better TTS output
    return cleaned_text.strip()

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

async def analyze_text(text, root, label, story_id, model=None, prompt_template=None, stream=False):
    """
    Asynchronously sends a request to the local Ollama instance for text analysis (sentiment and political bias)
    and updates the PyQt5 UI.

    :param text: The input text for analysis.
    :param root: The PyQt5 root QWidget instance, used to update the UI.
    :param label: The PyQt5 QLabel widget where the sentiment and bias result will be displayed.
    :param story_id: The unique identifier of the story.
    :param model: The model to use for analysis. If None, a model will be chosen from available models.
    :param prompt_template: The prompt template to send to the model.
    :param stream: Boolean indicating if streaming mode should be enabled. Default is False.
    :return: The analysis result from Ollama or 'neutral'/'error'/'model_error' in case of issues.
    """
    # Skip the analysis if the story was already processed
    if story_id in processed_story_ids:
        logging.info(f"Story '{story_id}' already processed, skipping.")
        return "already_processed"

    if not prompt_template:
        prompt_template = (
            "Analyze the following text for sentiment (positive, negative, or neutral) and political bias "
            "(left-wing or right-wing): {text}"
        )

    logging.info(f"Starting sentiment and bias analysis for story: {story_id}")

    # Clean the input text before sending it to Ollama for analysis
    cleaned_input = clean_text_for_tts(text)

    # Fetch available models asynchronously
    available_models = await list_models()
    if available_models == "error" or not available_models:
        error_message = "Failed to retrieve model list or no models available."
        logging.error(error_message)
        await add_to_tts_queue(error_message)
        update_ui(root, label, error_message)
        return "error"

    # If no model was provided or the provided model is not available, choose the first available one
    if not model or model not in available_models:
        logging.warning(f"Model '{model}' not found. Using the first available model: {available_models[0]}")
        model = available_models[0]

    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt_template.format(text=cleaned_input),
        "stream": stream
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP Error: {response.status}")
                
                result = (await response.json()).get('response', 'neutral').strip().lower()
                logging.info(f"Sentiment and bias analysis result: {result}")

                # Clean the result before passing to TTS for a more natural sounding speech
                cleaned_result = clean_text_for_tts(result)
                
                try:
                    # Only add to the TTS queue if the TTS engine is not already speaking
                    if not tts_is_speaking():
                        await add_to_tts_queue(f"Sentiment and bias analysis result: {cleaned_result}")
                        logging.info(f"Added sentiment result to TTS queue: {cleaned_result}")
                    else:
                        logging.info("TTS is currently speaking, will not add a new item to the queue yet.")
                except Exception as e:
                    logging.error(f"Error adding text to TTS queue: {e}")

                # Wait for TTS to finish speaking before updating the UI
                while tts_is_speaking():
                    await asyncio.sleep(0.5)  # Sleep briefly to check again

                # Update the UI with the result
                update_ui(root, label, f"Sentiment and bias analysis result: {result}")

                # Mark story as processed after TTS finishes
                processed_story_ids.add(story_id)
                logging.info(f"Story '{story_id}' marked as processed.")
                
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
