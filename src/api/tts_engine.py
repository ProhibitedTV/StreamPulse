"""
api/tts_engine.py

This module provides text-to-speech (TTS) functionality using the pyttsx3 library.
It manages a TTS queue to process and convert text to speech asynchronously, ensuring
that the TTS operations do not block the main PyQt5 application.

Functions:
    process_tts_queue - Continuously processes the TTS queue in a separate thread.
    add_to_tts_queue - Adds text to the TTS queue for conversion to speech.
    start_tts_thread - Starts the background thread for processing TTS requests.
    stop_tts_thread - Stops the TTS processing thread gracefully.
    tts_is_speaking - Returns True if the TTS engine is currently speaking, False otherwise.
    shutdown_tts - Shuts down the TTS engine and stops the TTS thread.
"""

import pyttsx3
import queue
import logging
import time
from utils.threading import run_in_thread

# Initialize logger
logging.basicConfig(level=logging.INFO)

# Initialize text-to-speech engine
try:
    engine = pyttsx3.init()
    logging.info("TTS engine initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize TTS engine: {e}")
    engine = None

# Initialize a queue for TTS requests
tts_queue = queue.Queue()

# Variable to track if the engine is actually speaking
tts_busy = False

def on_start(name):
    """
    Event handler triggered when the TTS engine starts speaking.
    """
    global tts_busy
    logging.info(f"Speech started for: {name}")
    tts_busy = True

def on_end(name, completed):
    """
    Event handler triggered when the TTS engine finishes speaking.
    """
    global tts_busy
    logging.info(f"Speech finished for: {name}")
    tts_busy = False

# Attach event listeners to the engine
if engine:
    engine.connect('started-utterance', on_start)
    engine.connect('finished-utterance', on_end)

def tts_is_speaking():
    """
    Returns True if the TTS engine is currently speaking, False otherwise.
    
    This function checks the tts_busy state to determine if speech is active.
    """
    logging.info(f"TTS engine busy state: {tts_busy}")
    return tts_busy

def process_tts_queue():
    """
    Continuously processes the TTS queue, converting text to speech using pyttsx3.
    
    Runs in a separate thread to avoid blocking the main application. The function retrieves
    text from the queue and passes it to the TTS engine. It exits gracefully when a 'None'
    signal is added to the queue. A timeout mechanism is added to prevent the engine from 
    getting stuck in a busy state for too long.
    """
    if not engine:
        logging.error("TTS engine is not initialized. Exiting TTS queue processing.")
        return
    
    while True:
        try:
            text = tts_queue.get()  # Block and wait for a new TTS request
            if text is None:
                logging.info("Received termination signal. Exiting TTS processing thread.")
                break  # Exit thread if None is received
            
            logging.info(f"Processing TTS request: {text}")
            engine.say(text)
            
            # Set a timeout for safety (e.g., 10 seconds)
            start_time = time.time()
            while tts_is_speaking():
                if time.time() - start_time > 10:  # Timeout after 10 seconds
                    logging.warning("TTS engine timeout reached. Forcing stop.")
                    engine.endLoop()  # Force stop the TTS engine
                    break
                time.sleep(0.5)  # Check every 0.5 seconds
            
            engine.runAndWait()  # Blocks until the current text is finished speaking
            tts_queue.task_done()
        except Exception as e:
            logging.error(f"Error processing TTS request: {e}")
            tts_queue.task_done()

async def add_to_tts_queue(text):
    """
    Asynchronously adds text to the TTS queue for processing by the TTS engine.

    Args:
        text (str): The text to be converted to speech.
    
    Raises:
        ValueError: If the provided text is empty or None.
    """
    if not text:
        raise ValueError("TTS request text cannot be empty.")
    
    logging.info(f"Adding text to TTS queue: {text}")
    try:
        tts_queue.put_nowait(text)  # Non-blocking queue addition
    except queue.Full:
        logging.error("TTS queue is full. Unable to add the request.")

def start_tts_thread():
    """
    Starts a background thread to continuously process the TTS queue.
    
    This ensures that text added to the queue is processed asynchronously without
    blocking the main PyQt5 application.
    """
    logging.info("Starting TTS processing thread.")
    run_in_thread(process_tts_queue)

def stop_tts_thread():
    """
    Stops the TTS processing thread gracefully by sending a termination signal (None).
    
    This ensures that any ongoing TTS requests are completed before stopping the thread.
    """
    logging.info("Stopping TTS processing thread.")
    tts_queue.put(None)  # Sending termination signal to the thread

# Automatically start the TTS processing thread when the module is loaded
start_tts_thread()

def shutdown_tts():
    """
    Shuts down the TTS engine and stops the TTS processing thread.
    
    This function should be called when the application is exiting to clean up resources.
    """
    logging.info("Shutting down TTS engine.")
    stop_tts_thread()
