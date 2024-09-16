"""
ui/story_display.py

This module handles the display of individual news stories in the StreamPulse application.
It is responsible for creating story cards with headlines, descriptions, and images.
The layout of the stories is managed by the main application in gui.py.

Key Features:
- Creates story cards with headlines, truncated descriptions, and optional images.
- Handles both pre-fetched images and a default image for cases where no image is available.
- Provides utility functions for clearing widgets from frames before updating content.

Functions:
- clear_widgets: Clears all widgets from the frame before populating new content.
- create_story_card: Creates a widget containing the layout for a single story card.
"""

import os
import logging
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QSize, Qt

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for layout configuration
MAX_DESCRIPTION_LENGTH = 300  # Limit for description length
IMAGE_WIDTH = 380
IMAGE_HEIGHT = 180

# Define the default image path
default_image_path = os.path.join(os.path.dirname(__file__), '..', '..', 'images', 'default.png')

def clear_widgets(frame):
    """
    Clears all widgets from the given frame.

    Args:
        frame (QWidget): The frame to clear.
    """
    for widget in frame.children():
        widget.deleteLater()

def create_story_card(story, parent_frame):
    """
    Creates a story card with the headline, truncated description, and optional image.

    Args:
        story (dict): The story data containing title, description, and pre-fetched image QPixmap.
        parent_frame (QWidget): The parent frame where the story card will be added.

    Returns:
        QWidget: A widget containing the story card layout.
    """
    headline = story.get("title", "No title available")
    description = story.get("description", "No description available.")

    # Truncate the description if it's too long
    if len(description) > MAX_DESCRIPTION_LENGTH:
        description = description[:MAX_DESCRIPTION_LENGTH] + "..."

    logging.debug(f"Displaying story: {headline}")

    # Create a story card layout
    story_card = QWidget(parent_frame)
    layout = QVBoxLayout(story_card)

    # Headline label
    headline_label = QLabel(headline, parent_frame)
    headline_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
    headline_label.setWordWrap(True)
    layout.addWidget(headline_label)

    # Description label
    description_label = QLabel(description, parent_frame)
    description_label.setStyleSheet("font-size: 14px; color: #b0b0b0;")
    description_label.setWordWrap(True)
    layout.addWidget(description_label)

    # Image display (using pre-fetched image or default if unavailable)
    image_label = QLabel(parent_frame)
    image_pixmap = story.get("image_pixmap", None)

    if image_pixmap and not image_pixmap.isNull():
        image_label.setPixmap(image_pixmap.scaled(QSize(IMAGE_WIDTH, IMAGE_HEIGHT), aspectRatioMode=Qt.KeepAspectRatio))
    else:
        default_pixmap = QPixmap(default_image_path)
        image_label.setPixmap(default_pixmap.scaled(QSize(IMAGE_WIDTH, IMAGE_HEIGHT), aspectRatioMode=Qt.KeepAspectRatio))

    layout.addWidget(image_label)

    return story_card
