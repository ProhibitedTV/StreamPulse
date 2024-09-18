"""
ui/story_display.py

This module handles the display of individual news stories in the StreamPulse application.
It is responsible for creating story cards with headlines, descriptions, images, category titles, and a progress bar.
The layout of the stories is managed by the main application in gui.py.

Key Features:
- Creates story cards with headlines, truncated descriptions, and optional images.
- Displays a category title for each story card.
- Displays a progress bar under each story card.
- Handles both pre-fetched images and a default image for cases where no image is available.
- Provides utility functions for clearing widgets from frames before updating content.

Functions:
- clear_widgets: Clears all widgets from the frame before populating new content.
- create_story_card: Creates a widget containing the layout for a single story card, including category titles and progress bars.
"""

import os
import logging
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QProgressBar
from PyQt5.QtGui import QPixmap, QFontMetrics
from PyQt5.QtCore import QSize, Qt
from api.fetchers import fetch_image

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
    This does not delete the frame or its layout.
    """
    for widget in frame.findChildren(QWidget):
        widget.deleteLater()

async def fetch_image_for_story(story):
    """
    Fetches the image for a story if available, using the `fetch_image` function.
    If an image URL is present, it fetches the image and returns a QPixmap object.
    Otherwise, it returns None.

    Args:
        story (dict): The story data containing image URLs.

    Returns:
        QPixmap or None: The image for the story or None if not available.
    """
    image_url = None

    # Try to find an image URL from the story data
    if 'media_thumbnail' in story and isinstance(story['media_thumbnail'], list) and 'url' in story['media_thumbnail'][0]:
        image_url = story['media_thumbnail'][0]['url']
    elif 'links' in story:
        for link in story['links']:
            if link.get('rel') == 'enclosure' and 'image' in link.get('type', ''):
                image_url = link.get('href')
                break

    if image_url:
        # Try fetching the image
        return await fetch_image(image_url, IMAGE_WIDTH, IMAGE_HEIGHT)
    return None

async def create_story_card(story, category, parent_frame):
    """
    Creates a story card with the category title, headline, truncated description, optional image, and progress bar.

    Args:
        story (dict): The story data containing title, description, and pre-fetched image QPixmap.
        category (str): The category title to display above the story.
        parent_frame (QWidget): The parent frame where the story card will be added.

    Returns:
        QWidget: A widget containing the story card layout, including category title and progress bar.
    """
    # Log the story to check if it has the required fields
    logging.info(f"Creating story card for story: {story}")

    # Extract required story fields
    headline = story.get("title", "No title available")
    description = story.get("description", "No description available.")

    # Truncate the description if it's too long
    if len(description) > MAX_DESCRIPTION_LENGTH:
        description = description[:MAX_DESCRIPTION_LENGTH] + "..."

    # Create a story card layout
    story_card = QWidget(parent_frame)
    layout = QVBoxLayout(story_card)

    # Apply more transparent background to the story card
    story_card.setStyleSheet("""
        background-color: rgba(44, 62, 80, 0.6);  /* Dark blue with 60% opacity */
        border-radius: 10px;
        padding: 8px;
        margin-bottom: 5px;
    """)

    # Category title label
    category_label = QLabel(category, parent_frame)
    category_label.setStyleSheet("""
        font-size: 24px;
        font-weight: bold;
        color: #e74c3c;
        padding: 10px;
    """)
    layout.addWidget(category_label)

    # Headline label with ellipsis for overflow using QFontMetrics
    headline_label = QLabel(headline, parent_frame)
    headline_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
    font_metrics = QFontMetrics(headline_label.font())
    elided_text = font_metrics.elidedText(headline, Qt.ElideRight, 380)  # Truncate with ellipsis if too long
    headline_label.setText(elided_text)
    layout.addWidget(headline_label)

    # Description label
    description_label = QLabel(description, parent_frame)
    description_label.setStyleSheet("font-size: 14px; color: #b0b0b0;")
    description_label.setWordWrap(True)
    layout.addWidget(description_label)

    # Image display (using pre-fetched image or default if unavailable)
    image_label = QLabel(parent_frame)
    image_pixmap = await fetch_image_for_story(story)

    if image_pixmap and not image_pixmap.isNull():
        image_label.setPixmap(image_pixmap.scaled(QSize(IMAGE_WIDTH, IMAGE_HEIGHT), aspectRatioMode=Qt.KeepAspectRatio))
        logging.info("Using pre-fetched image for story.")
    else:
        default_pixmap = QPixmap(default_image_path)
        image_label.setPixmap(default_pixmap.scaled(QSize(IMAGE_WIDTH, IMAGE_HEIGHT), aspectRatioMode=Qt.KeepAspectRatio))
        logging.warning(f"No image found for story: {headline}. Using default image.")

    layout.addWidget(image_label)

    # Progress bar to show rotation countdown
    progress_bar = QProgressBar(parent_frame)
    progress_bar.setStyleSheet("QProgressBar {border: 2px solid white; border-radius: 5px; background-color: #2c3e50;} QProgressBar::chunk {background-color: #3498db;}")
    layout.addWidget(progress_bar)

    return story_card, progress_bar