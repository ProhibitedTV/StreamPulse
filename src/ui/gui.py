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
from utils.threading import run_in_thread

# Update interval for feed refresh (10 seconds)
UPDATE_INTERVAL = 10000

# Global queue for feed entries
feed_queue = queue.Queue()

def add_category_label(parent_frame, category_name):
    """
    Adds a category label to the news feed display.
    """
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

    # Create the main frame to hold content above the background
    main_frame = ttkb.Frame(canvas)
    canvas.create_window(0, 0, window=main_frame, anchor="nw")

    # Set the weight of the grid for proper layout
    for i in range(4):
        main_frame.grid_columnconfigure(i, weight=1, uniform="col")  # Balanced grid layout for columns
    for i in range(3):
        main_frame.grid_rowconfigure(i, weight=1, uniform="row")  # Balanced grid layout for rows

    # Helper to set up each news section
    def create_news_section(row, col, category_name, internal_category):
        logging.debug(f"Setting up {category_name} section at row {row}, column {col}")
        
        # Create a frame to hold both the category label and the content
        section_frame = ttkb.Frame(main_frame)
        section_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Add the category label
        label = ttkb.Label(section_frame, text=f"{category_name} News", font=("Helvetica", 18, "bold"), bootstyle="primary")
        label.pack(pady=5)

        # Frame for the content (story cards) and sentiment analysis
        content_frame = ttkb.Frame(section_frame)
        content_frame.pack(fill="both", expand=True)

        sentiment_frame = ttkb.Frame(section_frame)
        sentiment_frame.pack(fill="both", expand=True)

        # Trigger feed update using threading to prevent blocking
        run_in_thread(update_feed, get_feeds_by_category(internal_category), content_frame, root, f"{category_name} News", sentiment_frame)

    # Adding sections for different categories of news
    create_news_section(0, 0, "General", "general")
    create_news_section(0, 1, "Financial", "financial")
    create_news_section(0, 2, "Video Games", "video_games")
    create_news_section(1, 0, "Science & Tech", "science_tech")
    create_news_section(1, 1, "Health & Environment", "health_environment")
    create_news_section(1, 2, "Entertainment", "entertainment")

    # Right column for global stats and world clock
    stats_clock_frame = ttkb.Frame(main_frame)
    stats_clock_frame.grid(row=0, column=3, rowspan=2, padx=10, pady=5, sticky="nsew")
    stats_clock_frame.grid_columnconfigure(0, weight=1)

    # Add Global Stats and World Clock widgets
    add_global_stats(stats_clock_frame)
    add_world_clock(stats_clock_frame)

    # Create Stock Ticker at the bottom
    stock_ticker_frame = ttkb.Frame(canvas, padding=10, bootstyle="info")
    canvas.create_window(960, 1050, window=stock_ticker_frame, anchor="center")
    create_stock_ticker_frame(stock_ticker_frame)

    logging.debug("Main frame setup complete.")
    return main_frame
