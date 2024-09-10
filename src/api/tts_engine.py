import pyttsx3
import queue
import logging
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

def process_tts_queue():
    """
    Continuously processes the text-to-speech (TTS) queue, converting text to speech.
    
    This function is run in a separate thread to avoid blocking the main application. It checks 
    for new TTS requests in the queue, and if found, processes them one by one by passing them 
    to the pyttsx3 engine. When 'None' is received, the thread will gracefully exit.
    """
    if not engine:
        logging.error("TTS engine is not initialized. Exiting TTS queue processing.")
        return
    
    while True:
        try:
            summary = tts_queue.get()  # Block and wait for a new TTS request
            if summary is None:
                logging.info("Received termination signal. Exiting TTS processing thread.")
                break  # Exit thread if None is received
            
            logging.info(f"Processing TTS request: {summary}")
            engine.say(summary)
            engine.runAndWait()
            tts_queue.task_done()
        except Exception as e:
            logging.error(f"Error processing TTS request: {e}")
            tts_queue.task_done()

def add_to_tts_queue(text):
    """
    Adds a text summary to the TTS queue for processing.

    Args:
        text (str): The text to be spoken by the TTS engine.
    
    Raises:
        ValueError: If the provided text is empty or None.
    """
    if not text:
        raise ValueError("TTS request text cannot be empty.")
    
    logging.info(f"Adding text to TTS queue: {text}")
    tts_queue.put(text)

def start_tts_thread():
    """
    Starts the TTS processing thread in the background to handle queued TTS requests.

    This function utilizes the `run_in_thread` utility to start the thread safely and 
    ensure the TTS processing is handled asynchronously.
    """
    logging.info("Starting TTS processing thread.")
    run_in_thread(process_tts_queue)

def stop_tts_thread():
    """
    Stops the TTS processing thread gracefully by sending a termination signal.
    
    This ensures that the TTS engine completes any ongoing requests before stopping.
    """
    logging.info("Stopping TTS processing thread.")
    tts_queue.put(None)  # Sending a termination signal to the thread

# Start the TTS processing thread when the module is loaded
start_tts_thread()

def shutdown_tts():
    """
    Shuts down the TTS engine and stops the TTS thread when the application exits.
    """
    logging.info("Shutting down TTS engine.")
    stop_tts_thread()
