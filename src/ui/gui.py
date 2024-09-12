import os
import logging
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame, QGridLayout, QWidget, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt
from api.fetchers import FetchStockData  # Import the stock data fetching class
from ui.stats_widgets import create_global_stats_widget, create_world_clock_widget
from ui.stock_ticker import create_stock_ticker_widget

def setup_main_frame(root):
    """
    Sets up the main GUI layout for the StreamPulse application.

    Args:
        root (QWidget): The main window or parent widget for the application.

    Returns:
        QWidget: The central widget containing the main frame layout.
    """
    logging.debug("Setting up main frame...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    bg_image_path = os.path.join(project_root, 'images', 'bg.png')

    central_widget = QWidget(root)
    root.setCentralWidget(central_widget)

    layout = QGridLayout(central_widget)
    layout.setSpacing(20)  # Adjusted for better spacing

    # Load the background image
    load_background_image(central_widget, layout, bg_image_path)

    # Create the news sections
    create_news_sections(layout, root)

    # Add the stats, clock, and other widgets
    add_stats_and_clock_widgets(layout, central_widget)

    # Stock ticker at the bottom, spanning across the full window width
    stock_ticker_frame = create_stock_ticker_widget()
    stock_ticker_frame.setFixedHeight(50)  # Adjust height for better visibility
    stock_ticker_frame.setStyleSheet("""
        background-color: rgba(0, 0, 0, 0.8); 
        border-radius: 5px;
        color: white;
        font-size: 16px;
    """)  # Ensure it has high contrast
    layout.addWidget(stock_ticker_frame, 5, 0, 1, 6, alignment=Qt.AlignBottom)  # Anchored at the bottom

    # Ensure the stock ticker is always at the bottom
    layout.setRowStretch(4, 1)

    # Initialize stock data fetching and connect the signal
    fetch_stock_data(stock_ticker_frame)

    logging.debug("Main frame setup complete.")
    return central_widget

def load_background_image(central_widget, layout, bg_image_path):
    """
    Loads the background image and applies it to the main layout.

    Args:
        central_widget (QWidget): The central widget for the background image.
        layout (QGridLayout): The layout to add the background image.
        bg_image_path (str): The file path to the background image.

    Returns:
        None
    """
    if os.path.exists(bg_image_path):
        try:
            bg_image = QPixmap(bg_image_path)
            bg_label = QLabel(central_widget)
            bg_label.setPixmap(bg_image)
            bg_label.setScaledContents(True)
            layout.addWidget(bg_label, 0, 0, 5, 6)  # Span across the entire grid
            logging.info("Background image loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading background image: {e}")
            central_widget.setStyleSheet("background-color: #2c3e50;")
    else:
        central_widget.setStyleSheet("background-color: #2c3e50;")

def apply_shadow_effect(widget):
    """
    Applies a shadow effect to a given widget.

    Args:
        widget (QWidget): The widget to which the shadow effect is applied.

    Returns:
        None
    """
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setXOffset(5)
    shadow.setYOffset(5)
    shadow.setColor(QColor(0, 0, 0, 160))
    widget.setGraphicsEffect(shadow)

def create_news_sections(layout, root):
    """
    Creates the news section widgets and adds them to the layout.

    Args:
        layout (QGridLayout): The layout to add the news section frames.
        root (QWidget): The main window or parent widget.

    Returns:
        None
    """
    categories = [
        ("General", "general"),
        ("Financial", "financial"),
        ("Video Games", "video_games"),
        ("Science & Tech", "science_tech"),
        ("Health & Environment", "health_environment"),
        ("Entertainment", "entertainment"),
    ]

    for i, (category_name, internal_category) in enumerate(categories):
        section_frame = QFrame(root)
        section_frame.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            color: white;
        """)
        apply_shadow_effect(section_frame)
        section_frame.setFixedSize(320, 180)

        layout.addWidget(section_frame, i // 3, i % 3, alignment=Qt.AlignTop)

        label = QLabel(f"{category_name} News", section_frame)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #ecf0f1;
            padding-bottom: 5px;
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #3498db, stop: 1 #2ecc71);
            border-radius: 5px;
        """)

        content_layout = QVBoxLayout(section_frame)
        content_layout.addWidget(label)

        content_frame = QWidget(section_frame)
        content_layout.addWidget(content_frame)

        sentiment_frame = QWidget(section_frame)
        content_layout.addWidget(sentiment_frame)

def add_stats_and_clock_widgets(layout, central_widget):
    """
    Adds the statistics and clock widgets to the layout.

    Args:
        layout (QGridLayout): The layout to add the statistics and clock widgets.
        central_widget (QWidget): The main parent widget.

    Returns:
        None
    """
    stats_clock_frame = QFrame(central_widget)
    stats_clock_frame.setStyleSheet("""
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
    """)
    apply_shadow_effect(stats_clock_frame)

    stats_clock_layout = QVBoxLayout(stats_clock_frame)
    stats_clock_frame.setFixedWidth(320)  # Restrict width to 320
    layout.addWidget(stats_clock_frame, 0, 3, 2, 1)

    stats_clock_layout.addWidget(create_global_stats_widget())
    stats_clock_layout.addWidget(create_world_clock_widget())

def fetch_stock_data(stock_ticker_frame):
    """
    Starts fetching stock data and connects it to the stock ticker widget.

    Args:
        stock_ticker_frame (QWidget): The stock ticker widget frame that will display the stock data.

    Returns:
        None
    """
    # Create a FetchStockData thread and connect the signal to the stock ticker
    fetch_stock_thread = FetchStockData()
    stock_ticker = stock_ticker_frame.findChild(QWidget, None)
    fetch_stock_thread.stock_data_signal.connect(stock_ticker.set_ticker_text)

    # Start fetching the stock data
    fetch_stock_thread.start()
