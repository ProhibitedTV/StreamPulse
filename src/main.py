import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui.loading_screen import LoadingScreen  # Import the LoadingScreen class
from ui.gui import setup_main_frame
from utils.threading import run_with_callback, shutdown_executor

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting StreamPulse application...")

class StreamPulseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StreamPulse - Dynamic News Display")
        self.showFullScreen()

        # Call loading screen logic
        self.load_with_loading_screen()

        # Set close event handling
        self.closeEvent = self.on_close

    def start_application(self):
        """
        Initialize the main application window once the news feeds have finished loading.
        This function sets up the main frame of the application.
        """
        logging.info("News feeds loaded, starting the main application.")
        setup_main_frame(self)  # Setup main UI components after loading is complete

    def load_with_loading_screen(self):
        """
        Display a loading screen while asynchronously fetching the news feeds.
        """
        logging.info("Displaying loading screen and starting feed loading process.")
        try:
            # Show loading screen and start loading feeds in the background
            self.loading_screen = LoadingScreen(self.start_application)
            self.loading_screen.show()
        except Exception as e:
            logging.error(f"Error occurred during loading process: {e}")

    def on_close(self, event):
        """Cleanup function to ensure proper shutdown of background threads."""
        logging.info("Closing application.")

        # Shut down the thread pool executor to stop background threads
        logging.info("Shutting down thread pool executor.")
        shutdown_executor()  # Ensure threads are stopped

        # Close the application
        event.accept()

# Main entry point for the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StreamPulseApp()

    # Execute the PyQt application event loop
    logging.info("Starting PyQt main loop.")
    sys.exit(app.exec_())
