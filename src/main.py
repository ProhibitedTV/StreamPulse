import os
import tkinter as tk
import logging
import ttkbootstrap as ttkb
from ui.loading_screen import show_loading_screen
from ui.gui import setup_main_frame
from utils.threading import run_with_callback, run_with_exception_handling

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting StreamPulse application...")

# GUI setup
root = ttkb.Window(themename="darkly")
root.title("StreamPulse - Dynamic News Display")
root.attributes("-fullscreen", True)

def start_application():
    """
    Initialize the main application window once the news feeds have finished loading.

    This function is called after the loading process is complete and:
    - Sets up the main frame of the application, where the news feeds and other
      components will be displayed.
    - Deiconifies (shows) the main window, which was hidden during the loading process.
    """
    logging.info("News feeds loaded, starting the main application.")
    setup_main_frame(root)
    root.deiconify()

def load_with_loading_screen():
    """
    Display a loading screen while asynchronously fetching the news feeds.

    This function hides the main application window and then shows a full-screen loading 
    screen. It also triggers the background process of loading news feeds, and once the 
    loading is complete, it transitions to the main application window.
    """
    logging.info("Displaying loading screen and starting feed loading process.")

    try:
        # Hide the root window during the loading process
        root.withdraw()

        # Show loading screen and start loading feeds in the background
        show_loading_screen(root, start_application)
    except Exception as e:
        logging.error(f"Error occurred during loading process: {e}")

def on_close():
    """Cleanup function to ensure proper shutdown of background threads."""
    logging.info("Closing application.")
    root.destroy()

# Handle proper exit on window close
root.protocol("WM_DELETE_WINDOW", on_close)

# Start the feed loading process in a background thread, and automatically
# call `start_application` after loading completes
logging.info("Starting the news feed loading in a background thread.")
run_with_callback(load_with_loading_screen, lambda _: start_application())

# Bind the 'Escape' key to exit full-screen mode
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
logging.info("Bound 'Escape' key to exit full-screen mode.")

# Bind 'Ctrl+Q' to close the application
root.bind("<Control-q>", lambda e: on_close())
logging.info("Bound 'Ctrl+Q' key to close the application.")

# Start the Tkinter main loop to keep the UI running
logging.info("Starting Tkinter main loop.")
root.mainloop()
