"""
feeds.py

This module handles the loading and updating of RSS feeds for the StreamPulse application.
It fetches the RSS feed content, displays news stories dynamically in the PyQt5 interface,
and updates the UI in regular intervals.

Functions:
    load_feed_config - Loads RSS feed URLs from a configuration file.
    load_feeds - Loads RSS feeds concurrently and updates the progress.
    update_feed - Dynamically fetches and displays RSS feed content, updating every 10 seconds.
"""

import logging
import json
import os
import queue
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

# Initialize logging
logging.basicConfig(level=logging.INFO)

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
            logging.info(f"Loaded RSS feed configuration from {config_file}.")
            return rss_feeds
    except Exception as e:
        logging.error(f"Error loading feed configuration: {e}")
        return {}

def load_feeds(rss_feeds, update_progress):
    """
    Loads all feeds concurrently using threads and updates the progress bar.

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

    def update_progress_callback(feed):
        """
        Callback to update progress bar after each feed is processed.
        """
        loaded_feeds[0] += 1
        progress = (loaded_feeds[0] / total_feeds) * 100
        update_progress(progress)

    # Load feeds in separate threads using the fetch_rss_feed from fetchers.py
    for category, feeds in rss_feeds.items():
        for feed in feeds:
            run_in_thread(fetch_rss_feed, feed, update_progress_callback)

    return rss_feeds

def update_feed(rss_feeds, content_frame, root, category_name, sentiment_frame):
    """
    Fetch and display RSS feed content dynamically, updating every 10 seconds.

    Args:
        rss_feeds (list): A list of RSS feed URLs to fetch data from.
        content_frame (QWidget): The frame in the GUI where the feed content will be displayed.
        root (QWidget): The main PyQt5 window or parent widget.
        category_name (str): The category name of the feed (e.g., 'General News').
        sentiment_frame (QWidget): A frame for displaying sentiment analysis results.
    """
    def fetch_feed_entries():
        feed_entries = []
        logging.info(f"Fetching feeds for category: {category_name}")

        for feed_url in rss_feeds:
            try:
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

        Args:
            frame (QWidget): The content frame in which to display the message.
            message (str): The message to display.
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
