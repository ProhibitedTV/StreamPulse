"""
ui/stock_ticker.py

This module defines the StockTicker widget, which displays scrolling stock prices.
It includes functionality to dynamically update and scroll the ticker text for real-time stock price display.
"""

import logging
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class StockTicker(QWidget):
    """
    A PyQt5 widget for displaying a horizontally scrolling stock ticker.

    Attributes:
        stock_label (QLabel): A label to display the scrolling stock prices.
        ticker_text (str): The current stock price data as a string.
        scroll_position (int): Tracks the current scroll position for the ticker.
    """
    def __init__(self, parent=None):
        super(StockTicker, self).__init__(parent)

        # Initialize the label for displaying the stock ticker
        self.stock_label = QLabel(self)
        self.stock_label.setStyleSheet("font-size: 14px; font-family: Helvetica; color: white;")
        self.stock_label.setAlignment(Qt.AlignLeft)

        # Set a fixed height for the ticker
        self.stock_label.setFixedHeight(30)

        # Set up the layout for the ticker
        layout = QHBoxLayout(self)
        layout.addWidget(self.stock_label)

        # Initialize ticker text and scroll position
        self.ticker_text = ""
        self.scroll_position = 0

        # Start the ticker scrolling
        self.scroll_ticker()

    def set_ticker_text(self, stock_text):
        """
        Updates the ticker text with the latest stock prices.

        Args:
            stock_text (str): The updated stock prices to be displayed in the ticker.
        """
        self.ticker_text = stock_text
        self.scroll_position = 0  # Reset scroll position
        self.stock_label.setText(self.ticker_text[:self.stock_label.width() // 8])  # Adjust initial view
        logging.info("Stock ticker text updated.")

    def scroll_ticker(self):
        """
        Scrolls the stock ticker text from right to left.
        This method continuously updates the displayed portion of the ticker.
        """
        if not self.ticker_text:
            return  # Skip scrolling if no ticker text is set

        # Scroll the text by incrementing the scroll position
        self.scroll_position += 1
        display_text = self.ticker_text[self.scroll_position:] + " " + self.ticker_text[:self.scroll_position]
        self.stock_label.setText(display_text)  # Update the label with the new text

        # Reset the scroll position if it exceeds the length of the ticker text
        if self.scroll_position >= len(self.ticker_text):
            self.scroll_position = 0

        # Set the timer to scroll the ticker again after 50ms
        QTimer.singleShot(50, self.scroll_ticker)


def create_stock_ticker_widget():
    """
    Creates a stock ticker widget with the necessary layout and styling.

    Returns:
        QWidget: The stock ticker widget frame.
    """
    stock_ticker_frame = QWidget()
    stock_ticker_frame.setStyleSheet("background-color: #17a2b8; padding: 20px; margin: 0px;")

    # Create the StockTicker widget and add it to the stock ticker frame
    stock_ticker = StockTicker(stock_ticker_frame)

    # Set up the layout
    layout = QVBoxLayout(stock_ticker_frame)
    layout.addWidget(stock_ticker)

    return stock_ticker_frame
