import os
import logging
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QFrame, QProgressBar, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
from PIL import Image
from api.fetchers import fetch_image, sanitize_html
from utils.threading import run_in_thread
from utils.web import open_link
from api.tts_engine import tts_queue
from api.sentiment import analyze_text

# Global flag to indicate whether content is active
is_content_active = False

def display_story_card(story, parent_frame, sentiment_frame):
    global is_content_active
    if not is_content_active:
        logging.info("Content is inactive, skipping story display.")
        return

    headline = story.get("title", "No title available")
    description = sanitize_html(story.get("description", "No description available."))
    image_url = story.get("media_content", [{}])[0].get("url", None)

    logging.debug(f"Displaying story: {headline}")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    default_image_path = os.path.join(project_root, 'images', 'default.png')

    def analyze_sentiment():
        if not is_content_active:
            logging.info("Content is inactive, skipping sentiment analysis.")
            return
        try:
            logging.debug(f"Analyzing sentiment for story: {headline}")
            sentiment = analyze_text(description, model="llama3:latest")
            parent_frame.update()
            update_sentiment_display(sentiment)
        except Exception as e:
            logging.error(f"Sentiment analysis failed for {headline}: {e}")
            parent_frame.update()
            update_sentiment_display("Sentiment analysis failed")

    def update_sentiment_display(sentiment):
        if not is_content_active:
            logging.info("Content is inactive, skipping sentiment display.")
            return

        logging.debug(f"Updating sentiment display with: {sentiment}")
        for widget in sentiment_frame.children():
            widget.deleteLater()  # Clear previous widgets
        sentiment_label = QLabel(f"Sentiment: {sentiment}", sentiment_frame)
        sentiment_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        sentiment_frame.layout().addWidget(sentiment_label)

        summary = f"Headline: {headline}. Sentiment: {sentiment}."
        tts_queue.put(summary)

    run_in_thread(analyze_sentiment)

    layout = QVBoxLayout(parent_frame)

    headline_label = QLabel(headline, parent_frame)
    headline_label.setStyleSheet("font-size: 18px; font-weight: bold;")
    headline_label.setWordWrap(True)
    layout.addWidget(headline_label)

    def load_default_image():
        try:
            default_image = Image.open(default_image_path)
            default_image = default_image.resize((380, 180), Image.Resampling.LANCZOS)
            display_image(default_image)
        except Exception as e:
            logging.error(f"Error loading default image: {e}")

    def display_image(image):
        if not is_content_active:
            logging.info("Content is inactive, skipping image display.")
            return
        try:
            img = QPixmap.fromImage(image)
            image_label = QLabel(parent_frame)
            image_label.setPixmap(img)
            layout.addWidget(image_label)
        except Exception as e:
            logging.error(f"Error displaying image: {e}")
            load_default_image()

    if image_url:
        def load_image():
            try:
                image = fetch_image(image_url, 380, 180)
                if image:
                    display_image(image)
                else:
                    logging.warning(f"Failed to load image from: {image_url}")
                    load_default_image()
            except Exception as e:
                logging.error(f"Error fetching image from {image_url}: {e}")
                load_default_image()

        run_in_thread(load_image)
    else:
        load_default_image()

    description_label = QLabel(description, parent_frame)
    description_label.setWordWrap(True)
    layout.addWidget(description_label)

    source = story.get("link", "Unknown Source")
    source_label = QLabel(f"Read more at: {source}", parent_frame)
    source_label.setStyleSheet("color: blue; text-decoration: underline; cursor: pointer;")
    source_label.mousePressEvent = lambda event: open_link(source)
    layout.addWidget(source_label)

def clear_and_display_story(content_frame, story, sentiment_frame):
    global is_content_active
    is_content_active = False  # Deactivate current content

    for widget in content_frame.children():
        widget.deleteLater()
    for widget in sentiment_frame.children():
        widget.deleteLater()

    is_content_active = True  # Activate new content

    try:
        display_story_card(story, content_frame, sentiment_frame)
    except Exception as e:
        logging.error(f"Error displaying story: {e}")

def fade_in_story(content_frame, story, sentiment_frame):
    """
    Fades in the story when displayed and calls sentiment analysis.
    
    Args:
        content_frame (QWidget): Frame where the story is to be displayed.
        story (dict): The story to be displayed.
        sentiment_frame (QWidget): Frame to display the sentiment analysis result.
    """
    logging.info(f"Displaying story: {story.get('title', 'No title available')}")

    # First, clear the previous story content and then display the new story.
    clear_and_display_story(content_frame, story, sentiment_frame)

    # Create a fade-in effect by gradually increasing the opacity.
    fade_frame = QWidget(content_frame)
    fade_frame.setStyleSheet("background-color: black;")
    fade_frame.setWindowOpacity(0.0)
    fade_frame.show()

    def fade(step=0):
        """Helper function to gradually increase the opacity."""
        if step <= 1.0:
            fade_frame.setWindowOpacity(step)
            QTimer.singleShot(50, lambda: fade(step + 0.05))  # Increase opacity in small steps

    fade()  # Start the fade-in process
