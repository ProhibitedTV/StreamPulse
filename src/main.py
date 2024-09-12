"""
main.py

This is the entry point for the StreamPulse application. It initializes the application, 
displays a loading screen while RSS feeds and stock data are fetched asynchronously, 
and sets up the main application window once the data has been loaded successfully. 
It also manages the cleanup of background threads upon closing the application.

Classes:
    StreamPulseApp - Manages the overall application logic, including loading data, 
                     starting the main window, and handling background threads.
                     
Functions:
    main - Initializes and starts the PyQt application.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from ui.loading_screen import LoadingScreen  # Import the LoadingScreen class
from ui.gui import setup_main_frame
from utils.threading import shutdown_executor, run_with_callback  # Use the new threading module

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
        super().__init__()
        self.setWindowTitle("StreamPulse - Dynamic News Display")
        self.showFullScreen()

        # Initialize a flag to track if threads are running
        self.threads_running = True

        # Placeholder for loaded data
        self.feeds_data = None
        self.stock_data = None

        # Call loading screen logic
        self.load_with_loading_screen()

        # Set close event handling
        self.closeEvent = self.on_close

    def start_application(self, future=None):
        """
        Initialize the main application window once the news feeds and stock data 
        have finished loading. This function sets up the main frame of the application.

        Args:
            future: The future object returned from the background loading task.
        """
        logging.info("News feeds loaded, starting the main application.")
        try:
            # Pass the loaded feeds_data and stock_data to the main frame setup
            setup_main_frame(self, self.feeds_data, self.stock_data)
            self.showFullScreen()  # Ensure the main window is in full-screen mode after the setup
            self.repaint()  # Force repaint after loading
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
            self.loading_screen = LoadingScreen(self.start_application)
            self.loading_screen.show()

            # Use the run_with_callback to handle background loading and trigger start_application after completion
            run_with_callback(self.loading_screen.start_loading_data, self.on_data_loaded)

        except Exception as e:
            logging.error(f"Error occurred during loading process: {e}", exc_info=True)
            QMessageBox.critical(self, "Loading Error", "An error occurred while loading data. Please restart the application.")

    def on_data_loaded(self, future):
        """
        Callback after data has loaded. It checks the validity of the loaded data 
        and proceeds with starting the main application.

        Args:
            future: The future object containing the loaded data.
        """
        logging.info("Data loading complete, processing data.")
        try:
            # Extract data from the future result, and check if it's valid
            result = future.result()
            if result is None or not isinstance(result, dict):
                raise ValueError("No data was loaded or invalid data format.")
            
            self.feeds_data = result.get("rss_feeds", None)
            self.stock_data = result.get("stock_data", None)

            # Ensure both data sources are loaded
            if self.feeds_data is None or self.stock_data is None:
                logging.error("Failed to load feeds or stock data.")
                QMessageBox.critical(self, "Data Error", "Failed to load feeds or stock data. Please check the configuration.")
                return

            # Start the main application
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
        reply = QMessageBox.question(self, 'Confirmation',
                                     'Are you sure you want to quit?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            logging.info("Closing application.")
            logging.info("Shutting down thread pool executor.")
            shutdown_executor()  # Ensure threads are stopped

            # Ensure all background threads are stopped before closing
            self.close_all_threads()

            event.accept()
        else:
            event.ignore()

    def close_all_threads(self):
        """
        Gracefully close all background threads, including the loading screen worker.
        """
        logging.info("Waiting for all threads to complete...")

        if self.threads_running:
            if hasattr(self, 'loading_screen'):
                logging.info("Closing the loading screen if still open.")
                self.loading_screen.close()

        # Flag that all threads have completed
        self.threads_running = False
        logging.info("All threads have completed.")


# Main entry point for the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StreamPulseApp()

    # Execute the PyQt application event loop
    logging.info("Starting PyQt main loop.")
    try:
        exit_code = app.exec_()
    except Exception as e:
        logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
    finally:
        logging.info(f"Application exited with code {exit_code}")
        sys.exit(exit_code)
