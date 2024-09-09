# tts_engine.py

import pyttsx3
import queue
import threading

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Initialize a queue for TTS requests
tts_queue = queue.Queue()

# TTS processing thread function
def process_tts_queue():
    """
    This thread function keeps checking the queue for new TTS requests and processes them one by one.
    """
    while True:
        summary = tts_queue.get()  # Wait for a new TTS request
        if summary is None:
            break  # Exit thread if None is received
        engine.say(summary)
        engine.runAndWait()
        tts_queue.task_done()

# Start the TTS processing thread
tts_thread = threading.Thread(target=process_tts_queue, daemon=True)
tts_thread.start()
