"""
fetchers.py

This module provides asynchronous utilities for fetching and processing data such as RSS feeds, stock prices, and images.
It incorporates robust handling of network errors, malformed feeds, and various content types through the use of modern 
libraries like `aiohttp`, `feedparser`, `yfinance`, and `Pillow` for image manipulation. The module also supports
image caching, HTML sanitization, and feed fallbacks with minimal HTML scraping for non-standard content.

Key Features:
- Asynchronous RSS/Atom feed fetching and parsing using `feedparser`, with fallback to basic HTML scraping if needed.
- Implements retry logic for network errors and transient failures using the `tenacity` library.
- Stock price retrieval from Alpha Vantage with fallback to Yahoo Finance (`yfinance`) in case of API failure.
- Image fetching, resizing, and caching, with fallback to default images in case of failure.
- HTML content sanitization using `bleach` to ensure safe display of fetched data.
- Caching for images to improve performance and avoid repeated network requests.
- RSS feed URLs are loaded from a configurable JSON file, with logging for detailed error handling and debugging.

Functions:
- `fetch_rss_feed`: Fetches RSS or Atom feeds asynchronously, with retry logic and graceful error handling.
- `attempt_html_scraping`: A fallback function for minimal HTML scraping of links and titles from non-standard feeds.
- `cache_image_path`: Generates a hashed file path for caching images.
- `fetch_image`: Fetches and resizes images asynchronously, supporting caching and file size limits.
- `load_default_image`: Loads a default image in case the fetch fails.
- `sanitize_html`: Sanitizes HTML content to allow safe display of specific tags.
- `fetch_stock_price`: Asynchronously fetches stock prices from Alpha Vantage or Yahoo Finance, with retry logic.
- `fetch_from_yahoo_finance`: Fetches stock prices directly from Yahoo Finance using the `yfinance` library.
- `load_feeds_from_file`: Loads RSS feed URLs from a JSON file.
- `initialize_feeds`: Initializes RSS feeds asynchronously by fetching their content and ensuring data validity.

Exception Handling:
- Custom exceptions like `FeedError`, `ParsingError`, and `NetworkError` for improved error clarity.
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
from bs4 import BeautifulSoup
import bleach
import json
import certifi
import hashlib

# Constants
RSS_FETCH_TIMEOUT = 15  # 15 seconds timeout for RSS fetching
DEFAULT_IMAGE_PATH = "../../images/default.png"  # Default fallback image path
CACHE_DIR = "../../cache/images"  # Directory for caching images
STOCKS = [
    # Technology
    "AAPL", "GOOGL", "MSFT", "AMZN", "META", "TSLA", "NFLX", "NVDA", "AMD", "INTC",
    "ORCL", "CSCO", "IBM", "ADBE", "CRM",
    
    # Financials
    "JPM", "BAC", "WFC", "GS", "C", "MS", "AXP", "SCHW", "V", "MA",
    
    # Energy
    "XOM", "CVX", "BP", "COP", "OXY", "SLB", "TOT", "RDS.A", "EOG",
    
    # Healthcare
    "PFE", "JNJ", "MRNA", "BMY", "LLY", "GILD", "UNH", "CVS", "ABT", "AMGN",
    
    # Consumer Goods
    "PG", "KO", "PEP", "MCD", "WMT", "TGT", "HD", "NKE", "COST",
    
    # Industrials
    "BA", "CAT", "GE", "UPS", "FDX", "LMT",
    
    # Communication Services
    "DIS", "VZ", "T", "CMCSA", "TMUS",
    
    # Utilities
    "DUK", "SO", "NEE",
    
    # Real Estate
    "PLD", "AMT"
]

# Load environment variables
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Global flag to track if Alpha Vantage has failed
alpha_vantage_failed = False

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Create SSL context using certifi certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

class FeedError(Exception):
    pass

class ParsingError(FeedError):
    pass

class NetworkError(FeedError):
    pass

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
async def fetch_rss_feed(feed_url):
    """
    Asynchronously fetches an RSS or Atom feed, handling SSL certificates and content types.
    Uses `feedparser` for parsing and handles malformed feeds gracefully.
    Attempts basic HTML scraping for non-XML content types.
    Retries up to 3 times on network errors, with enhanced handling for DNS failures.
    """
    try:
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(feed_url, timeout=RSS_FETCH_TIMEOUT) as response:
                # Handle HTTP status codes
                if response.status == 404:
                    logging.error(f"Feed not found (404) for URL: {feed_url}")
                    return {'entries': []}  # Skip and return empty

                elif 300 <= response.status < 400:
                    logging.warning(f"Redirection ({response.status}) for URL: {feed_url}.")
                    return {'entries': []}  # Log and skip redirections

                elif 400 <= response.status < 500:
                    logging.error(f"Client error ({response.status}) for URL: {feed_url}. Skipping this feed.")
                    return {'entries': []}  # Skip and return empty

                elif 500 <= response.status < 600:
                    logging.error(f"Server error ({response.status}) for URL: {feed_url}. Skipping this feed.")
                    return {'entries': []}  # Skip and return empty

                content_type = response.headers.get("Content-Type", "").lower()

                valid_content_types = [
                    "application/rss+xml", "application/xml", "text/xml",
                    "application/atom+xml", "application/json", "text/html"
                ]

                if any(valid_type in content_type for valid_type in valid_content_types):
                    content = await response.text()
                    feed = feedparser.parse(content)

                    if feed.bozo:
                        logging.warning(f"Bozo error in feed for {feed_url}, trying relaxed parsing.")
                        if feed.bozo_exception:
                            logging.error(f"Bozo exception: {feed.bozo_exception}")
                        return attempt_html_scraping(content, feed_url)

                    if 'entries' not in feed or not feed['entries'] or len(feed['entries']) == 0:
                        logging.warning(f"No entries in feed: {feed_url}, attempting fallback.")
                        return attempt_html_scraping(content, feed_url)

                    return feed

                else:
                    logging.warning(f"Unexpected content type {content_type} for feed {feed_url}.")
                    content = await response.text()
                    return attempt_html_scraping(content, feed_url)

    except aiohttp.ClientConnectorError as e:
        logging.error(f"DNS/Network error fetching feed from {feed_url}: {e}")
        return {'entries': []}  # Log DNS errors and skip
    except aiohttp.ClientError as e:
        logging.error(f"Network error fetching feed from {feed_url}: {e}")
        raise NetworkError(f"Failed to fetch feed from {feed_url}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching feed from {feed_url}: {e}")
        return attempt_html_scraping(await response.text(), feed_url)

def attempt_html_scraping(content, feed_url):
    """
    Fallback method to extract basic links or titles from HTML if the feed is non-standard.
    Uses BeautifulSoup to parse the HTML and extract article titles and links.
    """
    logging.info(f"Attempting HTML fallback scraping for {feed_url}")
    try:
        soup = BeautifulSoup(content, 'html.parser')
        feed = {'entries': []}
        for item in soup.find_all('a', href=True):
            entry = {
                'title': item.get_text(strip=True),
                'link': item['href']
            }
            if entry['title'] and entry['link']:
                feed['entries'].append(entry)
        return feed
    except Exception as e:
        logging.error(f"Failed HTML scraping for {feed_url}: {e}")
        return {'entries': []}

def cache_image_path(url):
    """
    Generates a hashed file path for caching images based on their URL.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    file_name = hashlib.md5(url.encode()).hexdigest() + ".png"
    return os.path.join(CACHE_DIR, file_name)

