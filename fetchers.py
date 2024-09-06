import requests
import feedparser
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import io

RSS_FETCH_TIMEOUT = 15

def fetch_rss_feed(feed_url):
    """
    Fetches RSS feed content from the provided URL using the `requests` library with a specified timeout.

    Args:
        feed_url (str): The URL of the RSS feed to fetch.

    Returns:
        dict: Parsed RSS feed content if the request is successful, else None.
    """
    try:
        response = requests.get(feed_url, timeout=RSS_FETCH_TIMEOUT)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        return feedparser.parse(response.content)
    except Exception as e:
        print(f"Error fetching feed from {feed_url}: {e}")
        return None

def fetch_image(url, width, height):
    """
    Fetches an image from a URL, resizes it to the specified width and height, and returns it as an `ImageTk.PhotoImage`.

    Args:
        url (str): The URL of the image to fetch.
        width (int): The width to resize the image to.
        height (int): The height to resize the image to.

    Returns:
        ImageTk.PhotoImage: The resized image object if the request is successful, else None.
    """
    try:
        response = requests.get(url, timeout=RSS_FETCH_TIMEOUT)
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        image = image.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception:
        return None

def sanitize_html(html_content):
    """
    Sanitizes HTML content by stripping out any tags and returning plain text.

    Args:
        html_content (str): The HTML content to sanitize.

    Returns:
        str: The plain text content without any HTML tags.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()
