"""
main.py

This is the entry point for the StreamPulse application. It initializes the PyQt5
application and integrates it with the asyncio event loop using QEventLoop. The application 
displays a loading screen while fetching RSS feeds and stock data asynchronously, and 
then sets up the main window to display dynamic news and stock information.

Key Features:
- Displays a loading screen while fetching data in the background.
- Integrates PyQt5 with asyncio to handle asynchronous operations within the PyQt event loop.
- Dynamically loads RSS feed data and stock prices for the main application window.
- Handles application lifecycle, including clean-up of threads upon exit.

Classes:
- StreamPulseApp: Main class managing the loading screen, data fetching, and initializing the main application window.
"""

import sys
import logging
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from ui.loading_screen import LoadingScreen
from ui.gui import MainWindow
from utils.threading import shutdown_executor
from qasync import QEventLoop

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting StreamPulse application...")

class StreamPulseApp(QMainWindow):
    """
    StreamPulseApp is the main class that manages the loading screen, 
    fetching of data, and initializing the main application window.
    
    Attributes:
        feeds_data (dict): Loaded RSS feed data.
        stock_data (dict): Loaded stock price data.
        threads_running (bool): Tracks whether threads are active.
    """
    def __init__(self):
        """
        Initializes the StreamPulse application, displays the loading screen, 
        and begins data fetching processes.
        """
        super().__init__()
        self.setWindowTitle("StreamPulse - Dynamic News Display")
        self.threads_running = True  # Flag to track if threads are running

        # Placeholder for loaded data
        self.feeds_data = None
        self.stock_data = None

        # Initialize the loading screen
        self.load_with_loading_screen()

        # Set close event handling
        self.closeEvent = self.on_close

    def start_application(self):
        """
        Initialize the main application window once the news feeds and stock data 
        have finished loading. This function sets up the main window of the application.
        """
        logging.info("Starting the main application window.")
        try:
            # Create the main window and pass the loaded feeds_data and stock_data to it
            self.main_window = MainWindow(self.feeds_data or {}, self.stock_data or {})
            self.main_window.showFullScreen()  # Ensure the main window is in full-screen mode

            # Explicitly close the loading screen to avoid overlap
            if self.loading_screen:
                logging.info("Closing the loading screen.")
                self.loading_screen.close()

            self.repaint()  # Force repaint after loading
            self.update()  # Ensure the window is updated and displayed properly
        except Exception as e:
            logging.error(f"Error occurred while starting the main application: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", "Failed to start the application. Please try again.")

    def load_with_loading_screen(self):
        """
        Display a loading screen while asynchronously fetching the news feeds and stock data.
        """
        logging.info("Displaying loading screen and starting feed loading process.")
        try:
            # Show loading screen and start loading feeds in the background using threading.py
            self.loading_screen = LoadingScreen(self.on_data_loaded)
            self.loading_screen.showFullScreen()

        except Exception as e:
            logging.error(f"Error occurred during loading process: {e}", exc_info=True)
            QMessageBox.critical(self, "Loading Error", "An error occurred while loading data. Please restart the application.")

    def on_data_loaded(self, result):
        """
        Callback after data has loaded. It checks the validity of the loaded data 
        and proceeds with starting the main application.

        Args:
            result: The dictionary containing 'rss_feeds' and 'stock_data'.
        """
        logging.info("Data loading complete, processing data.")
        try:
            # Check if the result contains valid data
            if not result or not isinstance(result, dict):
                raise ValueError("No data was loaded or invalid data format.")

            # Use the data loaded from the loading screen
            self.feeds_data = result.get("rss_feeds", {})
            self.stock_data = result.get("stock_data", {})

            # Log warnings if data is missing
            if not self.feeds_data:
                logging.warning("Feeds data is missing, but continuing with the main window.")
            if not self.stock_data:
                logging.warning("Stock data is missing, but continuing with the main window.")

            # Start the main application window with the loaded data
            self.start_application()

        except Exception as e:
            logging.error(f"Error processing loaded data: {e}", exc_info=True)
            QMessageBox.critical(self, "Data Processing Error", "An error occurred while processing loaded data. Please restart the application.")

    def on_close(self, event):
        """
        Cleanup function to ensure proper shutdown of background threads and resources
        when the application is closed.

        Args:
            event: The close event triggered when the user attempts to close the application.
        """
        try:
            reply = QMessageBox.question(self, 'Confirmation',
                                         'Are you sure you want to quit?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                logging.info("Closing application.")
                shutdown_executor()  # Ensure threads are stopped

                # Ensure all background threads and windows are closed before closing the app
                self.close_all_threads()
                if hasattr(self, 'loading_screen'):
                    self.loading_screen.close()  # Ensure the loading screen is closed
                if hasattr(self, 'main_window'):
                    self.main_window.close()  # Close the main window if open

                event.accept()
            else:
                event.ignore()
        except Exception as e:
            logging.error(f"Error during application shutdown: {e}", exc_info=True)

    def close_all_threads(self):
        """
        Gracefully close all background threads, including the loading screen worker.
        """
        try:
            logging.info("Waiting for all threads to complete...")

            if self.threads_running:
                if hasattr(self, 'loading_screen') and self.loading_screen.isVisible():
                    logging.info("Closing the loading screen.")
                    self.loading_screen.close()

            # Flag that all threads have completed
            self.threads_running = False
            logging.info("All threads have completed.")
        except Exception as e:
            logging.error(f"Error closing threads: {e}", exc_info=True)


# Main entry point for the application
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Integrate asyncio event loop with PyQt's event loop using QEventLoop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = StreamPulseApp()

    # Execute the PyQt and asyncio event loops concurrently
    logging.info("Starting PyQt main loop with asyncio integration.")
    try:
        with loop:
            exit_code = loop.run_forever()
    except Exception as e:
        logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
    finally:
        logging.info(f"Application exited with code {exit_code}")
        sys.exit(exit_code)
