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
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QThread
import asyncio
from api import fetchers

logging.basicConfig(level=logging.INFO)


class RSSFeedLoader(QThread):
    progress_signal = pyqtSignal(int, str)
    data_loaded_signal = pyqtSignal(dict)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        feeds_data = loop.run_until_complete(fetchers.initialize_feeds())  # Load structured data (category, URL, feed content)
        total_feeds = sum(len(feeds) for feeds in feeds_data.values())
        progress = 0

        for category, feeds in feeds_data.items():
            for feed_info in feeds:
                progress += 1
                feed_url = feed_info['url']
                message = f"Loaded feed {progress} of {total_feeds} from category: {category}"
                self.progress_signal.emit(int((progress / total_feeds) * 50), message)
        
        loop.close()

        self.data_loaded_signal.emit(feeds_data)


class StockDataLoader(QThread):
    progress_signal = pyqtSignal(int, str)
    stock_data_signal = pyqtSignal(dict)

    def run(self):
        stock_data = {}
        total_stocks = len(fetchers.STOCKS)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for i, symbol in enumerate(fetchers.STOCKS):
            try:
                price = loop.run_until_complete(fetchers.fetch_stock_price(symbol))
                stock_data[symbol] = price
            except Exception as e:
                logging.error(f"Error fetching stock price for {symbol}: {e}")
                stock_data[symbol] = "Error"

            progress = 50 + ((i + 1) / total_stocks) * 50
            self.progress_signal.emit(int(progress), f"Loaded stock price for {symbol}")

        loop.close()
        self.stock_data_signal.emit(stock_data)


class LoadingScreen(QMainWindow):
    progress_signal = pyqtSignal(float, str)

    def __init__(self, on_complete):
        super().__init__()
        self.on_complete = on_complete
        self.rss_feeds = None
        self.stock_data = None
        self.feeds_loader = None
        self.stock_loader = None
        self.loading_screen_closed = False  # Flag to track if the loading screen has already been closed
        self.setWindowTitle("Loading Data...")
        self.showFullScreen()

        self.setStyleSheet("""
            background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #34495e, stop: 1 #2c3e50);
        """)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.loading_label = QLabel("Loading data, please wait...", self)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            font-size: 24px;
            color: #ecf0f1;
            padding: 20px;
        """)
        layout.addWidget(self.loading_label)

        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 18px;
            color: #bdc3c7;
            padding-bottom: 20px;
        """)
        layout.addWidget(self.status_label)

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

        self.opacity_effect = QGraphicsOpacityEffect(self.central_widget)
        self.central_widget.setGraphicsEffect(self.opacity_effect)
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(1000)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.start()

        self.progress_signal.connect(self.update_progress)
        self.start_loading_data()

    def update_progress(self, progress, message=""):
        capped_progress = min(progress, 100)
        logging.info(f"Progress: {capped_progress}% - Message: {message}")
        self.progress_bar.setValue(capped_progress)
        self.status_label.setText(message)

    def start_loading_data(self):
        logging.info("Starting data loading process.")
        self.feeds_loader = RSSFeedLoader()
        self.feeds_loader.progress_signal.connect(self.update_progress)
        self.feeds_loader.data_loaded_signal.connect(self.on_feeds_loaded)
        self.feeds_loader.start()

        self.stock_loader = StockDataLoader()
        self.stock_loader.progress_signal.connect(self.update_progress)
        self.stock_loader.stock_data_signal.connect(self.on_stock_data_received)
        self.stock_loader.start()

    def on_feeds_loaded(self, feeds_data):
        self.rss_feeds = feeds_data
        self.check_if_complete()

    def on_stock_data_received(self, stock_data):
        self.stock_data = stock_data
        self.check_if_complete()

    def check_if_complete(self):
        if self.rss_feeds is not None and self.stock_data is not None:
            logging.info("All data loaded, proceeding to close the loading screen.")
            self.progress_signal.emit(100, "All data loaded")
            self.fade_out_and_close()

    def fade_out_and_close(self):
        if not self.loading_screen_closed:  # Check if the screen is already closed
            self.loading_screen_closed = True  # Set the flag to indicate the screen is closing
            self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_out_animation.setDuration(1000)
            self.fade_out_animation.setStartValue(1)
            self.fade_out_animation.setEndValue(0)
            self.fade_out_animation.finished.connect(self.close_loading_screen)
            self.fade_out_animation.start()

    def close_loading_screen(self):
        if self.loading_screen_closed:
            result = {"rss_feeds": self.rss_feeds, "stock_data": self.stock_data}
            self.on_complete(result)
            self.close()

    def closeEvent(self, event):
        logging.info("Closing loading screen.")
        if self.feeds_loader and self.feeds_loader.isRunning():
            self.feeds_loader.quit()
            self.feeds_loader.wait()
        if self.stock_loader and self.stock_loader.isRunning():
            self.stock_loader.quit()
            self.stock_loader.wait()
        event.accept()
