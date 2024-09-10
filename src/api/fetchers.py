import os
import io
import logging
from concurrent.futures import ThreadPoolExecutor

import requests
import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt
import bleach

from utils.threading import run_in_thread

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

def fetch_image(url, width, height):
    """
    Fetches and resizes an image from the provided URL, returns a Tkinter-compatible image object.
    Falls back to a default image if fetching fails.

    Args:
        url (str): The image URL.
        width (int): Desired width of the image.
        height (int): Desired height of the image.

    Returns:
        ImageTk.PhotoImage: Tkinter-compatible image or None if fetching/loading fails.
    """
    try:
        response = requests.get(url, timeout=RSS_FETCH_TIMEOUT)
        response.raise_for_status()
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        image = image.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(image)
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
        ImageTk.PhotoImage: Tkinter-compatible image, or None if loading the default image fails.
    """
    try:
        image = Image.open(DEFAULT_IMAGE_PATH)
        image = image.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(image)
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

def fetch_all_feeds(feed_urls):
    """
    Fetches multiple RSS feeds concurrently using ThreadPoolExecutor with retry logic.

    Args:
        feed_urls (list): A list of RSS feed URLs.

    Returns:
        list: A list of parsed feed entries (up to 3 per feed), or an empty list if no feeds are available.
    """
    feed_entries = []
    
    def fetch_feed(feed_url):
        return fetch_rss_feed(feed_url)

    # Use utils.threading.run_in_thread for each feed URL to avoid blocking
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_feed, url) for url in feed_urls]
        for future in futures:
            result = future.result()
            if result:
                feed_entries.extend(result.entries[:3])  # Limit to 3 stories per feed
    return feed_entries

def fetch_stock_price(symbol):
    """
    Fetches real-time stock data from Alpha Vantage or Yahoo Finance if Alpha Vantage fails.

    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT).

    Returns:
        str: Stock price if successful, otherwise "N/A".
    """
    global alpha_vantage_failed

    if alpha_vantage_failed:
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
        # Fetch the ticker data for the given symbol
        ticker = yf.Ticker(symbol)

        # Retrieve the most recent trading day's closing price
        hist = ticker.history(period="1d")
        
        if hist.empty:
            logging.warning(f"No data returned for {symbol}. It may be an invalid symbol or the market is closed.")
            return "N/A"

        # Extract the latest closing price
        price = hist['Close'].iloc[-1]
        formatted_price = f"{price:.2f}"
        
        logging.info(f"Fetched price for {symbol} from Yahoo Finance: {formatted_price}")
        return formatted_price

    except yf.YFRequestException as e:
        logging.error(f"Request error fetching stock data for {symbol}: {e}")
    except IndexError as e:
        logging.error(f"No closing price available for {symbol}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching stock data from Yahoo Finance for {symbol}: {e}")
    
    return "N/A"
