"""
ui/gui.py

This module defines the main graphical user interface (GUI) for the StreamPulse application. It is responsible for
rendering and managing the layout of dynamic content such as news stories, sentiment analysis, stock ticker,
and various widgets like global statistics and a world clock.

Key Features:
    - Displays a grid of news stories on the left side of the screen, which automatically rotates every 30 seconds.
    - Integrates with a text-to-speech (TTS) engine to provide vocal feedback based on sentiment analysis.
    - Displays sentiment analysis results on the right side of the screen, synchronized with TTS speech.
    - Handles multiple widgets including a stock ticker, global statistics, and a world clock.
    - Fetches and processes news stories from external feeds and updates the UI accordingly.
    - Allows independent rotation of story cards (left side) and sentiment analysis (right side), ensuring smooth user experience.
    - Progress bars and timers are used to visually represent the rotation of story cards.

Main Classes:
    - MainWindow: The main GUI window, responsible for initializing layouts, fetching data, and managing updates.
    
Main Functions:
    - setup_main_frame: Initializes the layout, including the news grid, sentiment widget, stock ticker, and stats widgets.
    - start_left_rotation: Rotates through story cards on the left side every 30 seconds, independent of other widgets.
    - start_right_rotation: Updates the sentiment analysis widget based on the TTS engine and story content.
    - update_news_grid: Populates the news grid with story cards fetched from external feeds.
    - get_current_sentiment_analysis: Fetches the sentiment analysis result for the currently displayed news story.
    - start_progress_bar: Manages the progress bar for each story card during its display period.

Dependencies:
    - PyQt5: For building and managing the GUI components.
    - asyncio: For handling asynchronous tasks and avoiding UI blocking.
    - TTS Engine: For integrating text-to-speech functionality.
    - api/sentiment: For performing sentiment analysis on the news stories.
    - ui/story_display: For handling the display of individual news stories.
    - ui/stock_ticker: For displaying stock prices in a ticker format.
    - ui/stats_widgets: For adding global statistics and world clock widgets.

This file manages the visual layout, real-time updates, and smooth transitions between dynamic elements in the StreamPulse application.
"""

import os
import logging
import asyncio
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QWidget, QGridLayout, QMainWindow, QSizePolicy, QScrollArea, QTextEdit
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPalette, QBrush, QPixmap
from ui.story_display import create_story_card, clear_widgets
from api.sentiment import analyze_text
from api.tts_engine import add_to_tts_queue, tts_is_speaking
from ui.stock_ticker import create_stock_ticker_widget
from ui.stats_widgets import create_global_stats_widget, create_world_clock_widget

# Set up logging
logging.basicConfig(level=logging.INFO)

