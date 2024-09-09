import requests
import feedparser
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import io
import logging
from tenacity import retry, wait_exponential, stop_after_attempt
import bleach
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from dotenv import load_dotenv
import os

# Constants
RSS_FETCH_TIMEOUT = 15  # Timeout in seconds for fetching RSS feeds
DEFAULT_IMAGE_PATH = "../../images/default.png"  # Default fallback image path

# Load environment variables from a .env file for stock fetching
load_dotenv()
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
STOCKS = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "META",
    "TSLA", "NFLX", "NVDA", "AMD", "INTC",
    "JPM", "BAC", "WFC", "GS", "C",
    "XOM", "CVX", "BP", "COP", "OXY",
    "PFE", "JNJ", "MRNA", "BMY", "LLY"
]

# Global flag to track if Alpha Vantage has failed
alpha_vantage_failed = False

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Fetching RSS feeds and images
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def fetch_rss_feed(feed_url):
    """
    Fetches RSS feed content from the provided URL using the `requests` library with a retry mechanism.
    
    :param feed_url: The RSS feed URL to fetch.
    :return: The parsed RSS feed data, or None if an error occurs.
    """
    try:
        response = requests.get(feed_url, timeout=RSS_FETCH_TIMEOUT)
        response.raise_for_status()  # Raises HTTPError for bad responses
        logging.info(f"Fetched RSS feed from {feed_url}")
        return feedparser.parse(response.content)
    except Exception as e:
        logging.error(f"Error fetching feed from {feed_url}: {e}")
        return None

def fetch_image(url, width, height):
    """
    Fetches an image from the provided URL, resizes it, and returns a Tkinter-compatible image object.
    Falls back to a default image if fetching fails.
    
    :param url: The image URL.
    :param width: The desired width of the image.
    :param height: The desired height of the image.
    :return: A Tkinter-compatible PhotoImage object or None if an error occurs.
    """
    try:
        response = requests.get(url, timeout=RSS_FETCH_TIMEOUT)
        response.raise_for_status()
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        image = image.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception as e:
        logging.warning(f"Error fetching image from {url}: {e}. Falling back to default image.")
        try:
            image = Image.open(DEFAULT_IMAGE_PATH)
            image = image.resize((width, height), Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            logging.error(f"Error loading default image: {e}")
            return None

def sanitize_html(html_content):
    """
    Sanitizes HTML content, removing unsafe elements while keeping allowed tags like bold, italic, etc.
    
    :param html_content: The raw HTML content.
    :return: The sanitized plain text content.
    """
    allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'p', 'ul', 'li', 'ol', 'br']
    return bleach.clean(html_content, tags=allowed_tags, strip=True)

def fetch_all_feeds(feed_urls):
    """
    Fetches multiple RSS feeds concurrently using ThreadPoolExecutor, with retry logic for each feed.
    
    :param feed_urls: A list of RSS feed URLs.
    :return: A list of parsed feed entries (up to 3 per feed), or an empty list if no feeds are available.
    """
    feed_entries = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_rss_feed, url) for url in feed_urls]
        for future in futures:
            result = future.result()
            if result:
                feed_entries.extend(result.entries[:3])  # Limit to 3 stories per feed
    return feed_entries

# Fetching stock data
def fetch_stock_price(symbol):
    """
    Fetches real-time stock data from Alpha Vantage or falls back to Yahoo Finance API.
    
    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT).
    
    Returns:
        str: Stock price if successful, otherwise "N/A".
    """
    global alpha_vantage_failed

    # If Alpha Vantage has already failed, skip and go straight to Yahoo Finance
    if alpha_vantage_failed:
        return fetch_from_yahoo_finance(symbol)

    alpha_vantage_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(alpha_vantage_url)
        data = response.json()
        
        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            return data["Global Quote"]["05. price"]
        else:
            logging.warning(f"No price data for {symbol}. Full response: {data}")
            alpha_vantage_failed = True  # Set failure flag
            return fetch_from_yahoo_finance(symbol)
    
    except Exception as e:
        logging.error(f"Error fetching stock data from Alpha Vantage for {symbol}: {e}")
        alpha_vantage_failed = True  # Set failure flag
        return fetch_from_yahoo_finance(symbol)

def fetch_from_yahoo_finance(symbol):
    """
    Fetches real-time stock data from Yahoo Finance as a fallback using yfinance.
    
    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT).
    
    Returns:
        str: Stock price if successful, otherwise "N/A".
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            logging.info(f"Fetched price for {symbol} from Yahoo Finance: {price}")
            return f"{price:.2f}"
        else:
            logging.warning(f"No historical data available for {symbol}")
            return "N/A"
    except Exception as e:
        logging.error(f"Error fetching stock data from Yahoo Finance for {symbol}: {e}")
        return "N/A"
