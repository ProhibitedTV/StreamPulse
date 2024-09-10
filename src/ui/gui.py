# Standard library imports
import os
import logging
import queue
import tkinter as tk
from tkinter import ttk

# Third-party library imports
import ttkbootstrap as ttkb
from PIL import Image, ImageTk

# Internal application imports
from api.fetchers import fetch_rss_feed, fetch_image, sanitize_html
from api.sentiment import analyze_text
from api.tts_engine import tts_queue
from ui.stats_widgets import add_global_stats, add_world_clock
from ui.feed_manager import update_feed
from ui.stock_ticker import create_stock_ticker_frame
from ui.feeds import get_feeds_by_category
from utils.threading import run_with_callback, run_with_exception_handling

# Update interval for feed refresh (10 seconds)
UPDATE_INTERVAL = 10000

# Global queue for feed entries
feed_queue = queue.Queue()

def add_category_label(parent_frame, category_name):
    """
    Adds a category label to the news feed display.
    """
    logging.debug(f"Adding category label: {category_name}")
    label = ttkb.Label(parent_frame, text=category_name, font=("Helvetica", 20, "bold"), bootstyle="primary")
    label.pack(pady=10)

def setup_main_frame(root):
    """
    Set up the main application frame within the root Tkinter window.
    This includes sections for general news, financial news, video games, science & tech, and other categories.

    Args:
        root: The root Tkinter window.

    Returns:
        ttkb.Frame: The main frame of the application with news sections, a stock ticker, global stats, and a world clock.
    """
    logging.debug("Setting up main frame...")

    # Get the absolute path of the project root directory (StreamPulse)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    bg_image_path = os.path.join(project_root, 'images', 'bg.png')

    # Load the background image if available
    if os.path.exists(bg_image_path):
        try:
            bg_image = Image.open(bg_image_path)
            bg_image = bg_image.resize((1920, 1080), Image.Resampling.LANCZOS)
            bg_photo = ImageTk.PhotoImage(bg_image)
            logging.info("Background image loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading background image: {e}")
            root.configure(bg="black")  # Fallback color if image fails
            return
    else:
        logging.error(f"Background image not found at path: {bg_image_path}")
        root.configure(bg="black")  # Fallback color if image is missing
        return

    # Create a Canvas to hold the background
    canvas = ttkb.Canvas(root, width=1920, height=1080)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")
    logging.debug("Canvas with background image created.")

    # Set a scroll region to prevent content from overflowing
    canvas.config(scrollregion=canvas.bbox("all"))

    # Create the main frame to hold content above the background
    main_frame = ttkb.Frame(canvas)
    canvas.create_window(0, 0, window=main_frame, anchor="nw")
    logging.debug("Main frame created and added to canvas.")

    # Set the weight of the grid for proper layout
    logging.debug("Configuring grid layout for main frame.")
    for i in range(4):
        main_frame.grid_columnconfigure(i, weight=1, uniform="col")
        logging.debug(f"Configured column {i} with weight 1 and uniform 'col'.")
    for i in range(3):
        main_frame.grid_rowconfigure(i, weight=1, uniform="row")
        logging.debug(f"Configured row {i} with weight 1 and uniform 'row'.")

    # Helper to set up each news section
    def create_news_section(row, col, category_name, internal_category):
        logging.debug(f"Setting up {category_name} section at row {row}, column {col}.")
        
        # Create a frame to hold both the category label and the content
        section_frame = ttkb.Frame(main_frame, width=450, height=400)
        section_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        section_frame.grid_propagate(False)
        logging.info(f"{category_name} section created with fixed size at row {row}, column {col}.")

        # Add the category label
        label = ttkb.Label(section_frame, text=f"{category_name} News", font=("Helvetica", 18, "bold"), bootstyle="primary")
        label.pack(pady=5)
        logging.debug(f"{category_name} label added to the section.")

        # Frame for the content (story cards) and sentiment analysis
        content_frame = ttkb.Frame(section_frame, width=450, height=300)
        content_frame.pack(fill="both", expand=True)
        content_frame.grid_propagate(False)
        logging.debug(f"Content frame created for {category_name} section.")

        sentiment_frame = ttkb.Frame(section_frame, width=450, height=100)
        sentiment_frame.pack(fill="both", expand=True)
        sentiment_frame.grid_propagate(False)
        logging.debug(f"Sentiment frame created for {category_name} section.")

        # Trigger feed update using threading to prevent blocking, 
        # use run_with_callback to process feed updates and then display in the UI
        logging.info(f"Starting feed update for {category_name}.")
        run_with_callback(
            get_feeds_by_category,  # Target function
            lambda feeds: update_feed(feeds, content_frame, root, f"{category_name} News", sentiment_frame),  # Callback function
            internal_category  # Pass as a positional argument, not keyword
        )

    # Adding sections for different categories of news
    logging.debug("Adding news sections.")
    create_news_section(0, 0, "General", "general")
    create_news_section(0, 1, "Financial", "financial")
    create_news_section(0, 2, "Video Games", "video_games")
    create_news_section(1, 0, "Science & Tech", "science_tech")
    create_news_section(1, 1, "Health & Environment", "health_environment")
    create_news_section(1, 2, "Entertainment", "entertainment")

    # Right column for global stats and world clock
    logging.debug("Setting up stats and clock frame.")
    stats_clock_frame = ttkb.Frame(main_frame)
    stats_clock_frame.grid(row=0, column=3, rowspan=2, padx=10, pady=5, sticky="nsew")
    stats_clock_frame.grid_columnconfigure(0, weight=1)
    logging.debug("Stats and clock frame created and added to grid.")

    # Add Global Stats and World Clock widgets
    logging.info("Adding global stats and world clock widgets.")
    add_global_stats(stats_clock_frame)
    add_world_clock(stats_clock_frame)

    # Create Stock Ticker at the bottom
    logging.debug("Creating stock ticker frame.")
    stock_ticker_frame = ttkb.Frame(canvas, padding=10, bootstyle="info")
    canvas.create_window(960, 1050, window=stock_ticker_frame, anchor="center")
    create_stock_ticker_frame(stock_ticker_frame)
    logging.debug("Stock ticker frame created.")

    logging.debug("Main frame setup complete.")
    return main_frame
