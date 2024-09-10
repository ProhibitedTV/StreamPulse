# Standard Library Imports
import logging
import queue
import tkinter as tk
from tkinter import ttk

# Third-party Library Imports
from PIL import Image, ImageTk

# Internal Project Imports
from api.fetchers import fetch_rss_feed, fetch_image, sanitize_html
from api.sentiment import analyze_text
from api.tts_engine import tts_queue
from utils.threading import run_in_thread
from ui.story_display import fade_in_story, clear_and_display_story

# Constants
UPDATE_INTERVAL = 10000  # 10 seconds
feed_queue = queue.Queue()  # Global queue for feed entries

def update_feed(rss_feeds, content_frame, root, category_name, sentiment_frame):
    """
    Fetch and display RSS feed content dynamically, updating every 10 seconds.
    Also updates sentiment analysis in a separate widget and performs TTS.
    
    Args:
        rss_feeds (list): A list of RSS feed URLs to fetch data from.
        content_frame (tk.Widget): The frame in the GUI where the feed content will be displayed.
        root (tk.Tk): The root Tkinter window.
        category_name (str): The category name of the feed (e.g., 'General News').
        sentiment_frame (tk.Widget): A frame for displaying sentiment analysis results.
    """
    feed_entries = []

    def fetch_feed_entries():
        """Fetch RSS feed entries and add them to the global feed queue."""
        nonlocal feed_entries
        feed_entries = []
        logging.debug(f"Fetching feeds for category: {category_name}")

        for feed_url in rss_feeds:
            try:
                logging.debug(f"Fetching feed from URL: {feed_url}")
                feed = fetch_rss_feed(feed_url)
                if feed:
                    logging.debug(f"Feed fetched from {feed_url}. Number of entries: {len(feed.entries[:3])}")
                    feed_entries.extend(feed.entries[:3])  # Limit to 3 stories per feed
                else:
                    logging.warning(f"No feed found at {feed_url}")
            except Exception as e:
                logging.error(f"Error fetching feed from {feed_url}: {e}")

        if not feed_entries:
            logging.warning(f"No entries retrieved for category: {category_name}")
            root.after(0, lambda: display_placeholder_message(content_frame, "No stories available"))
        else:
            logging.info(f"Total entries fetched for {category_name}: {len(feed_entries)}")
            feed_queue.put((category_name, feed_entries))

    def show_next_story():
        """Show the next story from the feed. Display a placeholder if no new stories are found."""
        try:
            category, entries = feed_queue.get_nowait()
            if category == category_name and entries:
                story = entries.pop(0)
                root.after(0, lambda: fade_in_story(content_frame, story, sentiment_frame))
                entries.append(story)  # Cycle through stories
            else:
                logging.debug(f"No stories available for category: {category_name}")
                root.after(0, lambda: display_placeholder_message(content_frame, "No stories available"))
        except queue.Empty:
            logging.debug(f"No new stories in the feed queue for category: {category_name}")
        finally:
            root.after(UPDATE_INTERVAL, show_next_story)

    def display_placeholder_message(frame, message):
        """Display a placeholder message when no feed entries are available."""
        for widget in frame.winfo_children():
            widget.destroy()  # Clear existing widgets
        label = ttk.Label(frame, text=message, font=("Helvetica", 14), anchor="center")
        label.pack(expand=True)

    # Fetch feeds using threading to prevent blocking
    run_in_thread(fetch_feed_entries)

    # Schedule the first story display
    root.after(UPDATE_INTERVAL, show_next_story)

    # Refresh the feed every 5 minutes (30 intervals)
    def refresh_feed():
        """Refresh feeds periodically by refetching them in the background."""
        logging.debug(f"Refreshing feeds for category: {category_name}")
        run_in_thread(fetch_feed_entries)
        root.after(UPDATE_INTERVAL * 30, refresh_feed)

    refresh_feed()