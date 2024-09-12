import logging
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QWidget, QMainWindow, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation
from ui.feeds import load_feeds
from api.fetchers import fetch_stock_price, STOCKS
from utils.threading import run_with_callback

logging.basicConfig(level=logging.INFO)

class LoadingScreen(QMainWindow):
    """
    A loading screen that appears while data (e.g., news feeds and stock prices) is being fetched.
    Displays a progress bar and status messages to the user, and smoothly transitions to the main
    application window once loading is complete.
    
    Attributes:
        progress_signal (pyqtSignal): Signal to update the progress bar and status label.
        on_complete (function): Callback function to execute when data loading is complete.
    """
    progress_signal = pyqtSignal(float, str)

    def __init__(self, on_complete):
        """
        Initializes the loading screen, sets up the layout, and starts the loading process.

        Args:
            on_complete (function): The function to call when loading is complete.
        """
        super().__init__()
        self.on_complete = on_complete
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

        # Start the loading process
        self.start_loading_data()

    def update_progress(self, progress, message=""):
        """
        Updates the progress bar and status label based on the current progress of data loading.

        Args:
            progress (float): The current progress (0-100%).
            message (str): A status message describing the current stage of the loading process.
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
        Initiates the data loading process for news feeds and stock prices.
        Calls the on_data_loaded callback once the data is fully loaded.
        """
        logging.info("Starting data loading process.")
        run_with_callback(self.load_data_and_complete, self.on_data_loaded)

    def load_data_and_complete(self):
        """
        Handles the loading of both news feeds and stock data. Emits progress signals as the data
        is fetched and updates the progress bar accordingly.
        """
        def feed_progress_update(current_feed_index, total_feeds):
            progress = min(((current_feed_index + 1) / total_feeds) * 50, 50)
            logging.info(f"Feed loading progress: {progress}% (Feed {current_feed_index + 1}/{total_feeds})")
            self.progress_signal.emit(progress, f"Loading feeds... {int(progress)}%")

        # Capture the feed data from load_feeds
        feeds_data = load_feeds(None, lambda current_feed_index: feed_progress_update(current_feed_index, total_feeds=50))
        if feeds_data is None:
            logging.error("Feeds data is None. Failed to load feeds.")
        else:
            logging.info(f"Feeds data loaded: {len(feeds_data)} categories.")

        stock_data = self.load_stock_data()

        # Return feeds_data and stock_data as a tuple
        return feeds_data, stock_data

    def load_stock_data(self):
        """
        Fetches stock price data and updates the progress bar. This process runs in parallel with 
        the feed loading, with progress updates emitted as each stock price is fetched.
        """
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

        # Signal that the loading is complete
        self.progress_signal.emit(100, "Loading complete")

    def on_data_loaded(self, future=None):
        """
        Callback to be invoked when the data loading is complete. Closes the loading screen
        and proceeds to the main application.

        Args:
            future (Future, optional): The Future object returned by the threading call.
        """
        logging.info("Worker thread finished, transitioning to main window.")
        self.close_loading_screen()

    def fade_out_and_close(self):
        """
        Smooth fade-out animation before closing the loading screen and proceeding to the main
        application window.
        """
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(1000)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.finished.connect(self.close_loading_screen)
        self.fade_out_animation.start()

    def close_loading_screen(self):
        """
        Closes the loading screen and invokes the callback to load the main window.
        """
        self.on_complete()
        self.close()

    def closeEvent(self, event):
        """
        Handles the window close event to ensure all background threads are properly stopped.

        Args:
            event (QCloseEvent): The close event.
        """
        logging.info("Closing loading screen.")
        event.accept()
