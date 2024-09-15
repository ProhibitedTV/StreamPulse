"""
ui/story_display.py

This module is responsible for displaying news categories in a grid format within the StreamPulse application.
Each category will display stories including the headline, truncated description, and an optional image.
The module handles layout management for the central widget, ensuring that stories are displayed correctly
across a grid of 3 columns by 2 rows, with fade-in transitions for each story card.

Key Features:
- Displays stories grouped by categories in a grid layout.
- Handles layout updates and story transitions with fade-in effects.
- Displays images and text for each story, truncating descriptions to avoid overflow.
- Provides a simple, visually appealing display for the StreamPulse application.
"""

import os
import logging
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QGridLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QSize, Qt, QTimer
from api.fetchers import fetch_image, sanitize_html
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for layout configuration
MAX_DESCRIPTION_LENGTH = 300  # Limit for description length
CATEGORY_GRID_COLUMNS = 3  # Number of columns in the grid
CATEGORY_GRID_ROWS = 2  # Number of rows in the grid
IMAGE_WIDTH = 380
IMAGE_HEIGHT = 180

# Define the default image path
default_image_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'default.png')


def clear_widgets(frame):
    """
    Clears all widgets from the given frame.

    Args:
        frame (QWidget): The frame to clear.
    """
    for widget in frame.children():
        widget.deleteLater()


async def create_story_card(story, parent_frame):
    """
    Creates a story card with the headline, truncated description, and optional image.

    Args:
        story (dict): The story data containing title, description, and image URL.
        parent_frame (QWidget): The parent frame where the story card will be added.

    Returns:
        QWidget: A widget containing the story card layout.
    """
    headline = story.get("title", "No title available")
    description = sanitize_html(story.get("description", "No description available."))

    # Truncate the description if it's too long
    if len(description) > MAX_DESCRIPTION_LENGTH:
        description = description[:MAX_DESCRIPTION_LENGTH] + "..."

    image_url = story.get("media_content", [{}])[0].get("url", None)

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

    # Image display
    async def display_image(image_path):
        image_label = QLabel(parent_frame)
        pixmap = QPixmap(image_path).scaled(QSize(IMAGE_WIDTH, IMAGE_HEIGHT), aspectRatioMode=Qt.KeepAspectRatio)
        image_label.setPixmap(pixmap)
        layout.addWidget(image_label)

    # Load image asynchronously
    if image_url:
        image = await fetch_image(image_url, IMAGE_WIDTH, IMAGE_HEIGHT)  # Awaiting fetch_image
        if image:
            await display_image(image)
        else:
            await display_image(default_image_path)
    else:
        await display_image(default_image_path)

    return story_card


async def display_category_grid(content_frame, categories):
    """
    Displays a grid of categories with corresponding stories.

    Args:
        content_frame (QWidget): The frame where the grid will be displayed.
        categories (dict): A dictionary of categories containing lists of stories.
    """
    clear_widgets(content_frame)
    grid_layout = QGridLayout(content_frame)

    row = 0
    col = 0

    for category, feed in categories.items():
        # Ensure that we're working with the 'entries' of the feed
        stories = feed.get('entries', [])
        for story in stories[:CATEGORY_GRID_ROWS * CATEGORY_GRID_COLUMNS]:
            story_card = await create_story_card(story, content_frame)  # Await story card creation
            grid_layout.addWidget(story_card, row, col)

            # Move to the next cell in the grid
            col += 1
            if col >= CATEGORY_GRID_COLUMNS:
                col = 0
                row += 1
            if row >= CATEGORY_GRID_ROWS:
                break

    content_frame.setLayout(grid_layout)
    content_frame.show()


async def fade_in_category_grid(content_frame, categories):
    """
    Fades in the category grid when displayed.

    Args:
        content_frame (QWidget): The frame where the category grid is displayed.
        categories (dict): The dictionary of categories and their corresponding stories.
    """
    def fade(step=0):
        if step <= 1.0:
            content_frame.setWindowOpacity(step)
            QTimer.singleShot(50, lambda: fade(step + 0.05))

    fade()

    await display_category_grid(content_frame, categories)  # Await display of category grid
