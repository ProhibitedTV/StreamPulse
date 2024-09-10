import os
import logging
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame, QGridLayout, QWidget, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt

from ui.stats_widgets import create_global_stats_widget, create_world_clock_widget
from ui.stock_ticker import create_stock_ticker_widget
from ui.feed_manager import update_feed

def setup_main_frame(root):
    """
    Sets up the main GUI layout for the StreamPulse application.

    Args:
        root (QWidget): The main window or parent widget for the application.
    """
    logging.debug("Setting up main frame...")

    # Get the absolute path of the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    bg_image_path = os.path.join(project_root, 'images', 'bg.png')

    central_widget = QWidget(root)
    root.setCentralWidget(central_widget)
    layout = QGridLayout(central_widget)
    layout.setSpacing(20)  # Increased spacing for better visuals
    logging.debug("Grid layout for central widget created.")

    # Load and set the background image if available
    load_background_image(central_widget, layout, bg_image_path)

    # Create the news sections
    logging.info("Creating news sections.")
    create_news_sections(layout, root)

    # Add global stats and world clock widgets
    logging.info("Adding global stats and world clock widgets.")
    add_stats_and_clock_widgets(layout, central_widget)

    # Create and add the stock ticker frame at the bottom
    logging.debug("Creating stock ticker frame.")
    stock_ticker_frame = create_stock_ticker_widget()
    layout.addWidget(stock_ticker_frame, 4, 0, 1, 4)
    logging.info("Stock ticker frame created.")

    logging.debug("Main frame setup complete.")
    return central_widget

def load_background_image(central_widget, layout, bg_image_path):
    """
    Loads the background image for the main frame. If not found, sets a default background color.

    Args:
        central_widget (QWidget): The main widget where the background is set.
        layout (QGridLayout): The layout where the background is added.
        bg_image_path (str): The file path to the background image.
    """
    if os.path.exists(bg_image_path):
        try:
            logging.debug(f"Loading background image from {bg_image_path}")
            bg_image = QPixmap(bg_image_path)
            bg_label = QLabel(central_widget)
            bg_label.setPixmap(bg_image)
            bg_label.setScaledContents(True)
            bg_label.setStyleSheet("opacity: 0.85;")  # Increased transparency for visibility of content
            layout.addWidget(bg_label, 0, 0, 5, 4)  # Adjusted grid span for full-screen background
            logging.info("Background image loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading background image: {e}")
            central_widget.setStyleSheet("background-color: #2c3e50;")  # Dark fallback color
    else:
        logging.error(f"Background image not found at path: {bg_image_path}")
        central_widget.setStyleSheet("background-color: #2c3e50;")

def apply_shadow_effect(widget):
    """
    Applies a subtle shadow effect to a widget for a modern, floating appearance.
    
    Args:
        widget (QWidget): The widget to apply the shadow to.
    """
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setXOffset(5)
    shadow.setYOffset(5)
    shadow.setColor(QColor(0, 0, 0, 160))
    widget.setGraphicsEffect(shadow)

def create_news_sections(layout, root):
    """
    Dynamically creates news sections for different categories and adds them to the layout.

    Args:
        layout (QGridLayout): The layout to which the sections are added.
        root (QWidget): The parent widget for the sections.
    """
    logging.debug("Creating news sections.")
    
    categories = [
        ("General", "general"),
        ("Financial", "financial"),
        ("Video Games", "video_games"),
        ("Science & Tech", "science_tech"),
        ("Health & Environment", "health_environment"),
        ("Entertainment", "entertainment"),
    ]

    for i, (category_name, internal_category) in enumerate(categories):
        logging.debug(f"Setting up section for {category_name}.")
        section_frame = QFrame(root)
        section_frame.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            color: white;
        """)
        apply_shadow_effect(section_frame)  # Add shadow effect for modern card look

        layout.addWidget(section_frame, i // 3, i % 3, 1, 1)

        label = QLabel(f"{category_name} News", section_frame)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #ecf0f1;
            padding-bottom: 10px;
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #3498db, stop: 1 #2ecc71);
            border-radius: 5px;
        """)

        content_layout = QVBoxLayout(section_frame)
        content_layout.addWidget(label)

        content_frame = QWidget(section_frame)
        content_layout.addWidget(content_frame)

        sentiment_frame = QWidget(section_frame)
        content_layout.addWidget(sentiment_frame)

        logging.info(f"Starting feed update for {category_name}.")
        update_feed([], content_frame, root, f"{category_name} News", sentiment_frame)
        logging.debug(f"Finished setup for {category_name} section.")

def add_stats_and_clock_widgets(layout, central_widget):
    """
    Adds the global statistics and world clock widgets to the layout.

    Args:
        layout (QGridLayout): The layout to which the widgets are added.
        central_widget (QWidget): The parent widget where the widgets are placed.
    """
    stats_clock_frame = QFrame(central_widget)
    stats_clock_frame.setStyleSheet("""
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
    """)
    apply_shadow_effect(stats_clock_frame)  # Apply shadow to stats/clock frame

    stats_clock_layout = QVBoxLayout(stats_clock_frame)
    layout.addWidget(stats_clock_frame, 0, 3, 2, 1)  # Placed in the right corner for balance

    # Add global stats and world clock widgets
    stats_clock_layout.addWidget(create_global_stats_widget())
    stats_clock_layout.addWidget(create_world_clock_widget())

    logging.debug("Global stats and world clock widgets added.")
