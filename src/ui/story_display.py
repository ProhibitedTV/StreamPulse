"""
story_display.py

This module handles the display of news stories in the StreamPulse application.
It manages loading images, sentiment analysis, text-to-speech processing, and
updating the PyQt5 interface with story details.
"""

import os
import logging
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QFrame, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
from api.fetchers import fetch_image, sanitize_html
from utils.threading import run_in_thread
from utils.web import open_link
from api.tts_engine import tts_queue
from api.sentiment import analyze_text

# Global flag to indicate whether content is active
is_content_active = False

def clear_widgets(frame):
    """Helper function to clear all widgets from a frame."""
    for widget in frame.children():
        widget.deleteLater()

def display_story_card(story, parent_frame, sentiment_frame):
    """
    Displays a news story card including the headline, description, image, and source.

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
    image_url = story.get("media_content", [{}])[0].get("url", None)

    logging.debug(f"Displaying story: {headline}")
    
    def analyze_sentiment():
        if not is_content_active:
            return
        try:
            sentiment = analyze_text(description, model="llama3:latest")
            update_sentiment_display(sentiment)
        except Exception as e:
            logging.error(f"Sentiment analysis failed for {headline}: {e}")
            update_sentiment_display("Sentiment analysis failed")

    def update_sentiment_display(sentiment):
        clear_widgets(sentiment_frame)
        sentiment_label = QLabel(f"Sentiment: {sentiment}", sentiment_frame)
        sentiment_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        sentiment_frame.layout().addWidget(sentiment_label)
        
        # Add the story and sentiment to the TTS queue
        summary = f"Headline: {headline}. Sentiment: {sentiment}."
        tts_queue.put(summary)

    run_in_thread(analyze_sentiment)

    layout = QVBoxLayout(parent_frame)
    
    headline_label = QLabel(headline, parent_frame)
    headline_label.setStyleSheet("font-size: 18px; font-weight: bold;")
    headline_label.setWordWrap(True)
    layout.addWidget(headline_label)

    def display_image(image):
        """Displays the image in the layout."""
        if not is_content_active:
            return
        image_label = QLabel(parent_frame)
        image_label.setPixmap(QPixmap(image))
        layout.addWidget(image_label)

    if image_url:
        def load_image():
            try:
                image = fetch_image(image_url, 380, 180)
                if image:
                    display_image(image)
                else:
                    logging.warning(f"Failed to load image from: {image_url}")
                    display_image("default.png")
            except Exception as e:
                logging.error(f"Error fetching image from {image_url}: {e}")
                display_image("default.png")

        run_in_thread(load_image)
    else:
        display_image("default.png")

    description_label = QLabel(description, parent_frame)
    description_label.setWordWrap(True)
    layout.addWidget(description_label)

    source = story.get("link", "Unknown Source")
    source_label = QLabel(f"Read more at: {source}", parent_frame)
    source_label.setStyleSheet("color: blue; text-decoration: underline; cursor: pointer;")
    source_label.mousePressEvent = lambda event: open_link(source)
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