async def fetch_image(url, width, height, max_file_size=5 * 1024 * 1024):
    """
    Asynchronously fetches and resizes an image from the provided URL, with caching for repeated requests.
    Returns a QPixmap object.
    """
    cached_path = cache_image_path(url)
    
    # Return cached image if it exists
    if os.path.exists(cached_path):
        logging.info(f"Loading cached image for URL: {url}")
        return QPixmap(cached_path)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=RSS_FETCH_TIMEOUT) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                if not content_type.startswith("image/"):
                    raise ValueError(f"Invalid content type {content_type} for image URL {url}")

                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > max_file_size:
                    raise ValueError(f"Image too large (>{max_file_size} bytes) for URL {url}")
                
                image_data = await response.read()

                image = Image.open(io.BytesIO(image_data))
                image.verify()
                image = Image.open(io.BytesIO(image_data))  # Reload after verification

                image = image.resize((width, height), Image.LANCZOS)

                if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                    background = Image.new("RGB", (width, height), (255, 255, 255))
                    background.paste(image, mask=image.convert('RGBA').split()[3])
                    image = background

                # Cache the image
                image.save(cached_path, format="PNG")

                pixmap = QPixmap(cached_path)
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

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5), reraise=True)
async def fetch_stock_price(symbol):
    """
    Asynchronously fetches real-time stock data from Alpha Vantage or Yahoo Finance as a fallback.
    Retries the fetch up to 5 times in case of network issues.
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
        logging.error(f"Network error fetching stock data from Alpha Vantage for {symbol}: {e}")
        alpha_vantage_failed = True
        return fetch_from_yahoo_finance(symbol)

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
    Ensures the returned data is in the expected format using `feedparser`.
    Returns a dictionary of categories with valid feed entries for each.
    """
    file_path = os.path.join(os.path.dirname(__file__), '../ui/rss_feeds.json')
    try:
        with open(file_path, 'r') as file:
            feed_data = json.load(file)
    except Exception as e:
        logging.error(f"Error loading feeds from {file_path}: {e}")
        return {}

    logging.info(f"Loaded categories and feed URLs from file.")
    
    feeds_data = {}

    # Iterate over categories and their URLs
    for category, urls in feed_data.items():
        feeds_data[category] = []
        for url in urls:
            try:
                logging.info(f"Fetching feed from URL: {url}")
                feed_content = await fetch_rss_feed(url)
                
                if feed_content and 'entries' in feed_content and len(feed_content['entries']) > 0:
                    feeds_data[category].append({
                        'url': url,
                        'feed': feed_content
                    })
                else:
                    logging.warning(f"Invalid or empty feed for {url}")

            except FeedError as e:
                logging.error(f"Feed error for {url}: {e}")
                feeds_data[category].append({'url': url, 'feed': {'entries': []}})
            except Exception as e:
                logging.error(f"Unexpected error fetching feed from {url}: {e}")
                feeds_data[category].append({'url': url, 'feed': {'entries': []}})

    return feeds_data
