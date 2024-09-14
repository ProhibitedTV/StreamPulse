"""
ui/story_display.py

This module is responsible for displaying individual news stories in the StreamPulse application.
It handles the rendering of a single story card, including the headline, truncated description,
optional image, and sentiment analysis. The module leverages asynchronous tasks for fetching
images and performing sentiment analysis using a local Ollama instance, and integrates with the
text-to-speech engine for verbal story summaries.

Key Features:
- Displays a headline, image, and description for a single news story.
- Truncates overly long descriptions to prevent layout overflow.
- Asynchronously fetches images and performs sentiment analysis.
- Updates the user interface with sentiment results and story details.
- Manages text-to-speech integration for verbal story summaries.

Functions:
- clear_widgets: Clears all widgets from a given frame.
- display_story_card: Displays a story's details, including headline, description, image, and sentiment.
- clear_and_display_story: Clears the current content and displays a new story.
- fade_in_story: Fades in the new story and handles sentiment analysis asynchronously.
"""

import os
import logging
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, QSize, Qt, QMetaObject, Q_ARG
from api.fetchers import fetch_image, sanitize_html
from utils.threading import run_in_thread
from utils.web import open_link
from api.tts_engine import tts_queue
from api.sentiment import analyze_text

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global flag to indicate whether content is active
is_content_active = False

MAX_DESCRIPTION_LENGTH = 300  # Limit for description length


def clear_widgets(frame):
    """
    Clears all widgets from the given frame.

    Args:
        frame (QWidget): The frame to clear.
    """
    for widget in frame.children():
        widget.deleteLater()


def display_story_card(story, parent_frame, sentiment_frame):
    """
    Displays a single news story card including the headline, truncated description, image, and sentiment.

    Args:
        story (dict): The story data containing title, description, image, and source link.
        parent_frame (QWidget): The frame to display the story.
        sentiment_frame (QWidget): The frame to display sentiment analysis results.
    """
    global is_content_active
    if not is_content_active:
        logging.info("Content is inactive, skipping story display.")
        return

    headline = story.get("title", "No title available")
    description = sanitize_html(story.get("description", "No description available."))

    # Truncate the description if it's too long
    if len(description) > MAX_DESCRIPTION_LENGTH:
        description = description[:MAX_DESCRIPTION_LENGTH] + "..."

    image_url = story.get("media_content", [{}])[0].get("url", None)

    logging.debug(f"Displaying story: {headline}")

    def analyze_sentiment():
        if not is_content_active:
            return
        try:
            sentiment = analyze_text(description, parent_frame, sentiment_frame)
            update_sentiment_display(sentiment)
        except Exception as e:
            logging.error(f"Sentiment analysis failed for {headline}: {e}")
            update_sentiment_display("Sentiment analysis failed")

    def update_sentiment_display(sentiment):
        QMetaObject.invokeMethod(sentiment_frame, "clear")
        sentiment_label = QLabel(f"Sentiment: {sentiment}", sentiment_frame)
        sentiment_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        QMetaObject.invokeMethod(sentiment_frame.layout(), "addWidget", Q_ARG(QLabel, sentiment_label))

        # Add the story and sentiment to the TTS queue
        summary = f"Headline: {headline}. Sentiment: {sentiment}."
        tts_queue.put(summary)

    run_in_thread(analyze_sentiment)

    layout = QVBoxLayout(parent_frame)
    
    headline_label = QLabel(headline, parent_frame)
    headline_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
    headline_label.setWordWrap(True)
    layout.addWidget(headline_label)

    # Display image
    def display_image(image):
        if not is_content_active:
            return
        image_label = QLabel(parent_frame)

        # Use a default image from the correct path
        default_image_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'default.png')
        
        pixmap = QPixmap(image).scaled(QSize(380, 180), aspectRatioMode=Qt.KeepAspectRatio)
        QMetaObject.invokeMethod(image_label, "setPixmap", Q_ARG(QPixmap, pixmap))
        layout.addWidget(image_label)

    def load_image():
        try:
            image = fetch_image(image_url, 380, 180)
            if image:
                display_image(image)
            else:
                logging.warning(f"Failed to load image from: {image_url}")
                display_image(default_image_path)  # Reference to default image
        except Exception as e:
            logging.error(f"Error fetching image from {image_url}: {e}")
            display_image(default_image_path)  # Reference to default image

    # Display description
    description_label = QLabel(description, parent_frame)
    description_label.setStyleSheet("font-size: 14px; color: #b0b0b0;")
    description_label.setWordWrap(True)
    layout.addWidget(description_label)

    # Display source link
    source = story.get("link", "Unknown Source")
    source_label = QLabel(f"<a href='{source}'>Read more</a>", parent_frame)
    source_label.setOpenExternalLinks(True)
    source_label.setStyleSheet("color: blue; text-decoration: underline;")
    layout.addWidget(source_label)


def clear_and_display_story(content_frame, story, sentiment_frame):
    """
    Clears the current content and displays a new story.

    Args:
        content_frame (QWidget): The frame where the story will be displayed.
        story (dict): The story data to display.
        sentiment_frame (QWidget): The frame for sentiment analysis results.
    """
    global is_content_active
    is_content_active = False  # Deactivate current content
    clear_widgets(content_frame)
    clear_widgets(sentiment_frame)
    is_content_active = True  # Activate new content

    display_story_card(story, content_frame, sentiment_frame)


def fade_in_story(content_frame, story, sentiment_frame):
    """
    Fades in the story when displayed and calls sentiment analysis.

    Args:
        content_frame (QWidget): Frame where the story is to be displayed.
        story (dict): The story to be displayed.
        sentiment_frame (QWidget): Frame to display the sentiment analysis result.
    """
    logging.info(f"Displaying story: {story.get('title', 'No title available')}")
    clear_and_display_story(content_frame, story, sentiment_frame)

    # Add fade-in effect
    fade_frame = QWidget(content_frame)
    fade_frame.setStyleSheet("background-color: black;")
    fade_frame.setWindowOpacity(0.0)
    fade_frame.show()

    def fade(step=0):
        if step <= 1.0:
            fade_frame.setWindowOpacity(step)
            QTimer.singleShot(50, lambda: fade(step + 0.05))

    fade()

import os