class MainWindow(QMainWindow):
    def __init__(self, feeds_data, stock_data):
        super().__init__()
        self.setWindowTitle("StreamPulse News")
        self.setFixedSize(1920, 1080)

        # Set background image
        background_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../images/bg.png'))
        palette = QPalette()
        pixmap = QPixmap(background_image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
        self.setPalette(palette)

        self.feeds_data = feeds_data
        self.stock_data = stock_data
        self.current_story_index = {}
        self.progress_timers = {}
        self.story_widgets = {}  # Initialize story_widgets as an empty dictionary
        self.setup_main_frame()

    def setup_main_frame(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        content_layout = QHBoxLayout()

        # Left side (story cards)
        left_layout = QVBoxLayout()
        content_layout.addLayout(left_layout, stretch=3)

        self.news_grid_layout = QGridLayout()
        self.news_grid_frame = QFrame(self.central_widget)
        self.news_grid_layout.setSpacing(15)
        self.news_grid_frame.setLayout(self.news_grid_layout)
        left_layout.addWidget(self.news_grid_frame)

        # Right side (stats and sentiment)
        right_layout = QVBoxLayout()
        content_layout.addLayout(right_layout, stretch=1)

        global_stats_widget = create_global_stats_widget()
        right_layout.addWidget(global_stats_widget)

        world_clock_widget = create_world_clock_widget()
        right_layout.addWidget(world_clock_widget)

        scroll_area = QScrollArea(self.central_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        self.sentiment_label = QTextEdit("Sentiment Analysis: Loading...", self.central_widget)
        self.sentiment_label.setStyleSheet("""
            font-size: 18px; font-weight: bold; padding: 15px; color: #3498db; 
            background-color: #34495e; border-radius: 8px;
        """)
        self.sentiment_label.setReadOnly(True)
        scroll_area.setWidget(self.sentiment_label)
        right_layout.addWidget(scroll_area)

        self.main_layout.addLayout(content_layout)

        # Stock ticker
        self.stock_ticker = create_stock_ticker_widget(self.stock_data)
        self.stock_ticker.setFixedHeight(40)
        self.stock_ticker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.main_layout.addWidget(self.stock_ticker)

        asyncio.ensure_future(self.update_news_grid())
        self.start_left_rotation()  # Start the left side rotation
        self.start_right_rotation()  # Start the right side TTS-driven update

    def start_left_rotation(self):
        """Rotate the story cards on the left side independently every 30 seconds."""
        async def rotate_story_cards():
            tasks = []
            for category, (story_card, stories, progress_bar) in self.story_widgets.items():
                tasks.append(self.update_story_card(category, story_card, stories, progress_bar))
            await asyncio.gather(*tasks)
            QTimer.singleShot(30000, self.start_left_rotation)

        asyncio.ensure_future(rotate_story_cards())

    def start_right_rotation(self):
        """Updates the sentiment widget based on TTS queue, independently of the story card rotation."""
        async def update_sentiment():
            logging.info("Checking if TTS is speaking...")
            
            timeout = 10  # Set a timeout to prevent indefinite waiting
            time_waited = 0

            # Wait for TTS to finish speaking or timeout
            while tts_is_speaking():
                logging.info("TTS is still speaking... waiting")
                await asyncio.sleep(1)
                time_waited += 1
                if time_waited >= timeout:
                    logging.warning("Timeout reached for TTS, forcing sentiment update.")
                    break

            logging.info("TTS has finished speaking, updating sentiment widget.")

            # Fetch the current story's sentiment analysis
            try:
                story_title, sentiment_result = await self.get_current_sentiment_analysis()
                if sentiment_result:
                    self.sentiment_label.setText(f"Story: {story_title}\n\n{sentiment_result}")
                    logging.info(f"Sentiment for '{story_title}' updated: {sentiment_result}")
                else:
                    logging.warning(f"No sentiment result returned for '{story_title}'")
            except Exception as e:
                logging.error(f"Error fetching sentiment analysis: {e}")

            # Add the new sentiment to TTS queue for speaking
            try:
                if sentiment_result:
                    await add_to_tts_queue(sentiment_result)
                    logging.info(f"Sentiment added to TTS queue: {sentiment_result}")
            except Exception as e:
                logging.error(f"Error adding sentiment to TTS queue: {e}")

        async def monitor_tts_and_update():
            await update_sentiment()
            QTimer.singleShot(1000, self.start_right_rotation)  # Check every second if TTS has finished

        asyncio.ensure_future(monitor_tts_and_update())

    async def update_story_card(self, category, story_card, stories, progress_bar):
        if category in self.progress_timers:
            self.progress_timers[category].stop()

        current_index = self.current_story_index.get(category, 0)
        next_index = (current_index + 1) % len(stories)
        self.current_story_index[category] = next_index

        clear_widgets(story_card)
        new_story_card, new_progress_bar = await create_story_card(stories[next_index], category, story_card)
        story_card.layout().addWidget(new_story_card)
        self.start_progress_bar(new_progress_bar, category, 30)

    async def get_current_sentiment_analysis(self):
        """Fetch the latest sentiment analysis result for the currently displayed story."""
        for category, (story_card, stories, progress_bar) in self.story_widgets.items():
            current_index = self.current_story_index.get(category, 0)
            story = stories[current_index]
            story_title = story.get('title', 'No title available')
            story_description = story.get('description', 'No description available')
            full_text = f"Title: {story_title}. Description: {story_description}"
            story_id = story.get('id', story_title)  # Use story 'id' or 'title' as the unique identifier

            logging.info(f"Analyzing text for story: {story_title}")
            sentiment_result = await analyze_text(
                full_text,
                root=self,
                label=self.sentiment_label,
                story_id=story_id,  # Pass the unique story identifier
                model="llama3:latest"  # You can change this to use dynamic model selection
            )
            logging.info(f"Sentiment result for {story_title}: {sentiment_result}")
            return story_title, sentiment_result

    def start_progress_bar(self, progress_bar, category, duration_seconds):
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_interval = 1000  # 1 second interval
        increment = 100 / duration_seconds

        def update_progress():
            current_value = progress_bar.value()
            new_value = current_value + increment
            if new_value >= 100:
                progress_bar.setValue(100)
            else:
                progress_bar.setValue(new_value)

        if category in self.progress_timers:
            self.progress_timers[category].stop()

        progress_timer = QTimer(self)
        progress_timer.timeout.connect(update_progress)
        progress_timer.start(progress_interval)

        self.progress_timers[category] = progress_timer

    async def update_news_grid(self):
        if self.news_grid_layout is None:
            logging.error("News grid layout not initialized.")
            return

        categories = list(self.feeds_data.keys())
        if not categories:
            logging.warning("No categories available to display.")
            return

        clear_widgets(self.news_grid_frame)

        row, col = 0, 0
        max_columns = 2

        for category in categories:
            feeds = self.feeds_data.get(category, [])
            if not isinstance(feeds, list):
                logging.error(f"Feeds for category {category} are not a list: {feeds}")
                continue

            stories = []
            for feed_dict in feeds:
                feed_data = feed_dict.get('feed', {})
                stories.extend(feed_data.get('entries', []))

            if not stories:
                logging.warning(f"No stories found for category: {category}")
                continue

            self.current_story_index[category] = 0
            story_card, progress_bar = await create_story_card(stories[0], category, self.news_grid_frame)
            story_card.setFixedSize(580, 280)
            self.news_grid_layout.addWidget(story_card, row, col)

            self.story_widgets[category] = (story_card, stories, progress_bar)
            self.start_progress_bar(progress_bar, category, 30)

            col += 1
            if col >= max_columns:
                col = 0
                row += 1
