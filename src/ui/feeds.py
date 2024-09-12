import logging
import time
import json
import queue
from PyQt5.QtCore import QTimer
from utils.threading import run_in_thread
from api.fetchers import fetch_rss_feed, sanitize_html
from api.sentiment import analyze_text
from ui.story_display import fade_in_story

# Constants
UPDATE_INTERVAL = 10000  # 10 seconds
feed_queue = queue.Queue()  # Global queue for feed entries

logging.basicConfig(level=logging.INFO)

def load_feed_config(config_file):
    """
    Loads the RSS feed URLs from a JSON configuration file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: A dictionary of categorized RSS feeds.
    """
    try:
        with open(config_file, 'r') as file:
            rss_feeds = json.load(file)
            logging.info(f"Loaded RSS feed configuration from {config_file}.")
            return rss_feeds
    except Exception as e:
        logging.error(f"Error loading feed configuration: {e}")
        return {}

def get_feeds_by_category(category, rss_feeds):
    """
    Returns the RSS feeds of a given category.

    Args:
        category (str): Category of the RSS feeds (e.g., "general", "financial").
        rss_feeds (dict): A dictionary containing the categorized RSS feeds.

    Returns:
        list: List of RSS feed URLs for the specified category.
    """
    category = category.lower().strip()
    if category in rss_feeds:
        logging.info(f"Fetching feeds for category: {category}")
        return rss_feeds[category]
    else:
        valid_categories = ", ".join(rss_feeds.keys())
        logging.error(f"Invalid feed category '{category}'. Valid categories are: {valid_categories}")
        return []

def load_feeds_in_thread(feed, update_progress, total_feeds, loaded_feeds):
    """
    Loads a single feed in a separate thread and updates the progress.

    Args:
        feed (str): The RSS feed URL to be loaded.
        update_progress (function): Function to update the progress bar.
        total_feeds (int): Total number of feeds to be loaded.
        loaded_feeds (list): Shared list to track the number of loaded feeds.
    """
    try:
        time.sleep(0.5)  # Simulate network delay
        loaded_feeds[0] += 1
        progress = (loaded_feeds[0] / total_feeds) * 100
        update_progress(progress)
        logging.info(f"Loaded feed: {feed}")
    except Exception as e:
        logging.error(f"Error loading feed {feed}: {e}")

def load_feeds(rss_feeds, update_progress):
    """
    Loads all feeds concurrently using threads and updates the progress bar.

    Args:
        rss_feeds (dict): Dictionary of RSS feeds.
        update_progress (function): Function to update the loading progress.
    """
    total_feeds = sum(len(feeds) for feeds in rss_feeds.values())
    loaded_feeds = [0]

    for category, feeds in rss_feeds.items():
        for feed in feeds:
            run_in_thread(load_feeds_in_thread, feed, update_progress, total_feeds, loaded_feeds)

def update_feed(rss_feeds, content_frame, root, category_name, sentiment_frame):
    """
    Fetch and display RSS feed content dynamically, updating every 10 seconds.

    Args:
        rss_feeds (list): A list of RSS feed URLs to fetch data from.
        content_frame (QWidget): The frame in the GUI where the feed content will be displayed.
        root (QWidget): The root PyQt5 main window or parent widget.
        category_name (str): The category name of the feed (e.g., 'General News').
        sentiment_frame (QWidget): A frame for displaying sentiment analysis results.
    """
    feed_entries = []

    def fetch_feed_entries():
        nonlocal feed_entries
        feed_entries = []
        logging.debug(f"Fetching feeds for category: {category_name}")

        for feed_url in rss_feeds:
            try:
                logging.debug(f"Fetching feed from URL: {feed_url}")
                feed = fetch_rss_feed(feed_url)
                if feed:
                    feed_entries.extend(feed.entries[:3])  # Limit to 3 stories per feed
                else:
                    logging.warning(f"No feed found at {feed_url}")
            except Exception as e:
                logging.error(f"Error fetching feed from {feed_url}: {e}")

        if not feed_entries:
            logging.warning(f"No entries retrieved for category: {category_name}")
            display_placeholder_message(content_frame, "No stories available")
        else:
            feed_queue.put((category_name, feed_entries))

    def show_next_story():
        try:
            category, entries = feed_queue.get_nowait()
            if category == category_name and entries:
                story = entries.pop(0)
                description = sanitize_html(getattr(story, 'description', 'No description available'))
                title = getattr(story, 'title', 'No title available')

                try:
                    sentiment = analyze_text(description, model="llama3:latest")
                except Exception as e:
                    logging.error(f"Sentiment analysis failed: {e}")
                    sentiment = 'Unknown'

                fade_in_story(content_frame, story, sentiment_frame, sentiment)
                entries.append(story)
            else:
                display_placeholder_message(content_frame, "No stories available")
        except queue.Empty:
            logging.debug(f"Feed queue is empty for category: {category_name}")
        finally:
            logging.debug(f"Scheduling next story display in {UPDATE_INTERVAL}ms for category: {category_name}")

    def display_placeholder_message(frame, message):
        for widget in frame.children():
            widget.deleteLater()  # Clear existing widgets
        label = QLabel(message, parent=frame)
        label.setStyleSheet("font-size: 14px;")
        label.setAlignment(Qt.AlignCenter)
        frame.layout().addWidget(label)

    run_in_thread(fetch_feed_entries)

    timer = QTimer(root)
    timer.timeout.connect(show_next_story)
    timer.start(UPDATE_INTERVAL)

    def refresh_feed():
        run_in_thread(fetch_feed_entries)

    refresh_timer = QTimer(root)
    refresh_timer.timeout.connect(refresh_feed)
    refresh_timer.start(UPDATE_INTERVAL * 30)

    show_next_story()
