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
import json

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
    Fetches an RSS or Atom feed, handling different content types gracefully.

    Args:
        feed_url (str): The URL of the feed.

    Returns:
        dict: Parsed feed data or an error message if fetching fails.
    """
    try:
        response = requests.get(feed_url, timeout=RSS_FETCH_TIMEOUT)
        content_type = response.headers.get("Content-Type", "").lower()

        # Allowed content types for feeds
        valid_content_types = [
            "application/rss+xml", "application/xml", "text/xml",
            "application/atom+xml", "application/json", "text/html"
        ]

        # Parsing based on content type
        if "json" in content_type:
            return response.json().get('feeds', {})
        elif any(valid_type in content_type for valid_type in valid_content_types):
            feed = feedparser.parse(response.content)
            if feed.bozo:
                raise ValueError(f"Malformed feed data for {feed_url}")
            return feed
        else:
            logging.warning(f"Unexpected content type {content_type} for feed {feed_url}. Attempting to parse.")
            return feedparser.parse(response.content)

    except Exception as e:
        logging.error(f"Error fetching feed from {feed_url}: {e}")
        return {"error": str(e)}


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


@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
def fetch_image(url, width, height, max_file_size=5 * 1024 * 1024):
    """
    Fetches and resizes an image from the provided URL, returns a QPixmap object.
    Falls back to a default image if fetching fails. Includes validation of content
    type, file size, and handles transparency.

    Args:
        url (str): The image URL.
        width (int): Desired width of the image.
        height (int): Desired height of the image.
        max_file_size (int): Maximum allowed file size in bytes (default: 5MB).

    Returns:
        QPixmap: PyQt-compatible image or None if fetching/loading fails.
    """
    try:
        response = requests.get(url, timeout=RSS_FETCH_TIMEOUT, stream=True)
        response.raise_for_status()

        # Check content type is an image
        content_type = response.headers.get("Content-Type", "").lower()
        if not content_type.startswith("image/"):
            raise ValueError(f"Invalid content type {content_type} for image URL {url}")

        # Check the file size doesn't exceed the limit
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_file_size:
            raise ValueError(f"Image too large (>{max_file_size} bytes) for URL {url}")
        elif not content_length:
            # Fallback: check the size of image data
            image_data = io.BytesIO(response.content)
            if image_data.getbuffer().nbytes > max_file_size:
                raise ValueError(f"Image too large (>{max_file_size} bytes) for URL {url}")

        # Load and verify the image
        image_data = io.BytesIO(response.content)
        image = Image.open(image_data)
        image.verify()
        image = Image.open(image_data)  # Reload image after verification

        # Resize the image
        image = image.resize((width, height), Image.LANCZOS)

        # Handle transparency
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            background = Image.new("RGB", (width, height), (255, 255, 255))  # White background
            background.paste(image, mask=image.convert('RGBA').split()[3])  # Paste with transparency mask
            image = background

        # Load image directly into QPixmap without saving to disk
        pixmap = QPixmap()
        with io.BytesIO() as output_buffer:
            image.save(output_buffer, format="PNG")
            pixmap.loadFromData(output_buffer.getvalue())

        return pixmap

    except requests.RequestException as e:
        logging.warning(f"Network error fetching image from {url}: {e}. Falling back to default image.")
    except (Image.UnidentifiedImageError, ValueError) as e:
        logging.warning(f"Error processing image from {url}: {e}. Falling back to default image.")
    except Exception as e:
        logging.error(f"Unexpected error fetching image from {url}: {e}. Falling back to default image.")

    # Return default image if fetching or processing failed
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

        # Load the image directly into QPixmap without saving to disk
        pixmap = QPixmap()
        with io.BytesIO() as output_buffer:
            image.save(output_buffer, format="PNG")
            pixmap.loadFromData(output_buffer.getvalue())

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


# Function to load RSS feeds from a JSON file
def load_feeds_from_file():
    """
    Loads the RSS feed URLs from a JSON file located in the 'src/ui/' directory.

    Returns:
        list: A list of feed URLs or an empty list if loading fails.
    """
    file_path = os.path.join(os.path.dirname(__file__), '../ui/rss_feeds.json')  # File path is handled inside the function
    
    try:
        with open(file_path, 'r') as file:
            feeds = json.load(file).get('feeds', [])
            return feeds
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading feeds from {file_path}: {e}")
        return []


# Function to fetch all feeds once and return the data
def fetch_all_feeds(feed_urls):
    """
    Fetches and processes multiple RSS feeds.

    Args:
        feed_urls (list): List of feed URLs to fetch.

    Returns:
        dict: Dictionary containing feed data indexed by URL or errors if any occur.
    """
    feeds_data = {}
    for url in feed_urls:
        feed_data = fetch_rss_feed(url)
        if 'error' not in feed_data:
            feeds_data[url] = feed_data
        else:
            logging.error(f"Error fetching feed {url}: {feed_data['error']}")
    return feeds_data


# Initialization function to load and fetch feeds
def initialize_feeds():
    """
    Initializes the RSS feeds by loading them from the file and fetching their content.

    Returns:
        dict: Dictionary containing all feed data fetched from the URLs.
    """
    feed_urls = load_feeds_from_file()
    if not feed_urls:
        logging.error("No feeds loaded.")
        return {}
    
    return fetch_all_feeds(feed_urls)
