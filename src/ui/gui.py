"""
ui/gui.py

This module defines the main graphical user interface (GUI) for the StreamPulse application.
It handles the layout and display of news categories, stock ticker, global statistics, and other
dynamic content such as sentiment and bias analysis.

Key Features:
- Sets up the main window with a layout that includes a 3x2 grid of news categories.
- Handles automatic story transitions and integrates sentiment analysis via Ollama.
- Displays dynamic widgets like a stock ticker, global statistics, and a world clock.
- Ensures the layout exists and fits within a 1080p display.

Classes:
- MainWindow: The main interface class that manages the display and layout of news, stock updates, 
  and other widgets.

Functions:
- setup_main_frame: Initializes the main GUI layout and ensures it fits within 1080p.
- update_news_grid: Updates the grid with news stories once data is loaded.
- display_news_stories: Cycles through stories in each category and performs sentiment analysis.
- rotate_through_categories: Rotates between news categories, triggering story updates.
"""

import logging
import asyncio
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget, QGridLayout, QMainWindow, QSizePolicy
from PyQt5.QtCore import QTimer, QSize
from ui.story_display import create_story_card, clear_widgets
from api.sentiment import analyze_text
from api.tts_engine import add_to_tts_queue
from ui.stock_ticker import create_stock_ticker_widget
from ui.stats_widgets import create_global_stats_widget, create_world_clock_widget

# Set up logging
logging.basicConfig(level=logging.INFO)

class MainWindow(QMainWindow):
    """
    MainWindow is the main graphical interface for StreamPulse. It displays the news categories,
    a stock ticker, and widgets like global stats and a world clock.
    """
    def __init__(self, feeds_data, stock_data):
        super().__init__()
        self.setWindowTitle("StreamPulse News")
        self.setFixedSize(1920, 1080)  # Ensure window fits within 1080p display
        self.setStyleSheet("background-color: #2c3e50; color: white;")
        self.feeds_data = feeds_data  # RSS feeds data loaded in loading_screen.py
        self.stock_data = stock_data  # Stock data loaded in loading_screen.py
        self.current_category = 0  # To track which category we're currently displaying
        self.current_story_index = {}  # To track the current story index for each category

        # Initialize the main layout
        self.news_grid_layout = None  # Ensure layout is defined
        self.setup_main_frame()

    def setup_main_frame(self):
        """
        Sets up the main layout of the application, including the 3x2 grid of news categories,
        stock ticker, global statistics, and world clock.
        Ensures the layout fits within 1080p and widgets are properly sized.
        """
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Main layout with sidebar for stats and clock
        self.main_layout = QHBoxLayout(self.central_widget)

        # Left-side layout for news grid and stock ticker
        left_layout = QVBoxLayout()
        self.main_layout.addLayout(left_layout, stretch=3)  # Add stretch to control layout space

        # Create a grid layout for the news categories
        self.news_grid_layout = QGridLayout()
        self.news_grid_frame = QFrame(self.central_widget)
        self.news_grid_frame.setLayout(self.news_grid_layout)
        left_layout.addWidget(self.news_grid_frame)

        # Create label to show sentiment analysis below the news grid
        self.sentiment_label = QLabel("Sentiment Analysis: Loading...", self.central_widget)
        self.sentiment_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; padding: 8px;")
        left_layout.addWidget(self.sentiment_label)

        # Add the stock ticker at the bottom, adjust height, and pass the stock data to it
        self.stock_ticker = create_stock_ticker_widget(self.stock_data)
        self.stock_ticker.setFixedHeight(50)  # Make the stock ticker height smaller
        left_layout.addWidget(self.stock_ticker)

        # Right-side layout for global stats and clock
        right_layout = QVBoxLayout()
        self.main_layout.addLayout(right_layout, stretch=1)  # Smaller stretch for the right layout

        # Add global statistics widget
        global_stats_widget = create_global_stats_widget()
        right_layout.addWidget(global_stats_widget)

        # Add world clock widget
        world_clock_widget = create_world_clock_widget()
        right_layout.addWidget(world_clock_widget)

        # Ensure the stock ticker extends across the bottom of both layouts
        self.stock_ticker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Populate the news grid with initial stories
        self.update_news_grid()

        # Start rotating through categories
        self.rotate_through_categories()

    def update_news_grid(self):
        """
        Updates the grid layout by populating it with story cards.
        This is triggered after the news data is loaded.
        Ensures layout exists before modifying it.
        """
        if self.news_grid_layout is None:
            logging.error("News grid layout not initialized.")
            return

        categories = list(self.feeds_data.keys())
        
        if not categories:
            logging.warning("No categories available to display.")
            return
        
        # Clear the grid first
        clear_widgets(self.news_grid_frame)

        # Populate the grid with story cards from each category
        row, col = 0, 0
        for category in categories[:6]:  # Limit to 6 categories (3 rows x 2 columns)
            stories = self.feeds_data.get(category, {}).get("entries", [])
            if stories:
                # Create a story card for the first story in each category
                story_card = create_story_card(stories[0], self.news_grid_frame)
                self.news_grid_layout.addWidget(story_card, row, col)
                col += 1
                if col > 1:  # Move to the next row after 2 columns
                    col = 0
                    row += 1

    async def display_news_stories(self):
        """
        Displays stories in each category's grid slot. Cycles through stories for each category.
        Ensures the layout exists before accessing it. Asynchronous to leverage async analyze_text.
        """
        if self.news_grid_layout is None:
            logging.error("News grid layout is not initialized.")
            return

        categories = list(self.feeds_data.keys())
        
        if not categories:
            logging.error("No categories found in feed data.")
            return

        # Select a story to perform sentiment analysis
        category = categories[self.current_category]

        # Initialize the current story index if not already set
        if category not in self.current_story_index:
            self.current_story_index[category] = 0

        # Get the list of stories for the current category
        stories = self.feeds_data.get(category, {}).get("entries", [])
        if not stories:
            logging.warning(f"No stories found for category: {category}")
            return

        # Get the current story for the category
        story_index = self.current_story_index[category]
        if story_index >= len(stories):
            logging.error(f"Story index {story_index} out of range for category: {category}")
            return

        story = stories[story_index]

        # Update TTS engine to narrate the story
        headline = story.get("title", "No title available")
        await add_to_tts_queue(f"Reading story from {category}: {headline}")

        # Perform sentiment analysis asynchronously and display result
        await analyze_text(story.get("description", ""), self.news_grid_frame, self.sentiment_label)

        # Move to the next story in the category
        self.current_story_index[category] = (story_index + 1) % len(stories)

    def rotate_through_categories(self):
        """
        Rotates through the news categories, displaying one story at a time from each category.
        Checks for layout existence before updating.
        """
        if self.news_grid_layout is None:
            logging.error("News grid layout is not initialized.")
            return

        categories = list(self.feeds_data.keys())

        if not categories:
            logging.error("No categories available for rotation.")
            return

        # Rotate to the next category
        self.current_category = (self.current_category + 1) % len(categories)

        # Display stories in the new category asynchronously
        asyncio.create_task(self.display_news_stories())

        # Set a timer to rotate to the next category after 10 seconds
        QTimer.singleShot(10000, self.rotate_through_categories)
