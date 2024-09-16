"""
ui/gui.py

This module defines the main graphical user interface (GUI) for the StreamPulse application.
It sets up the main frame, including the layout of news categories, stories, stock ticker, and global statistics.
Integrates with story display, sentiment analysis, and stock ticker modules to handle story transitions,
narration, and stock updates.

Key Features:
- Displays a 3x2 grid of news categories.
- Cycles through stories in each category, narrating one story at a time.
- Integrates sentiment and bias analysis for each story using Ollama.
- Displays a stock ticker at the bottom of the screen.
- Provides global statistics such as U.S. National Debt and CO2 emissions.
- Displays a live world clock.

Functions:
- setup_main_frame: Initializes the main GUI and layout.
- display_news_stories: Displays stories in a grid of categories.
- rotate_through_categories: Handles automatic story rotation and narration.
"""

import logging
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget, QGridLayout, QMainWindow
from PyQt5.QtCore import QTimer
from ui.story_display import create_story_card, clear_widgets
from api.sentiment import analyze_text
from api.tts_engine import add_to_tts_queue
from ui.stock_ticker import StockTicker
from ui.stats_widgets import create_global_stats_widget, create_world_clock_widget

# Set up logging
logging.basicConfig(level=logging.INFO)

class MainWindow(QMainWindow):
    def __init__(self, feeds_data, stock_data):
        super().__init__()
        self.setWindowTitle("StreamPulse News")
        self.setStyleSheet("background-color: #2c3e50; color: white;")
        self.feeds_data = feeds_data  # RSS feeds data loaded in loading_screen.py
        self.stock_data = stock_data  # Stock data loaded in loading_screen.py
        self.current_category = 0  # To track which category we're currently displaying
        self.current_story_index = {}  # To track the current story index for each category

        # Initialize the main layout
        self.setup_main_frame()

    def setup_main_frame(self):
        """
        Sets up the main layout of the application, including the 3x2 grid of news categories,
        stock ticker, global statistics, and world clock.
        """
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Main layout with sidebar for stats and clock
        self.main_layout = QHBoxLayout(self.central_widget)

        # Left-side layout for news grid and stock ticker
        left_layout = QVBoxLayout()
        self.main_layout.addLayout(left_layout)

        # Create a grid layout for the news categories
        self.news_grid_layout = QGridLayout()
        self.news_grid_frame = QFrame(self.central_widget)
        self.news_grid_frame.setLayout(self.news_grid_layout)
        left_layout.addWidget(self.news_grid_frame)

        # Create label to show sentiment analysis below the news grid
        self.sentiment_label = QLabel("Sentiment Analysis: Loading...", self.central_widget)
        self.sentiment_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding: 10px;")
        left_layout.addWidget(self.sentiment_label)

        # Add the stock ticker at the bottom
        self.stock_ticker = StockTicker(self.central_widget)
        left_layout.addWidget(self.stock_ticker)

        # Right-side layout for global stats and clock
        right_layout = QVBoxLayout()
        self.main_layout.addLayout(right_layout)

        # Add global statistics widget
        global_stats_widget = create_global_stats_widget()
        right_layout.addWidget(global_stats_widget)

        # Add world clock widget
        world_clock_widget = create_world_clock_widget()
        right_layout.addWidget(world_clock_widget)

        # Populate the news grid with initial stories
        self.update_news_grid()

        # Start rotating through categories
        self.rotate_through_categories()

    def update_news_grid(self):
        """
        Updates the grid layout by populating it with story cards.
        """
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

    def display_news_stories(self):
        """
        Displays stories in each category's grid slot. Cycles through stories for each category.
        """
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
        stories = self.feeds_data.get(category, {}).get("entries", [])  # Ensure we're accessing 'entries'
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
        add_to_tts_queue(f"Reading story from {category}: {headline}")

        # Perform sentiment analysis and display result
        analyze_text(story.get("description", ""), self.news_grid_frame, self.sentiment_label)

        # Move to the next story in the category
        self.current_story_index[category] = (story_index + 1) % len(stories)

    def rotate_through_categories(self):
        """
        Rotates through the news categories, displaying one story at a time from each category.
        """
        categories = list(self.feeds_data.keys())

        if not categories:
            logging.error("No categories available for rotation.")
            return

        # Rotate to the next category
        self.current_category = (self.current_category + 1) % len(categories)
        
        # Display stories in the new category
        self.display_news_stories()

        # Set a timer to rotate to the next category after 10 seconds
        QTimer.singleShot(10000, self.rotate_through_categories)
