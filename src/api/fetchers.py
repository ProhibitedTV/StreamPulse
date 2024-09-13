"""
api/fetchers.py

This module contains utility functions and classes for fetching data related to RSS feeds,
stock prices, and images. It uses retry logic for network requests, handles API interactions
with Alpha Vantage and Yahoo Finance, and fetches and processes images for the application.

Classes:
    FetchRSSFeeds - Asynchronous class to fetch RSS feed entries.
    FetchStockData - Asynchronous class to fetch stock prices and emit progress.
    
Functions:
    fetch_rss_feed - Fetches and parses an RSS feed with retry logic.
    fetch_stock_price - Fetches stock prices using Alpha Vantage or Yahoo Finance.
    fetch_from_yahoo_finance - Fetches stock price from Yahoo Finance as a fallback.
    fetch_image - Fetches and resizes an image from a URL, returns a QPixmap object.
    load_default_image - Loads a default image if the fetching fails.
    sanitize_html - Sanitizes HTML content to remove unsafe elements.
"""

import os
import io
import logging
import requests
import feedparser
import yfinance as yf
from PIL import Image
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt
import bleach

# Constants
RSS_FETCH_TIMEOUT = 15  # Timeout in seconds for fetching RSS feeds
DEFAULT_IMAGE_PATH = "../../images/default.png"  # Default fallback image path
STOCKS = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "META",
    "TSLA", "NFLX", "NVDA", "AMD", "INTC",
    "JPM", "BAC", "WFC", "GS", "C",
    "XOM", "CVX", "BP", "COP", "OXY",
    "PFE", "JNJ", "MRNA", "BMY", "LLY"
]

# Load environment variables from a .env file for stock fetching
load_dotenv()
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Global flag to track if Alpha Vantage has failed
alpha_vantage_failed = False

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Classes for Asynchronous Fetching
class FetchRSSFeeds(QThread):
    """
    Fetches RSS feeds asynchronously and emits progress updates.
    
    Attributes:
        feed_urls (list): List of RSS feed URLs to fetch.
        progress_signal (pyqtSignal): Signal to update progress in the main application.
    """
    progress_signal = pyqtSignal(int, str)

    def __init__(self, feed_urls):
        super().__init__()
        self.feed_urls = feed_urls

    def run(self):
        """
        Fetch RSS feed entries in a background thread and emit progress signals.
        """
        feed_entries = []
        total_feeds = len(self.feed_urls)

        for i, feed_url in enumerate(self.feed_urls):
            result = fetch_rss_feed(feed_url)
            if result:
                feed_entries.extend(result.entries[:3])  # Limit to 3 stories per feed
            progress = ((i + 1) / total_feeds) * 50  # Update progress (feeds are 50% of total)
            self.progress_signal.emit(int(progress), f"Loaded feed {i + 1} of {total_feeds}")

        self.progress_signal.emit(50, "Finished loading feeds")  # 50% done


class FetchStockData(QThread):
    """
    Fetches stock data asynchronously and emits progress updates.
    
    Attributes:
        progress_signal (pyqtSignal): Signal to update progress in the main application.
        stock_data_signal (pyqtSignal): Signal to pass the formatted stock data string.
    """
    progress_signal = pyqtSignal(int, str)
    stock_data_signal = pyqtSignal(str)

    def run(self):
        """
        Fetch stock prices in a background thread and emit progress signals.
        """
        stock_prices = []
        total_stocks = len(STOCKS)

        for index, symbol in enumerate(STOCKS):
            price = fetch_stock_price(symbol)
            stock_prices.append(f"{symbol}: ${price}")
            progress = 50 + ((index + 1) / total_stocks) * 50  # Stocks account for the remaining 50%
            self.progress_signal.emit(int(progress), f"Fetching stock price for {symbol}")

        stock_text = "  |  ".join(stock_prices)  # Format stock prices into a single string
        self.stock_data_signal.emit(stock_text)  # Emit the formatted stock data
        self.progress_signal.emit(100, "Finished loading stocks")  # 100% done


