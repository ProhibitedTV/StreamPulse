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
"""

import logging
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QWidget, QMainWindow, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QThread, QTimer
import asyncio
from api.fetchers import initialize_feeds, fetch_stock_price, STOCKS

logging.basicConfig(level=logging.INFO)


class RSSFeedLoader(QThread):
    """
    QThread class to load RSS feeds asynchronously using asyncio.
    """
    progress_signal = pyqtSignal(int, str)  # Signal to emit progress updates
    data_loaded_signal = pyqtSignal(dict)  # Signal emitted when all feeds are loaded

    def run(self):
        """
        Runs the asynchronous feed loading process.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        rss_feeds = loop.run_until_complete(initialize_feeds())
        loop.close()

        self.data_loaded_signal.emit(rss_feeds)


class StockDataLoader(QThread):
    """
    QThread class to load stock data asynchronously using asyncio.
    """
    progress_signal = pyqtSignal(int, str)  # Signal to emit progress updates
    stock_data_signal = pyqtSignal(dict)  # Signal emitted when stock data is loaded

    def run(self):
        stock_data = {}
        total_stocks = len(STOCKS)

        # Use the full list of stock symbols from fetchers.py
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for i, symbol in enumerate(STOCKS):
            try:
                price = loop.run_until_complete(fetch_stock_price(symbol))
                stock_data[symbol] = price
            except Exception as e:
                logging.error(f"Error fetching stock price for {symbol}: {e}")
                stock_data[symbol] = "Error"

            progress = 50 + ((i + 1) / total_stocks) * 50
            self.progress_signal.emit(int(progress), f"Loaded stock price for {symbol}")

        loop.close()
        self.stock_data_signal.emit(stock_data)


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
        self.rss_feeds = None
        self.stock_data = None
        self.feeds_loader = None
        self.stock_loader = None
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

    def start_loading_data(self):
        """
        Initiates the loading of data by running the load_data_and_complete function in a background thread.
        """
        logging.info("Starting data loading process.")
        
        # Start the RSS feeds loader thread
        self.feeds_loader = RSSFeedLoader()
        self.feeds_loader.progress_signal.connect(self.update_progress)
        self.feeds_loader.data_loaded_signal.connect(self.on_feeds_loaded)
        self.feeds_loader.start()

        # Start the stock data loader thread
        self.stock_loader = StockDataLoader()
        self.stock_loader.progress_signal.connect(self.update_progress)
        self.stock_loader.stock_data_signal.connect(self.on_stock_data_received)
        self.stock_loader.start()

    def on_feeds_loaded(self, feeds_data):
        """
        Callback function when RSS feeds are loaded.
        """
        self.rss_feeds = feeds_data
        self.check_if_complete()

    def on_stock_data_received(self, stock_data):
        """
        Callback function when stock data is loaded.
        """
        self.stock_data = stock_data
        self.check_if_complete()

    def check_if_complete(self):
        """
        Checks if both RSS feeds and stock data have been loaded before proceeding.
        """
        if self.rss_feeds is not None and self.stock_data is not None:
            logging.info("All data loaded, proceeding to close the loading screen.")
            self.progress_signal.emit(100, "All data loaded")
            self.fade_out_and_close()

    def fade_out_and_close(self):
        """
        Fades out the loading screen and closes it after ensuring all data is loaded.
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
        result = {
            "rss_feeds": self.rss_feeds,
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
        if self.feeds_loader and self.feeds_loader.isRunning():
            self.feeds_loader.quit()
            self.feeds_loader.wait()
        if self.stock_loader and self.stock_loader.isRunning():
            self.stock_loader.quit()
            self.stock_loader.wait()
        event.accept()
