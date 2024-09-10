# Standard Library Imports
import logging
import queue

# Third-party Library Imports
from PyQt5.QtCore import QTimer

# Internal Project Imports
from api.fetchers import fetch_rss_feed, sanitize_html
from api.sentiment import analyze_text
from ui.story_display import fade_in_story, clear_and_display_story
from utils.threading import run_in_thread

# Constants
UPDATE_INTERVAL = 10000  # 10 seconds
feed_queue = queue.Queue()  # Global queue for feed entries

def update_feed(rss_feeds, content_frame, root, category_name, sentiment_frame):
    """
    Fetch and display RSS feed content dynamically, updating every 10 seconds.
    Also updates sentiment analysis in a separate widget and performs TTS.

    Args:
        rss_feeds (list): A list of RSS feed URLs to fetch data from.
        content_frame (QWidget): The frame in the GUI where the feed content will be displayed.
        root (QWidget): The root PyQt5 main window or parent widget.
        category_name (str): The category name of the feed (e.g., 'General News').
        sentiment_frame (QWidget): A frame for displaying sentiment analysis results.
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
            display_placeholder_message(content_frame, "No stories available")
        else:
            logging.info(f"Total entries fetched for {category_name}: {len(feed_entries)}")
            logging.debug(f"Adding {len(feed_entries)} entries to the queue for category: {category_name}")
            feed_queue.put((category_name, feed_entries))

    def show_next_story():
        """Show the next story from the feed. Display a placeholder if no new stories are found."""
        try:
            category, entries = feed_queue.get_nowait()
            if category == category_name and entries:
                story = entries.pop(0)
                
                # Safely handle missing attributes for 'description' and 'title'
                description = sanitize_html(getattr(story, 'description', 'No description available'))
                title = getattr(story, 'title', 'No title available')

                logging.debug(f"Displaying story: {title} for category: {category_name}")

                # Perform sentiment analysis with a fallback in case of failure
                try:
                    sentiment = analyze_text(description, model="llama3:latest")
                except Exception as e:
                    logging.error(f"Sentiment analysis failed: {e}")
                    sentiment = 'Unknown'

                fade_in_story(content_frame, story, sentiment_frame, sentiment)
                entries.append(story)  # Cycle through stories
            else:
                logging.debug(f"No stories available for category: {category_name}")
                display_placeholder_message(content_frame, "No stories available")
        except queue.Empty:
            logging.debug(f"Feed queue is empty for category: {category_name}")
        finally:
            logging.debug(f"Scheduling next story display in {UPDATE_INTERVAL}ms for category: {category_name}")

    def display_placeholder_message(frame, message):
        """Display a placeholder message when no feed entries are available."""
        logging.debug(f"Displaying placeholder message for category: {category_name} - {message}")
        for widget in frame.children():
            widget.deleteLater()  # Clear existing widgets
        label = QLabel(message, parent=frame)
        label.setStyleSheet("font-size: 14px;")
        label.setAlignment(Qt.AlignCenter)
        frame.layout().addWidget(label)

    # Fetch feeds using threading to prevent blocking
    logging.debug(f"Starting to fetch feeds for category: {category_name}")
    run_in_thread(fetch_feed_entries)

    # Timer for story display
    timer = QTimer(root)
    timer.timeout.connect(show_next_story)
    timer.start(UPDATE_INTERVAL)

    # Refresh the feed every 5 minutes (30 intervals)
    def refresh_feed():
        """Refresh feeds periodically by refetching them in the background."""
        logging.debug(f"Refreshing feeds for category: {category_name}")
        run_in_thread(fetch_feed_entries)

    # Timer for feed refresh (every 5 minutes)
    refresh_timer = QTimer(root)
    refresh_timer.timeout.connect(refresh_feed)
    refresh_timer.start(UPDATE_INTERVAL * 30)

    show_next_story()  # Show the first story immediately
