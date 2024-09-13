"""
ui/loading_screen.py

This module defines the LoadingScreen class, which is responsible for displaying a loading screen while
the application fetches necessary data, such as RSS feeds and stock prices. It handles asynchronous
data loading and communicates progress updates to the user interface using PyQt5.

Key Features:
- Displays a loading screen with progress feedback.
- Loads RSS feeds and stock data asynchronously.
- Provides smooth visual transitions using opacity effects.
- Uses signals to communicate data loading progress.

Classes:
    LoadingScreen - Manages the display and behavior of the loading screen during data loading.
"""

import logging
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QWidget, QMainWindow, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation
from ui.feeds import load_feeds, load_feed_config  # Use feeds.py's functions
from api.fetchers import FetchStockData  # Use the class for fetching stock data
from utils.threading import run_with_callback

logging.basicConfig(level=logging.INFO)


class LoadingScreen(QMainWindow):
    """
    LoadingScreen displays a loading screen while the application fetches necessary
    RSS feeds and stock data. It handles asynchronous loading of data and communicates
    progress back to the user interface.
    """
    progress_signal = pyqtSignal(float, str)

    def __init__(self, on_complete):
        super().__init__()
        self.on_complete = on_complete
        self.feeds_data = None
        self.stock_data = None
        self.stock_data_thread = None  # Store the stock data thread
        self.setWindowTitle("Loading Data...")
        self.showFullScreen()

        # Set gradient background
        self.setStyleSheet("""
            background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #34495e, stop: 1 #2c3e50);
        """)

        # Initialize UI components
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Loading label
        self.loading_label = QLabel("Loading data, please wait...", self)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            font-size: 24px;
            color: #ecf0f1;
            padding: 20px;
        """)
        layout.addWidget(self.loading_label)

        # Status label
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 18px;
            color: #bdc3c7;
            padding-bottom: 20px;
        """)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 10px;
                text-align: center;
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 20px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Opacity effect for smooth visual transitions
        self.opacity_effect = QGraphicsOpacityEffect(self.central_widget)
        self.central_widget.setGraphicsEffect(self.opacity_effect)
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(1000)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.start()

        # Connect progress signals to update the UI
        self.progress_signal.connect(self.update_progress)

        # Start the loading process
        self.start_loading_data()

    def update_progress(self, progress, message=""):
        """
        Updates the progress bar and status message during the loading process.
        Args:
            progress (float): The percentage of completion (0-100).
            message (str): The status message to display.
        """
        capped_progress = min(progress, 100)
        logging.info(f"Progress: {capped_progress}% - Message: {message}")
        self.progress_bar.setValue(capped_progress)
        self.status_label.setText(message)

        if capped_progress == 100:
            logging.info("Data loading complete, closing loading screen.")
            self.fade_out_and_close()

    def start_loading_data(self):
        """
        Initiates the loading of data by running the load_data_and_complete function in a background thread.
        """
        logging.info("Starting data loading process.")
        run_with_callback(self.load_data_and_complete, self.on_data_loaded)

    def load_data_and_complete(self):
        """
        Loads RSS feeds and stock data, emits progress signals, and checks the completion of the loading process.
        Returns:
            dict: A dictionary containing 'rss_feeds' and 'stock_data' or None if loading fails.
        """
        rss_feeds = load_feed_config()
        if not rss_feeds:
            logging.error("Failed to load RSS feeds.")
            return None

        # Start feed loading and stock data fetching asynchronously
        results = {"rss_feeds": None, "stock_data": None}
        feed_loaded = [False]
        stock_loaded = [False]

        # Define the update functions
        def feed_progress_update(progress, message=""):
            """
            Updates the progress bar with the current progress percentage and message.
            Args:
                progress (float): The current progress percentage (0 to 100).
                message (str): The message to display alongside the progress.
            """
            self.progress_signal.emit(progress, message)

        def on_feeds_loaded():
            loaded_data = load_feeds(rss_feeds, feed_progress_update)  # Call load_feeds from feeds.py
            if loaded_data:
                results["rss_feeds"] = loaded_data
            else:
                results["rss_feeds"] = {"error": "No valid RSS feeds loaded."}
            feed_loaded[0] = True
            self.check_if_complete(results, feed_loaded, stock_loaded)

        # Load feeds
        on_feeds_loaded()

        # Load stock data
        self.stock_data_thread = FetchStockData()

        def on_stock_data_received(stock_text):
            """
            Callback function to handle stock data once fetched.
            """
            if stock_text:
                results["stock_data"] = stock_text
            else:
                results["stock_data"] = "No valid stock data available."
            stock_loaded[0] = True
            self.check_if_complete(results, feed_loaded, stock_loaded)

        self.stock_data_thread.stock_data_signal.connect(on_stock_data_received)

        self.stock_data_thread.start()

        return None  # Return None as this is asynchronous

    def check_if_complete(self, results, feed_loaded, stock_loaded):
        """
        Checks if both RSS feeds and stock data have finished loading and returns the results.
        Args:
            results (dict): The dictionary holding the loaded data.
            feed_loaded (list): List indicating if the RSS feed loading is complete.
            stock_loaded (list): List indicating if the stock data loading is complete.
        """
        if feed_loaded[0] and stock_loaded[0]:
            if not results["rss_feeds"]:
                logging.warning("No valid RSS feeds loaded.")
                results["rss_feeds"] = {"error": "No valid RSS feeds loaded."}

            if not results["stock_data"]:
                logging.warning("No valid stock data loaded.")
                results["stock_data"] = "Stock data not available."

            self.progress_signal.emit(100, "Loading complete")
            self.feeds_data = results["rss_feeds"]
            self.stock_data = results["stock_data"]

    def on_data_loaded(self, future=None):
        """
        Callback triggered when data has finished loading. Transitions to the main application window.

        Args:
            future: The future object returned by the background task.
        """
        logging.info("Worker thread finished, transitioning to main window.")
        try:
            if future:
                data = future.result()
            else:
                data = {"rss_feeds": self.feeds_data, "stock_data": self.stock_data}

            if not data["rss_feeds"]:
                logging.warning("Feeds data is None, continuing with placeholders.")
                data["rss_feeds"] = {"error": "No valid RSS feeds loaded."}

            if not data["stock_data"]:
                logging.warning("Stock data is None, continuing with placeholders.")
                data["stock_data"] = {"error": "No valid stock data loaded."}

            logging.debug(f"Loaded data: {data}")
            # Pass data to main app
            self.feeds_data = data["rss_feeds"]
            self.stock_data = data["stock_data"]
            self.close_loading_screen()

        except Exception as e:
            logging.error(f"Error processing loaded data: {e}", exc_info=True)

    def fade_out_and_close(self):
        """
        Fades out the loading screen and closes it.
        """
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(1000)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.finished.connect(self.close_loading_screen)
        self.fade_out_animation.start()

    def close_loading_screen(self):
        """
        Closes the loading screen and proceeds to the main application.
        """
        if self.stock_data_thread and self.stock_data_thread.isRunning():
            self.stock_data_thread.quit()  # Gracefully stop the thread if it's still running
            self.stock_data_thread.wait()  # Wait for the thread to finish

        result = {
            "rss_feeds": self.feeds_data,
            "stock_data": self.stock_data
        }
        self.on_complete(result)
        self.close()

    def closeEvent(self, event):
        """
        Handles the close event of the loading screen window.

        Args:
            event: The close event.
        """
        logging.info("Closing loading screen.")
        if self.stock_data_thread and self.stock_data_thread.isRunning():
            self.stock_data_thread.quit()  # Gracefully stop the thread
            self.stock_data_thread.wait()  # Wait for it to finish
        event.accept()