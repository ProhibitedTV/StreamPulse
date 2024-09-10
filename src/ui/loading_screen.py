import os
import logging
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QWidget, QMainWindow, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QColor
from ui.feeds import load_feeds
from api.fetchers import fetch_stock_price, STOCKS

logging.basicConfig(level=logging.INFO)

class LoadingScreen(QMainWindow):
    progress_signal = pyqtSignal(float, str)

    def __init__(self, on_complete):
        super().__init__()
        self.on_complete = on_complete
        self.setWindowTitle("Loading Data...")
        self.showFullScreen()

        # Set gradient background
        self.setStyleSheet("""
            background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #34495e, stop: 1 #2c3e50);
        """)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Loading icon (spinner)
        self.loading_spinner = QLabel(self)
        self.loading_spinner.setAlignment(Qt.AlignCenter)
        spinner_pixmap = QPixmap(os.path.join('images', 'spinner.png'))  # Placeholder for spinner image
        self.loading_spinner.setPixmap(spinner_pixmap)
        layout.addWidget(self.loading_spinner)

        # Animate spinner (rotation)
        self.spinner_animation = QPropertyAnimation(self.loading_spinner, b"rotation")
        self.spinner_animation.setDuration(2000)
        self.spinner_animation.setStartValue(0)
        self.spinner_animation.setEndValue(360)
        self.spinner_animation.setLoopCount(-1)
        self.spinner_animation.start()

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

        # Animated progress bar
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

        self.progress_signal.connect(self.update_progress)
        self.worker = DataLoadingWorker(self.progress_signal)

        self.start_loading_data()

    def update_progress(self, progress, message=""):
        capped_progress = min(progress, 100)
        logging.info(f"Progress: {capped_progress}% - Message: {message}")
        self.progress_bar.setValue(capped_progress)
        self.status_label.setText(message)

        if capped_progress == 100:
            logging.info("Data loading complete, closing loading screen.")
            self.worker.quit()
            self.worker.wait()  # Ensure the worker has stopped
            self.fade_out_and_close()  # Smoothly transition out of the loading screen

    def start_loading_data(self):
        logging.info("Starting data loading process.")
        self.worker.start()

    def fade_out_and_close(self):
        """Smooth fade-out animation before closing the loading screen."""
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(1000)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.finished.connect(self.close_loading_screen)
        self.fade_out_animation.start()

    def close_loading_screen(self):
        self.close()  # Close the loading screen
        self.on_complete()  # Load the main application window

    def closeEvent(self, event):
        logging.info("Closing loading screen and stopping worker.")
        if self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        event.accept()


class DataLoadingWorker(QThread):
    def __init__(self, progress_signal):
        super().__init__()
        self.progress_signal = progress_signal

    def run(self):
        try:
            self.load_data_and_close()
        except Exception as e:
            logging.error(f"Error during data loading: {e}")

    def load_stock_data(self):
        total_stocks = len(STOCKS)
        for index, symbol in enumerate(STOCKS):
            try:
                fetch_stock_price(symbol)
                progress = (index + 1) / total_stocks * 50
                logging.info(f"Stock loading progress: {50 + progress}% for {symbol}")
                self.progress_signal.emit(50 + progress, f"Fetching stock price for {symbol}...")
            except Exception as e:
                logging.error(f"Error fetching stock data for {symbol}: {e}")
                self.progress_signal.emit(50 + (index + 1) / total_stocks * 50, f"Failed to fetch stock data for {symbol}...")

    def load_data_and_close(self):
        self.progress_signal.emit(0, "Loading news feeds...")

        def feed_progress_update(current_feed_index, total_feeds):
            progress = min(((current_feed_index + 1) / total_feeds) * 50, 50)
            logging.info(f"Feed loading progress: {progress}% (Feed {current_feed_index + 1}/{total_feeds})")
            self.progress_signal.emit(progress, f"Loading feeds... {int(progress)}%")

        load_feeds(None, lambda current_feed_index: feed_progress_update(current_feed_index, total_feeds=50))
        self.load_stock_data()
        self.progress_signal.emit(100, "Loading complete")
