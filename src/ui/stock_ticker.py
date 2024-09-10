import logging
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
from api.fetchers import fetch_stock_price, STOCKS
from utils.threading import run_in_thread

class StockTicker(QWidget):
    """
    StockTicker widget for displaying scrolling stock prices.
    """
    def __init__(self, parent=None):
        super(StockTicker, self).__init__(parent)

        # Create a label to display the stock ticker text
        self.stock_label = QLabel(self)
        self.stock_label.setStyleSheet("font-size: 14px; font-family: Helvetica; color: white;")
        self.stock_label.setAlignment(Qt.AlignLeft)

        # Set up layout
        layout = QHBoxLayout(self)
        layout.addWidget(self.stock_label)

        # Initialize the ticker text and start scrolling
        self.initialize_ticker()

    def initialize_ticker(self):
        """
        Initializes the ticker by fetching stock data and starting the scrolling.
        """
        # Update the ticker text initially
        self.update_ticker_text()

        # Schedule periodic updates for stock prices every 60 seconds
        QTimer.singleShot(60000, self.update_ticker_text)

        # Start the scrolling process
        self.scroll_ticker()

    def update_ticker_text(self):
        """
        Fetch stock prices in a background thread and update the ticker text.
        """
        def update():
            ticker_text = self.get_ticker_text()
            self.stock_label.setText(ticker_text)
            logging.info("Stock ticker text updated.")

        # Run the update in a separate thread to avoid blocking the UI
        run_in_thread(update)

    def get_ticker_text(self):
        """
        Fetch stock prices and format them into ticker text.

        Returns:
            str: Formatted stock symbols and prices.
        """
        ticker_text = ""
        for symbol in STOCKS:
            try:
                price = fetch_stock_price(symbol)
                ticker_text += f"{symbol}: ${price}  |  "
            except Exception as e:
                ticker_text += f"{symbol}: Error fetching price  |  "
                logging.error(f"Error fetching stock data for {symbol}: {e}")
        return ticker_text

    def scroll_ticker(self):
        """
        Scrolls the stock ticker from right to left by updating the label text.
        """
        if self.stock_label is None or self.stock_label.parent() is None:
            return  # QLabel or its parent has been deleted, stop further scrolling

        current_text = self.stock_label.text()
        if len(current_text) > 1:  # Ensure text isn't too short for scrolling
            self.stock_label.setText(current_text[1:] + current_text[0])  # Scroll text

        # Set the timer to call scroll_ticker again after 50ms
        QTimer.singleShot(50, self.scroll_ticker)


def create_stock_ticker_widget():
    """
    Creates the stock ticker widget.

    Returns:
        QWidget: The stock ticker widget frame.
    """
    stock_ticker_frame = QWidget()
    stock_ticker_frame.setStyleSheet("background-color: #17a2b8; padding: 10px;")

    # Create the StockTicker widget and add it to the stock ticker frame
    stock_ticker = StockTicker(stock_ticker_frame)
    
    # Set up the layout
    layout = QVBoxLayout(stock_ticker_frame)
    layout.addWidget(stock_ticker)

    return stock_ticker_frame
