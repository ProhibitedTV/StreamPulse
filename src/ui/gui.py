"""
ui/gui.py

This module defines the main graphical user interface (GUI) for the StreamPulse application.
It is responsible for rendering and managing the layout of various dynamic content such as news categories,
a stock ticker, global statistics, sentiment analysis, and a world clock.

Key Features:
- Initializes and sets up the main window for displaying a 3x2 grid of news categories.
- Integrates sentiment analysis and text-to-speech (TTS) functionality for the news stories.
- Displays additional dynamic widgets like a stock ticker, global statistics, and world clock.
- Handles the automatic rotation of news categories and story transitions.
- Manages error handling for missing or invalid content from RSS feeds.

Classes:
- MainWindow: The main class that manages the GUI components, including news stories, stock data, 
  and widgets such as sentiment analysis and the stock ticker.

Functions:
- setup_main_frame: Sets up the primary layout, including the news grid, stock ticker, global stats, 
  sentiment analysis, and world clock.
- update_news_grid: Updates the grid with story cards populated with headlines, descriptions, and images.
- display_news_stories: Cycles through stories in each category, integrates sentiment analysis, 
  and updates the TTS engine.
- rotate_through_categories: Rotates between different news categories and automatically refreshes stories.
"""

import logging
import asyncio
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget, QGridLayout, QMainWindow, QSizePolicy, QScrollArea, QTextEdit, QProgressBar
from PyQt5.QtCore import QTimer
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
    a stock ticker, and widgets like global stats, sentiment analysis, and a world clock.
    """
    def __init__(self, feeds_data, stock_data):
        super().__init__()
        self.setWindowTitle("StreamPulse News")
        self.setFixedSize(1920, 1080)  # Ensure window fits within 1080p display
        self.setStyleSheet("""
            background-color: #2c3e50; color: white;
            QFrame { background-color: #34495e; border-radius: 10px; }
            QLabel { color: #ecf0f1; }
        """)
        self.feeds_data = feeds_data  # RSS feeds data loaded in loading_screen.py
        self.stock_data = stock_data  # Stock data loaded in loading_screen.py
        self.current_story_index = {}  # To track the current story index for each category
        self.progress_timers = {}  # Store progress timers for each category

        # Initialize the main layout
        self.news_grid_layout = None  # Ensure layout is defined
        self.story_widgets = {}  # Store the story widgets to update later
        self.setup_main_frame()

    def setup_main_frame(self):
        """
        Sets up the main layout of the application, including the 3x2 grid of news categories,
        stock ticker, global statistics, sentiment analysis, and world clock.
        """
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Main layout with sidebar for stats, sentiment, and clock
        self.main_layout = QVBoxLayout(self.central_widget)  # Use vertical layout for main screen
        content_layout = QHBoxLayout()  # Content section layout (left: news grid, right: stats)

        # Left-side layout for news grid
        left_layout = QVBoxLayout()
        content_layout.addLayout(left_layout, stretch=3)  # Add stretch to control layout space

        # Create a grid layout for the news categories
        self.news_grid_layout = QGridLayout()
        self.news_grid_frame = QFrame(self.central_widget)
        self.news_grid_layout.setSpacing(15)
        self.news_grid_frame.setLayout(self.news_grid_layout)
        left_layout.addWidget(self.news_grid_frame)

        # Right-side layout for global stats, sentiment analysis, and world clock
        right_layout = QVBoxLayout()
        content_layout.addLayout(right_layout, stretch=1)  # Smaller stretch for the right layout

        # Add global statistics widget
        global_stats_widget = create_global_stats_widget()
        right_layout.addWidget(global_stats_widget)

        # Add world clock widget
        world_clock_widget = create_world_clock_widget()
        right_layout.addWidget(world_clock_widget)

        # Create a scrollable area for the sentiment widget
        scroll_area = QScrollArea(self.central_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")  # Remove border for clean look

        # Add a text box inside the scrollable area for the sentiment analysis
        self.sentiment_label = QTextEdit("Sentiment Analysis: Loading...", self.central_widget)
        self.sentiment_label.setStyleSheet("""
            font-size: 18px; font-weight: bold; padding: 15px; color: #3498db; 
            background-color: #34495e; border-radius: 8px;
        """)
        self.sentiment_label.setReadOnly(True)  # Make the text box read-only

        scroll_area.setWidget(self.sentiment_label)  # Add the text box to the scroll area
        right_layout.addWidget(scroll_area)

        # Add the content layout (left and right) to the main layout
        self.main_layout.addLayout(content_layout)

        # Stock ticker, positioned at the bottom and stretched across both left and right layouts
        self.stock_ticker = create_stock_ticker_widget(self.stock_data)
        self.stock_ticker.setFixedHeight(40)  # Adjust stock ticker height
        self.stock_ticker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Ensure ticker spans full width
        self.main_layout.addWidget(self.stock_ticker)  # Add the stock ticker to the main layout

        # Populate the news grid with initial stories
        asyncio.ensure_future(self.update_news_grid())

        # Start rotating through stories in each category
        self.rotate_stories()
        
    def start_progress_bar(self, progress_bar, category, duration_seconds):
        """
        Starts updating the progress bar over the given duration (in seconds).
        This function increments the progress bar at regular intervals.
        """
        progress_bar.setRange(0, 100)  # Set progress range from 0 to 100
        progress_bar.setValue(0)  # Initialize progress bar at 0%
        progress_interval = 1000  # Update every 1000 ms (1 second)

        # Calculate how much progress to make per interval
        increment = 100 / duration_seconds

        def update_progress():
            current_value = progress_bar.value()
            new_value = current_value + increment
            if new_value >= 100:
                progress_bar.setValue(100)
            else:
                progress_bar.setValue(new_value)

        # Stop any existing timer for this category
        if category in self.progress_timers:
            self.progress_timers[category].stop()

        # Use a QTimer to update the progress bar every interval
        progress_timer = QTimer(self)
        progress_timer.timeout.connect(update_progress)
        progress_timer.start(progress_interval)

        # Store the new timer for this category
        self.progress_timers[category] = progress_timer

    async def update_news_grid(self):
        """
        Updates the grid layout by populating it with story cards.
        Only one story per category will be displayed at a time.
        """
        if self.news_grid_layout is None:
            logging.error("News grid layout not initialized.")
            return

        categories = list(self.feeds_data.keys())
        if not categories:
            logging.warning("No categories available to display.")
            return

        logging.info("Clearing existing widgets from the grid layout.")
        clear_widgets(self.news_grid_frame)  # Clear any existing widgets

        row, col = 0, 0
        max_columns = 2  # Limit to 2 columns in the grid

        # Iterate through categories and fetch stories
        for category in categories:
            feeds = self.feeds_data.get(category, [])
            if not isinstance(feeds, list):
                logging.error(f"Feeds for category {category} are not a list: {feeds}")
                continue  # Skip if the structure isn't valid

            stories = []
            for feed_dict in feeds:
                feed_data = feed_dict.get('feed', {})
                if not isinstance(feed_data, dict):
                    logging.error(f"Feed data for URL {feed_dict.get('url')} is not a dictionary: {feed_data}")
                    continue  # Skip this feed
                stories.extend(feed_data.get('entries', []))

            if not stories:
                logging.warning(f"No stories found for category: {category}")
                continue

            # Set up initial story index and display the first story
            self.current_story_index[category] = 0
            story_card, progress_bar = await create_story_card(stories[0], category, self.news_grid_frame)
            story_card.setFixedSize(580, 280)

            # Add the story card to the grid layout
            self.news_grid_layout.addWidget(story_card, row, col)

            # Store the widget reference for later updates
            self.story_widgets[category] = (story_card, stories, progress_bar)

            # Start progress bar for the first story
            self.start_progress_bar(progress_bar, category, 30)

            # Update row and col for grid layout
            col += 1
            if col >= max_columns:  # Move to next row after max columns
                col = 0
                row += 1

    def rotate_stories(self):
        """
        Rotates through the stories in each category every 30 seconds.
        """
        async def update_story_card(category, story_card, stories, progress_bar):
            # Stop the current progress bar timer for this category
            if category in self.progress_timers:
                self.progress_timers[category].stop()

            # Update the story index for the category
            current_index = self.current_story_index.get(category, 0)
            next_index = (current_index + 1) % len(stories)
            self.current_story_index[category] = next_index

            # Clear the current story card and update with the next story
            clear_widgets(story_card)
            new_story_card, new_progress_bar = await create_story_card(stories[next_index], category, story_card)
            story_card.layout().addWidget(new_story_card)

            # Start the progress bar for this story
            self.start_progress_bar(new_progress_bar, category, 30)  # 30 seconds per story

        async def rotate_all_stories():
            tasks = []
            for category, (story_card, stories, progress_bar) in self.story_widgets.items():
                # For each category, update the story card asynchronously
                tasks.append(update_story_card(category, story_card, stories, progress_bar))
            await asyncio.gather(*tasks)

            # Rotate stories again after 30 seconds
            QTimer.singleShot(30000, self.rotate_stories)

        # Start the rotation
        asyncio.ensure_future(rotate_all_stories())