# Functions for Fetching Data
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def fetch_rss_feed(feed_url):
    """
    Fetches RSS feed content from the provided URL with retry logic.
    
    Args:
        feed_url (str): The RSS feed URL to fetch.

    Returns:
        feedparser.FeedParserDict: Parsed RSS feed data, or None if an error occurs.
    """
    try:
        response = requests.get(feed_url, timeout=RSS_FETCH_TIMEOUT)
        response.raise_for_status()
        logging.info(f"Fetched RSS feed from {feed_url}")
        return feedparser.parse(response.content)
    except requests.RequestException as e:
        logging.error(f"Error fetching feed from {feed_url}: {e}")
        return None


@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def fetch_stock_price(symbol):
    """
    Fetches real-time stock data from Alpha Vantage or Yahoo Finance if Alpha Vantage fails.

    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT).

    Returns:
        str: Stock price if successful, otherwise "N/A".
    """
    global alpha_vantage_failed

    if alpha_vantage_failed or not API_KEY:
        return fetch_from_yahoo_finance(symbol)

    alpha_vantage_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(alpha_vantage_url, timeout=RSS_FETCH_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            price = data["Global Quote"]["05. price"]
            logging.info(f"Fetched price for {symbol} from Alpha Vantage: {price}")
            return price
        else:
            logging.warning(f"No price data for {symbol}. Full response: {data}")
            alpha_vantage_failed = True
            return fetch_from_yahoo_finance(symbol)
    
    except requests.RequestException as e:
        logging.error(f"Error fetching stock data from Alpha Vantage for {symbol}: {e}")
        alpha_vantage_failed = True
        return fetch_from_yahoo_finance(symbol)


def fetch_from_yahoo_finance(symbol: str) -> str:
    """
    Fetches the latest stock price from Yahoo Finance using yfinance.

    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT).

    Returns:
        str: Stock price as a formatted string if successful, otherwise "N/A".
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        
        if hist.empty:
            logging.warning(f"No data returned for {symbol}. It may be an invalid symbol or the market is closed.")
            return "N/A"

        price = hist['Close'].iloc[-1]
        formatted_price = f"{price:.2f}"
        logging.info(f"Fetched price for {symbol} from Yahoo Finance: {formatted_price}")
        return formatted_price

    except Exception as e:
        logging.error(f"Unexpected error fetching stock data from Yahoo Finance for {symbol}: {e}")
    
    return "N/A"


def fetch_image(url, width, height):
    """
    Fetches and resizes an image from the provided URL, returns a QPixmap object.
    Falls back to a default image if fetching fails.

    Args:
        url (str): The image URL.
        width (int): Desired width of the image.
        height (int): Desired height of the image.

    Returns:
        QPixmap: PyQt-compatible image or None if fetching/loading fails.
    """
    try:
        response = requests.get(url, timeout=RSS_FETCH_TIMEOUT)
        response.raise_for_status()
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        image = image.resize((width, height), Image.LANCZOS)
        image.save("temp_image.png")  # Temporarily save the image to load into QPixmap
        pixmap = QPixmap("temp_image.png")
        os.remove("temp_image.png")  # Remove the temporary file
        return pixmap
    except requests.RequestException as e:
        logging.warning(f"Error fetching image from {url}: {e}. Falling back to default image.")
        return load_default_image(width, height)


def load_default_image(width, height):
    """
    Loads the default image if fetching the image fails.

    Args:
        width (int): Desired width of the image.
        height (int): Desired height of the image.

    Returns:
        QPixmap: PyQt-compatible image, or None if loading the default image fails.
    """
    try:
        image = Image.open(DEFAULT_IMAGE_PATH)
        image = image.resize((width, height), Image.LANCZOS)
        image.save("temp_image.png")
        pixmap = QPixmap("temp_image.png")
        os.remove("temp_image.png")
        return pixmap
    except Exception as e:
        logging.error(f"Error loading default image: {e}")
        return None


def sanitize_html(html_content):
    """
    Sanitizes HTML content to remove unsafe elements while keeping certain allowed tags.

    Args:
        html_content (str): Raw HTML content.

    Returns:
        str: Sanitized content with allowed tags.
    """
    allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'p', 'ul', 'li', 'ol', 'br']
    return bleach.clean(html_content, tags=allowed_tags, strip=True)
