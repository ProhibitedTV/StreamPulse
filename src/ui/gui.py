"""
gui.py

This module sets up the main graphical user interface (GUI) for the StreamPulse application. 
It organizes various sections of the application window, including the news story display, 
global statistics, and a stock ticker. The interface dynamically displays content based on 
RSS feed data and stock market prices retrieved from external sources.

Key Functions:
    - setup_main_frame: Sets up the main layout of the application, organizing the news 
      stories, stats sidebar, and stock ticker.
    - create_header_frame: Builds the header section containing the app logo and live time.
    - create_footer_ticker: Displays a scrolling ticker with live stock prices.
    - format_stock_data: Formats the stock data for the ticker display.
    - display_news_stories: Displays news stories from the loaded RSS feeds.

Dependencies:
    - PyQt5 for UI components and layouts.
    - Other UI modules such as stats_widgets, stock_ticker, and story_display.
    - Logging for tracking application events and errors.

This module is tightly integrated with the loading screen and fetchers to ensure that 
the data loaded is displayed in an interactive and dynamic interface.
"""

import logging
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QScrollArea, QDesktopWidget
from PyQt5.QtCore import Qt
from ui.stats_widgets import create_global_stats_widget, create_world_clock_widget
from ui.stock_ticker import StockTicker
from ui.story_display import clear_and_display_story
from PyQt5.QtGui import QFont

# Set up basic logging
logging.basicConfig(level=logging.INFO)


def setup_main_frame(window, feeds_data, stock_data):
    """
    Sets up the main frame of the application, organizing different sections for news,
    global stats, a world clock, and a stock ticker.
    
    Args:
        window (QMainWindow): The main application window.
        feeds_data (dict): The RSS feeds data loaded from loading_screen.py.
        stock_data (dict): Stock price data loaded from loading_screen.py.
    """
    logging.info("Setting up main frame layout...")

    # Get screen dimensions
    screen_geometry = QDesktopWidget().availableGeometry(window)
    screen_width = screen_geometry.width()
    screen_height = screen_geometry.height()

    # Central widget that holds all the layout
    central_widget = QWidget(window)
    window.setCentralWidget(central_widget)
    
    # Set maximum size for the central widget to avoid overflow
    central_widget.setMaximumSize(screen_width, screen_height)

    # Main layout for the application
    main_layout = QVBoxLayout(central_widget)
    central_widget.setStyleSheet("background-color: #1e1e1e;")  # Darker background for a modern look

    # HEADER: Logo + Live Time
    header_frame = create_header_frame(window)
    if header_frame.layout() is None:
        header_frame.setLayout(QHBoxLayout())  # Ensure layout is only set once
    main_layout.addWidget(header_frame)

    # MAIN CONTENT: News Stories and Sidebar
    content_layout = QHBoxLayout()

    # News stories section (with scroll area for multiple stories)
    news_scroll = QScrollArea()
    news_section = QFrame()
    news_section.setStyleSheet("background-color: rgba(34, 34, 34, 0.8); border: 1px solid #333; padding: 20px; border-radius: 15px;")
    news_scroll.setWidgetResizable(True)
    news_scroll.setWidget(news_section)

    if news_section.layout() is None:
        news_section.setLayout(QVBoxLayout())  # Check and set layout

    # Set a maximum width for the news section to avoid it being too wide
    news_section.setMaximumWidth(screen_width // 2)  # Limit to half the screen width

    content_layout.addWidget(news_scroll, stretch=2)

    # Display the news stories from feeds_data using story_display
    display_news_stories(news_section, feeds_data)

    # Right Sidebar: Stats + World Clock
    sidebar_layout = QVBoxLayout()

    # Global Stats Widget
    global_stats = create_global_stats_widget()
    sidebar_layout.addWidget(global_stats)

    # World Clock Widget
    world_clock = create_world_clock_widget()
    sidebar_layout.addWidget(world_clock)

    sidebar_frame = QFrame()
    sidebar_frame.setLayout(sidebar_layout)
    sidebar_frame.setStyleSheet("background-color: rgba(28, 28, 28, 0.8); padding: 20px; border-left: 1px solid #333; border-radius: 15px;")
    
    # Set a maximum width for the sidebar to control its size
    sidebar_frame.setMaximumWidth(screen_width // 4)  # Limit sidebar to 1/4th of the screen

    if sidebar_frame.layout() is None:
        sidebar_frame.setLayout(sidebar_layout)  # Ensure the sidebar layout is set only once
    
    content_layout.addWidget(sidebar_frame, stretch=1)

    main_layout.addLayout(content_layout)

    # FOOTER: Scrolling Ticker for Stock Data
    stock_ticker_widget = create_footer_ticker(stock_data)
    if stock_ticker_widget.layout() is None:
        stock_ticker_widget.setLayout(QVBoxLayout())  # Ensure layout is set
    main_layout.addWidget(stock_ticker_widget)

    window.showFullScreen()


def create_header_frame(window):
    """
    Creates the header bar that contains the app logo and the current time.
    It mimics a cable news-style header.

    Args:
        window (QMainWindow): The main application window.

    Returns:
        QFrame: The header frame.
    """
    header_frame = QFrame()
    header_layout = QHBoxLayout(header_frame)
    header_frame.setStyleSheet("background-color: rgba(153, 0, 0, 0.9); padding: 10px; border-bottom: 2px solid #111;")

    # Logo
    logo_label = QLabel("StreamPulse")
    logo_label.setFont(QFont("Helvetica", 28, QFont.Bold))
    logo_label.setStyleSheet("color: white; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);")
    header_layout.addWidget(logo_label, alignment=Qt.AlignLeft)

    return header_frame


def create_footer_ticker(stock_data):
    """
    Creates the footer ticker that displays scrolling stock prices.

    Args:
        stock_data (dict): Stock price data to display in the ticker.

    Returns:
        StockTicker: The StockTicker widget with stock data.
    """
    footer_frame = QFrame()
    footer_frame.setStyleSheet("background-color: rgba(23, 162, 184, 0.8); padding: 0px; margin: 0px; border-radius: 5px;")

    footer_layout = QVBoxLayout(footer_frame)
    stock_ticker = StockTicker(footer_frame)  # Correct instance of StockTicker
    ticker_text = format_stock_data(stock_data)
    stock_ticker.set_ticker_text(ticker_text)  # Populate ticker with live stock data

    footer_layout.addWidget(stock_ticker)

    return footer_frame


def format_stock_data(stock_data):
    """
    Formats the stock data for the ticker text.

    Args:
        stock_data (dict): Dictionary of stock symbols and their current prices.

    Returns:
        str: Formatted string for the ticker text.
    """
    ticker_text = ""
    for symbol, price in stock_data.items():
        ticker_text += f"{symbol}: {price} | "
    return ticker_text.strip(" | ")


def display_news_stories(news_section, feeds_data):
    """
    Displays news stories from feeds_data in the news section.
    Args:
        news_section (QWidget): The section to display the stories.
        feeds_data (dict): The parsed RSS feed data.
    """
    logging.info("Displaying news stories...")

    for url, feed in feeds_data.items():
        # Get entries from the feed
        for entry in feed.get('entries', []):
            story = {
                "title": entry.get("title", "No Title"),
                "description": entry.get("description", "No Description"),
                "link": entry.get("link", "#"),
                "media_content": entry.get("media_content", [{}])
            }
            # Use a method to render the story (e.g., a card or text)
            clear_and_display_story(news_section, story)

    news_section.update()