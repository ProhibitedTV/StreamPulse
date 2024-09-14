"""
ui/stock_ticker.py

This module defines the StockTicker widget, which displays scrolling stock prices.
It includes functionality to dynamically update and scroll the ticker text for real-time stock price display.
"""

import logging
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt, QEvent
from PyQt5.QtGui import QFontMetrics
from api.fetchers import fetch_stock_price, STOCKS  # Import fetchers and stock list

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
        self.stock_label.setStyleSheet("font-size: 18px; font-family: Helvetica; color: white;")
        self.stock_label.setAlignment(Qt.AlignLeft)

        # Set up the layout for the ticker to fill the width
        layout = QHBoxLayout(self)
        layout.addWidget(self.stock_label)
        layout.setContentsMargins(0, 0, 0, 0)

        # Initialize ticker text and scroll position
        self.ticker_text = ""
        self.scroll_position = 0

        # Timer for scrolling the ticker
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.scroll_ticker)
        self.scroll_timer.start(30)  # Control the scroll speed

        # Set to expand across full width
        self.setFixedHeight(40)
        self.setAutoFillBackground(True)

        # Fetch and update stock prices
        self.update_ticker_text()

    def update_ticker_text(self):
        """
        Fetches the stock prices from the fetchers module and updates the ticker text.
        """
        stock_data = {symbol: fetch_stock_price(symbol) for symbol in STOCKS}
        self.set_ticker_text(format_stock_data(stock_data))

    def set_ticker_text(self, stock_text):
        """
        Updates the ticker text with the latest stock prices.

        Args:
            stock_text (str): The updated stock prices to be displayed in the ticker.
        """
        self.ticker_text = stock_text + " " * 10  # Add some space between repetitions
        self.scroll_position = 0  # Reset scroll position
        self.update()  # Trigger a redraw to ensure changes are visible
        logging.info("Stock ticker text updated.")

    def scroll_ticker(self):
        """
        Scrolls the stock ticker text from right to left.
        This method continuously updates the displayed portion of the ticker.
        """
        if not self.ticker_text:
            return  # Skip scrolling if no ticker text is set

        font_metrics = QFontMetrics(self.stock_label.font())
        text_width = font_metrics.width(self.ticker_text)

        # If the text is smaller than the label width, append the text to fill it
        while text_width < self.width():
            self.ticker_text += " " + self.ticker_text
            text_width = font_metrics.width(self.ticker_text)

        # Scroll the text by incrementing the scroll position
        self.scroll_position += 1
        display_text = self.ticker_text[self.scroll_position:] + self.ticker_text[:self.scroll_position]
        self.stock_label.setText(display_text)  # Update the label with the new text

        # Reset the scroll position if it exceeds the length of the ticker text
        if self.scroll_position >= len(self.ticker_text):
            self.scroll_position = 0

    def resizeEvent(self, event):
        """
        Ensures the ticker stretches across the full width of the parent window.
        """
        self.stock_label.setFixedWidth(self.width())
        super(StockTicker, self).resizeEvent(event)


def format_stock_data(stock_data):
    """
    Formats the stock data for the ticker text.

    Args:
        stock_data (dict): Dictionary of stock symbols and their current prices.

    Returns:
        str: Formatted string for the ticker text.
    """
    return " | ".join([f"{symbol}: {price}" for symbol, price in stock_data.items()])


def create_stock_ticker_widget():
    """
    Creates a stock ticker widget with the necessary layout and styling.

    Returns:
        QWidget: The stock ticker widget frame.
    """
    stock_ticker_frame = QWidget()
    stock_ticker_frame.setStyleSheet("background-color: #17a2b8; padding: 0px; margin: 0px;")

    # Create the StockTicker widget and add it to the stock ticker frame
    stock_ticker = StockTicker(stock_ticker_frame)

    # Set up the layout
    layout = QHBoxLayout(stock_ticker_frame)
    layout.addWidget(stock_ticker)

    return stock_ticker_frame
