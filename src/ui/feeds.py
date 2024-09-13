"""
ui/feeds.py

This module handles the loading and updating of RSS feeds for the StreamPulse application.
It fetches the RSS feed content, displays news stories dynamically in the PyQt5 interface,
and updates the UI in regular intervals.

Key Enhancements:
    - Retry mechanism with exponential backoff for feed fetching.
    - Feed disabling after repeated failures to reduce load.
    - Failure tracking and creative error handling.
"""

import logging
import json
import os
import queue
import threading
import time
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QLabel
from utils.threading import run_in_thread
from api.fetchers import fetch_rss_feed, sanitize_html
from api.sentiment import analyze_text
from ui.story_display import fade_in_story

# Constants
UPDATE_INTERVAL = 10000  # 10 seconds
feed_queue = queue.Queue()  # Global queue for feed entries
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'rss_feeds.json')
RETRY_LIMIT = 3  # Maximum number of retry attempts for a failed feed
RETRY_BACKOFF = 2  # Exponential backoff multiplier (2^n seconds)
DISABLED_FEEDS = set()  # Track feeds that are disabled due to repeated failures

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Track failure count for each feed URL
failure_counts = {}

def load_feed_config(config_file=None):
    """
    Loads the RSS feed URLs from a JSON configuration file. Defaults to 'rss_feeds.json'
    in the 'ui' directory if no path is provided.

    Args:
        config_file (str, optional): Path to the configuration file.

    Returns:
        dict: A dictionary of categorized RSS feeds, or an empty dict if loading fails.
    """
    config_file = config_file or DEFAULT_CONFIG_PATH

    try:
        with open(config_file, 'r') as file:
            rss_feeds = json.load(file)
            if rss_feeds:
                logging.info(f"Loaded RSS feed configuration from {config_file}.")
            else:
                logging.warning(f"No RSS feeds found in {config_file}.")
            return rss_feeds
    except Exception as e:
        logging.error(f"Error loading feed configuration from {config_file}: {e}")
        return {}

def fetch_with_retry(feed_url, category, retries=0):
    """
    Fetch an RSS feed with retry logic using exponential backoff. If the feed fails
    after RETRY_LIMIT attempts, it is disabled for the current session.

    Args:
        feed_url (str): The URL of the RSS feed.
        category (str): The category to which the feed belongs.
        retries (int, optional): Current retry count.

    Returns:
        feed: The fetched feed object, or None if it fails after retries.
    """
    try:
        if feed_url in DISABLED_FEEDS:
            logging.warning(f"Feed {feed_url} is disabled and will not be fetched.")
            return None

        feed = fetch_rss_feed(feed_url)
        if feed and feed.entries:
            logging.info(f"Successfully fetched feed from {feed_url}")
            return feed
        else:
            raise ValueError(f"Feed {feed_url} returned no entries.")

    except Exception as e:
        logging.error(f"Error fetching feed {feed_url}: {e}")

        # Retry with exponential backoff
        if retries < RETRY_LIMIT:
            retry_delay = RETRY_BACKOFF ** retries
            logging.info(f"Retrying feed {feed_url} in {retry_delay} seconds (Attempt {retries + 1}/{RETRY_LIMIT})")
            time.sleep(retry_delay)
            return fetch_with_retry(feed_url, category, retries + 1)
        else:
            logging.error(f"Feed {feed_url} failed after {RETRY_LIMIT} retries. Disabling for this session.")
            DISABLED_FEEDS.add(feed_url)
            return None

def load_feeds(rss_feeds, update_progress):
    """
    Loads all feeds concurrently using threads and updates the progress bar.
    Includes retry logic and feed disabling.

    Args:
        rss_feeds (dict): Dictionary of RSS feeds.
        update_progress (function): Function to update the loading progress.

    Returns:
        dict: The RSS feeds for further use, or None if no feeds are available.
    """
    if not rss_feeds:
        logging.error("RSS feeds are None. Cannot load feeds.")
        return None

    total_feeds = sum(len(feeds) for feeds in rss_feeds.values())
    loaded_feeds = [0]
    loaded_data = {}
    threads = []

    def update_progress_callback(feed, category):
        """
        Callback to update progress bar after each feed is processed and store the data.
        """
        if category not in loaded_data:
            loaded_data[category] = []
        if feed:
            loaded_data[category].append(feed)

        loaded_feeds[0] += 1
        progress = (loaded_feeds[0] / total_feeds) * 100
        update_progress(progress)

    def fetch_and_store_feed(feed, category):
        fetched_feed = fetch_with_retry(feed, category)
        update_progress_callback(fetched_feed, category)

    # Create threads for each feed and start fetching
    for category, feeds in rss_feeds.items():
        for feed in feeds:
            thread = threading.Thread(target=fetch_and_store_feed, args=(feed, category))
            threads.append(thread)
            thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    return loaded_data if loaded_feeds[0] > 0 else None

def update_feed(rss_feeds, content_frame, root, category_name, sentiment_frame):
    """
    Fetch and display RSS feed content dynamically, updating every 10 seconds.
    """
    def fetch_feed_entries():
        feed_entries = []
        logging.info(f"Fetching feeds for category: {category_name}")

        for feed_url in rss_feeds:
            feed = fetch_with_retry(feed_url, category_name)
            if feed:
                feed_entries.extend(feed.entries[:3])  # Limit to 3 stories per feed

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

                try:
                    sentiment = analyze_text(description, model="llama3:latest")
                except Exception as e:
                    logging.error(f"Sentiment analysis failed: {e}")
                    sentiment = 'Unknown'

                fade_in_story(content_frame, story, sentiment_frame, sentiment)
                entries.append(story)  # Cycle stories
            else:
                display_placeholder_message(content_frame, "No stories available")
        except queue.Empty:
            logging.debug(f"Feed queue is empty for category: {category_name}")
        finally:
            logging.debug(f"Scheduling next story display in {UPDATE_INTERVAL}ms for category: {category_name}")

    def display_placeholder_message(frame, message):
        """
        Displays a placeholder message in case no stories are available.
        """
        for widget in frame.children():
            widget.deleteLater()  # Clear existing widgets
        label = QLabel(message, parent=frame)
        label.setStyleSheet("font-size: 14px;")
        label.setAlignment(Qt.AlignCenter)
        frame.layout().addWidget(label)

    # Start fetching the feed entries in the background
    run_in_thread(fetch_feed_entries)

    # Schedule updates to show the next story at regular intervals
    timer = QTimer(root)
    timer.timeout.connect(show_next_story)
    timer.start(UPDATE_INTERVAL)

    # Schedule feed refreshes periodically (e.g., every 5 minutes)
    refresh_timer = QTimer(root)
    refresh_timer.timeout.connect(fetch_feed_entries)
    refresh_timer.start(UPDATE_INTERVAL * 30)

    # Show the first story immediately
    show_next_story()
