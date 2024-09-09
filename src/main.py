import os
import tkinter as tk
import ttkbootstrap as ttkb
from ui.loading_screen import show_loading_screen
from ui.gui import setup_main_frame
from utils.threading import run_in_thread

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
    setup_main_frame(root)
    root.deiconify()

def load_with_loading_screen():
    """
    Display a loading screen while asynchronously fetching the news feeds.

    This function hides the main application window and then shows a full-screen loading 
    screen. It also triggers the background process of loading news feeds, and once the 
    loading is complete, it transitions to the main application window.
    """
    # Hide the root window during the loading process
    root.withdraw()

    # Show loading screen and start loading feeds in the background
    show_loading_screen(root, start_application)

# Start the feed loading process in a background thread using run_in_thread
run_in_thread(load_with_loading_screen)

# Bind the 'Escape' key to exit full-screen mode
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

# Start the Tkinter main loop to keep the UI running
root.mainloop()
