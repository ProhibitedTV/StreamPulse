import logging
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt


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

        # Set a fixed height and let the width auto-adjust
        self.stock_label.setFixedHeight(30)

        # Set up layout
        layout = QHBoxLayout(self)
        layout.addWidget(self.stock_label)

        # Initialize ticker text and start scrolling
        self.ticker_text = ""
        self.scroll_position = 0

        # Set up a timer to scroll the ticker text
        self.scroll_ticker()  # Start scrolling

    def set_ticker_text(self, stock_text):
        """
        Set the ticker text with the latest stock prices.
        """
        self.ticker_text = stock_text
        self.scroll_position = 0  # Reset scroll position when ticker text updates
        self.stock_label.setText(self.ticker_text[:self.stock_label.width() // 8])  # Initially set text based on width
        logging.info("Stock ticker text updated.")

    def scroll_ticker(self):
        """
        Scrolls the stock ticker text from right to left.
        """
        if not self.ticker_text:
            return  # If no ticker text is available, skip scrolling

        # Scroll the text by incrementing the scroll position
        self.scroll_position += 1
        display_text = self.ticker_text[self.scroll_position:] + " " + self.ticker_text[:self.scroll_position]
        self.stock_label.setText(display_text)  # Display full scrolling text

        # Reset scroll position if it exceeds the length of the ticker text
        if self.scroll_position >= len(self.ticker_text):
            self.scroll_position = 0

        # Set the timer to call scroll_ticker again after 50ms for faster scrolling
        QTimer.singleShot(50, self.scroll_ticker)


def create_stock_ticker_widget():
    """
    Creates the stock ticker widget.

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
