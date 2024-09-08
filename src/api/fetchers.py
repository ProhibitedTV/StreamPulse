import requests
import feedparser
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import io
import logging
from tenacity import retry, wait_exponential, stop_after_attempt
import bleach
from concurrent.futures import ThreadPoolExecutor

RSS_FETCH_TIMEOUT = 15
DEFAULT_IMAGE_PATH = "path/to/default/image.png"

logging.basicConfig(level=logging.INFO)

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def fetch_rss_feed(feed_url):
    """
    Fetches RSS feed content from the provided URL using the `requests` library with a retry mechanism.
    """
    try:
        response = requests.get(feed_url, timeout=RSS_FETCH_TIMEOUT)
        response.raise_for_status()
        logging.info(f"Fetched RSS feed from {feed_url}")
        return feedparser.parse(response.content)
    except Exception as e:
        logging.error(f"Error fetching feed from {feed_url}: {e}")
        return None

def fetch_image(url, width, height):
    """
    Fetches an image from a URL, resizes it, and returns it, with a fallback to a default image if it fails.
    """
    try:
        response = requests.get(url, timeout=RSS_FETCH_TIMEOUT)
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        image = image.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception:
        try:
            image = Image.open(DEFAULT_IMAGE_PATH)
            image = image.resize((width, height), Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            logging.error(f"Error loading default image: {e}")
            return None

def sanitize_html(html_content):
    """
    Sanitizes HTML content by removing unsafe elements and returning plain text.
    """
    allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'p', 'ul', 'li', 'ol', 'br']
    return bleach.clean(html_content, tags=allowed_tags, strip=True)

def fetch_all_feeds(feed_urls):
    """
    Fetch multiple feeds concurrently using ThreadPoolExecutor.
    """
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_rss_feed, url) for url in feed_urls]
        return [future.result() for future in futures]
