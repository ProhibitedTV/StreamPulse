import os
import tkinter as tk
import ttkbootstrap as ttkb
from ui.loading_screen import show_loading_screen
from ui.gui import setup_main_frame
import threading

# GUI setup
root = ttkb.Window(themename="darkly")
root.title("StreamPulse - Dynamic News Display")
root.attributes("-fullscreen", True)

# Function to start the main application after feeds are loaded
def start_application():
    # Setup the main frame (this is where the feeds will be displayed)
    setup_main_frame(root)
    # Show the main window once the feeds are fully loaded
    root.deiconify()

# Function to load feeds with a loading screen
def load_with_loading_screen():
    # Hide the root window initially
    root.withdraw()

    # Show the loading screen and load feeds in the background
    show_loading_screen(root, start_application)

# Start the feed loading process
load_with_loading_screen()

# Press 'Esc' to exit full screen
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

# Start the Tkinter main loop
root.mainloop()
