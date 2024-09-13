"""
api/fetchers.py

This module contains utility functions and classes for fetching data related to RSS feeds,
stock prices, and images. It uses retry logic for network requests, handles API interactions
with Alpha Vantage and Yahoo Finance, and fetches and processes images for the application.

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
from tenacity import retry, wait_exponential, stop_after_attempt
import bleach

# Constants
RSS_FETCH_TIMEOUT = 15  # 15 seconds timeout for RSS fetching
DEFAULT_IMAGE_PATH = "../../images/default.png"  # Default fallback image path
STOCKS = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "META", "TSLA", "NFLX", "NVDA", "AMD", "INTC",
    "JPM", "BAC", "WFC", "GS", "C", "XOM", "CVX", "BP", "COP", "OXY", "PFE", "JNJ", 
    "MRNA", "BMY", "LLY"
]

# Load environment variables
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Global flag to track if Alpha Vantage has failed
alpha_vantage_failed = False

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Functions for Fetching Data
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
def fetch_rss_feed(feed_url):
    """
    Fetches an RSS feed from a given URL with retry logic.
    
    Args:
        feed_url (str): The URL of the RSS feed.
    
    Returns:
        dict: The parsed RSS feed data or an error message if fetching fails.
    """
    try:
        response = requests.get(feed_url, timeout=RSS_FETCH_TIMEOUT)
        if response.headers.get("Content-Type") not in ["application/rss+xml", "application/xml", "text/xml"]:
            raise ValueError(f"Invalid content type {response.headers.get('Content-Type')} for feed {feed_url}")

        feed = feedparser.parse(response.content)
        if feed.bozo:
            raise ValueError(f"Malformed feed data for {feed_url}")

        return feed

    except Exception as e:
        logging.error(f"Error fetching feed from {feed_url}: {e}")
        return {"error": str(e)}

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5), reraise=True)
def fetch_stock_price(symbol):
    """
    Fetches real-time stock data from Alpha Vantage or Yahoo Finance as a fallback.

    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT).

    Returns:
        str or dict: Stock price if successful, otherwise a dictionary with an error message.
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
        str or dict: Stock price as a formatted string if successful, otherwise a dictionary with an error message.
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        
        if hist.empty:
            logging.warning(f"No data returned for {symbol}. It may be an invalid symbol or the market is closed.")
            return {"error": f"Invalid data for {symbol}. Market may be closed or symbol is incorrect"}

        price = hist['Close'].iloc[-1]
        formatted_price = f"{price:.2f}"
        logging.info(f"Fetched price for {symbol} from Yahoo Finance: {formatted_price}")
        return formatted_price

    except Exception as e:
        logging.error(f"Unexpected error fetching stock data from Yahoo Finance for {symbol}: {e}")
        return {"error": f"Failed to fetch stock data for {symbol}"}

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
