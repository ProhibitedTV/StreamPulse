import tkinter as tk
from tkinter import ttk
from ui.feeds import load_feeds
from api.fetchers import fetch_stock_price, STOCKS  # Import stock fetching functions
import threading
import logging

logging.basicConfig(level=logging.INFO)

def show_loading_screen(root, on_complete):
    """
    Displays a full-screen loading screen with a progress bar and real-time status updates
    while news feeds and stock data are being loaded. Once loading is complete, the main
    application window is shown.
    
    Args:
        root (tk.Tk): The main application window.
        on_complete (function): Function to call once loading is complete.
    """
    # Create the loading screen as a separate window
    loading_screen = tk.Toplevel(root)
    loading_screen.attributes("-fullscreen", True)  # Set to full-screen
    loading_screen.title("Loading Data...")

    # Add a label to display the loading message
    loading_label = ttk.Label(loading_screen, text="Loading data, please wait...", font=("Helvetica", 20))
    loading_label.pack(pady=30)

    # Label to display real-time status updates
    status_label = ttk.Label(loading_screen, text="", font=("Helvetica", 16))
    status_label.pack(pady=10)

    # Create a progress bar to indicate the loading progress
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(loading_screen, variable=progress_var, maximum=100, length=600)
    progress_bar.pack(pady=30)

    def update_progress(progress, message=""):
        """
        Updates the progress bar and status message based on the loading progress.
        
        Args:
            progress (float): The current progress as a percentage (0 to 100).
            message (str): A status message to display.
        """
        if loading_screen.winfo_exists():  # Ensure loading screen still exists
            capped_progress = min(progress, 100)  # Cap progress at 100%
            logging.info(f"Progress: {progress}% - Message: {message}")
            root.after(0, lambda: progress_var.set(capped_progress))
            root.after(0, lambda: status_label.config(text=message))
            loading_screen.update_idletasks()

    def load_stock_data(update_progress):
        """
        Loads stock data and updates the progress bar during the process.
        
        Args:
            update_progress (function): Function to update the progress.
        """
        total_stocks = len(STOCKS)
        for index, symbol in enumerate(STOCKS):
            # Fetch stock price for the symbol
            fetch_stock_price(symbol)
            # Update progress and show real-time status for each stock symbol
            progress = (index + 1) / total_stocks * 50  # Stocks account for the remaining 50% of progress
            logging.info(f"Stock loading progress: {50 + progress}% for {symbol}")
            update_progress(50 + progress, f"Fetching stock price for {symbol}...")

    def load_data_and_close():
        """
        Loads the feeds and stock data, updates the progress bar during loading, 
        and closes the loading screen once all data is fully loaded.
        """
        # Load feeds (accounts for 50% of the progress)
        update_progress(0, "Loading news feeds...")
        
        def feed_progress_update(current_feed_index, total_feeds):
            """
            Update the progress based on the current feed being processed.
            
            Args:
                current_feed_index (int): Index of the current feed being processed.
                total_feeds (int): Total number of feeds to load.
            """
            progress = min(((current_feed_index + 1) / total_feeds) * 50, 50)  # Cap feed progress at 50%
            logging.info(f"Feed loading progress: {progress}% (Feed {current_feed_index + 1}/{total_feeds})")
            update_progress(progress, f"Loading feeds... {int(progress)}%")
        
        load_feeds(root, lambda current_feed_index: feed_progress_update(current_feed_index, total_feeds=50))

        # Load stock data (accounts for the remaining 50% of the progress)
        load_stock_data(lambda p, msg="": update_progress(p, msg))

        # Once done, close the loading screen and show the main window
        if loading_screen.winfo_exists():  # Ensure the loading screen still exists
            root.after(0, loading_screen.destroy)
            root.after(0, on_complete)

    # Start loading data in a separate thread to avoid blocking the UI
    threading.Thread(target=load_data_and_close, daemon=True).start()
