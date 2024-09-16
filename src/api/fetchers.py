"""
api/fetchers.py

This module provides asynchronous utilities for fetching data such as RSS feeds, stock prices, and images.
It uses modern libraries like `aiohttp` for async HTTP requests, `feedparser` for RSS/Atom feed parsing,
`yfinance` for retrieving stock prices, and `Pillow` for handling image manipulation. Additionally, it includes
error handling mechanisms like retries using `tenacity` to ensure robustness in the face of network failures.

Key Functions:
- fetch_rss_feed: Asynchronously fetches and parses RSS/Atom feeds, handling different content types gracefully.
- fetch_stock_price: Asynchronously retrieves real-time stock prices from Alpha Vantage, with a fallback to Yahoo Finance.
- fetch_image: Asynchronously downloads and resizes images from URLs, with error handling and a fallback to a default image.
- sanitize_html: Cleans HTML content, keeping only a safe set of tags for display purposes.
- initialize_feeds: Loads RSS feed URLs from a JSON file and fetches their content asynchronously.
- load_default_image: Loads a default image when image fetching fails.
"""

import os
import io
import logging
import ssl
import aiohttp
import feedparser
import yfinance as yf
from PIL import Image
from PyQt5.QtGui import QPixmap
from tenacity import retry, wait_exponential, stop_after_attempt
import bleach
import json
import certifi

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

# Create SSL context using certifi certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Async functions for fetching data
async def fetch_rss_feed(feed_url):
    """
    Asynchronously fetches an RSS or Atom feed, handling different content types gracefully.
    Ensures that SSL certificates are verified using the certifi package.
    """
    ssl_context = aiohttp.TCPConnector(ssl=None, ssl_context=aiohttp.helpers.ssl_create_default_context(cafile=certifi.where()))
    
    async with aiohttp.ClientSession(connector=ssl_context) as session:
        try:
            async with session.get(feed_url, timeout=RSS_FETCH_TIMEOUT) as response:
                content_type = response.headers.get("Content-Type", "").lower()

                # Allowed content types for feeds
                valid_content_types = [
                    "application/rss+xml", "application/xml", "text/xml",
                    "application/atom+xml", "application/json", "text/html"
                ]

                if "json" in content_type:
                    return await response.json().get('feeds', {})
                elif any(valid_type in content_type for valid_type in valid_content_types):
                    content = await response.text()
                    feed = feedparser.parse(content)
                    if feed.bozo:
                        raise ValueError(f"Malformed feed data for {feed_url}")
                    return feed
                else:
                    logging.warning(f"Unexpected content type {content_type} for feed {feed_url}. Attempting to parse.")
                    content = await response.text()
                    return feedparser.parse(content)

        except Exception as e:
            logging.error(f"Error fetching feed from {feed_url}: {e}")
            return {"error": str(e)}

def fetch_from_yahoo_finance(symbol: str) -> str:
    """
    Fetches the latest stock price from Yahoo Finance using yfinance.
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
async def fetch_stock_price(symbol):
    """
    Asynchronously fetches real-time stock data from Alpha Vantage or Yahoo Finance as a fallback.
    """
    global alpha_vantage_failed

    if alpha_vantage_failed or not API_KEY:
        return fetch_from_yahoo_finance(symbol)

    alpha_vantage_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(alpha_vantage_url, timeout=RSS_FETCH_TIMEOUT, ssl=ssl_context) as response:
                data = await response.json()
                if "Global Quote" in data and "05. price" in data["Global Quote"]:
                    price = data["Global Quote"]["05. price"]
                    logging.info(f"Fetched price for {symbol} from Alpha Vantage: {price}")
                    return price
                else:
                    logging.warning(f"No price data for {symbol}. Full response: {data}")
                    alpha_vantage_failed = True
                    return fetch_from_yahoo_finance(symbol)

    except aiohttp.ClientError as e:
        logging.error(f"Error fetching stock data from Alpha Vantage for {symbol}: {e}")
        alpha_vantage_failed = True
        return fetch_from_yahoo_finance(symbol)

async def fetch_image(url, width, height, max_file_size=5 * 1024 * 1024):
    """
    Asynchronously fetches and resizes an image from the provided URL, returns a QPixmap object.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=RSS_FETCH_TIMEOUT) as response:
                # Check content type is an image
                content_type = response.headers.get("Content-Type", "").lower()
                if not content_type.startswith("image/"):
                    raise ValueError(f"Invalid content type {content_type} for image URL {url}")

                # Check the file size doesn't exceed the limit
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > max_file_size:
                    raise ValueError(f"Image too large (>{max_file_size} bytes) for URL {url}")
                image_data = await response.read()

                # Load and verify the image
                image = Image.open(io.BytesIO(image_data))
                image.verify()
                image = Image.open(io.BytesIO(image_data))  # Reload image after verification

                # Resize the image
                image = image.resize((width, height), Image.LANCZOS)

                # Handle transparency
                if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                    background = Image.new("RGB", (width, height), (255, 255, 255))
                    background.paste(image, mask=image.convert('RGBA').split()[3])
                    image = background

                # Load image directly into QPixmap
                pixmap = QPixmap()
                with io.BytesIO() as output_buffer:
                    image.save(output_buffer, format="PNG")
                    pixmap.loadFromData(output_buffer.getvalue())

                return pixmap

    except Exception as e:
        logging.error(f"Error fetching image from {url}: {e}")
        return load_default_image(width, height)

def load_default_image(width, height):
    """
    Loads the default image if fetching the image fails.
    """
    try:
        image = Image.open(DEFAULT_IMAGE_PATH)
        image = image.resize((width, height), Image.LANCZOS)
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
    """
    allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'p', 'ul', 'li', 'ol', 'br']
    return bleach.clean(html_content, tags=allowed_tags, strip=True)

def load_feeds_from_file():
    """
    Loads the RSS feed URLs from a JSON file.
    """
    file_path = os.path.join(os.path.dirname(__file__), '../ui/rss_feeds.json')
    try:
        with open(file_path, 'r') as file:
            feed_data = json.load(file)
            feeds = [url for category in feed_data.values() for url in category]
            return feeds
    except Exception as e:
        logging.error(f"Error loading feeds from {file_path}: {e}")
        return []

async def initialize_feeds():
    """
    Asynchronously initializes the RSS feeds by loading them from the file and fetching their content.
    """
    feed_urls = load_feeds_from_file()
    
    if not feed_urls:
        logging.error("No feeds loaded. The rss_feeds.json file may be empty or incorrectly formatted.")
        return {}

    logging.info(f"Loaded {len(feed_urls)} feed URLs from file.")
    feeds_data = {}

    for url in feed_urls:
        try:
            logging.info(f"Fetching feed from URL: {url}")
            feed_data = await fetch_rss_feed(url)
            if 'error' in feed_data:
                logging.error(f"Failed to fetch feed from {url}. Error: {feed_data['error']}")
            else:
                feeds_data[url] = feed_data
        except Exception as e:
            logging.error(f"Error fetching feed from {url}: {e}")

    return feeds_data
