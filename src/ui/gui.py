import os
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from api.fetchers import fetch_rss_feed, fetch_image, sanitize_html
from api.sentiment import analyze_text
from api.tts_engine import tts_queue
from PIL import Image, ImageTk
import logging
from ui.stats_widgets import add_global_stats, add_world_clock
from ui.stock_ticker import create_stock_ticker_frame
from ui.feeds import get_feeds_by_category
import threading
import queue

# Update interval for feed refresh (10 seconds)
UPDATE_INTERVAL = 10000

# Global queue for feed entries
feed_queue = queue.Queue()

def update_feed(rss_feeds, content_frame, root, category_name, sentiment_frame):
    """
    Fetch and display RSS feed content dynamically, updating every 10 seconds.
    Also updates sentiment analysis in a separate widget and performs TTS.
    
    Args:
        rss_feeds (list): A list of RSS feed URLs to fetch data from.
        content_frame (tk.Widget): The frame in the GUI where the feed content will be displayed.
        root (tk.Tk): The root Tkinter window.
        category_name (str): The category name of the feed (e.g., 'General News').
        sentiment_frame (tk.Widget): A frame for displaying sentiment analysis results.
    """
    feed_entries = []  # Initialize feed_entries in the outer scope

    def fetch_feed_entries():
        """
        Fetch RSS feed entries and add them to the global feed queue.
        If any error occurs during fetching, log it and skip that feed.
        """
        nonlocal feed_entries  # Ensure we modify the outer feed_entries list
        feed_entries = []  # Clear previous entries
        
        logging.debug(f"Fetching feeds for category: {category_name}")

        for feed_url in rss_feeds:
            try:
                logging.debug(f"Fetching feed from URL: {feed_url}")
                feed = fetch_rss_feed(feed_url)
                
                if feed:
                    logging.debug(f"Feed fetched from {feed_url}. Number of entries: {len(feed.entries[:3])}")
                    feed_entries.extend(feed.entries[:3])  # Limit the number of entries
                else:
                    logging.warning(f"No feed found at {feed_url}")

            except ConnectionError as ce:
                logging.error(f"Connection error while fetching feed from {feed_url}: {ce}")
            except Exception as e:
                logging.error(f"Unexpected error fetching feed from {feed_url}: {e}")
        
        if not feed_entries:
            logging.warning(f"No entries retrieved for category: {category_name}")
        else:
            logging.info(f"Total entries fetched for {category_name}: {len(feed_entries)}")

        # Place fetched entries into the queue for processing
        feed_queue.put((category_name, feed_entries))

    def show_next_story():
        try:
            category, entries = feed_queue.get_nowait()
            if category == category_name and entries:
                if not entries:  # Fallback in case entries list is empty
                    logging.warning(f"No stories available for category: {category_name}")
                    display_placeholder_message(content_frame, "No stories available")
                else:
                    story = entries.pop(0)
                    root.after(0, lambda: fade_in_story(content_frame, story, sentiment_frame))
                    entries.append(story)  # Move story to end for cyclic display
            else:
                logging.debug(f"No stories available for category: {category_name}")
        except queue.Empty:
            logging.debug(f"No new stories in the feed queue for category: {category_name}")
        finally:
            root.after(UPDATE_INTERVAL, show_next_story)

    def display_placeholder_message(frame, message):
        """Display a placeholder message when no feed entries are available."""
        for widget in frame.winfo_children():
            widget.destroy()  # Clear existing widgets
        label = ttk.Label(frame, text=message, font=("Helvetica", 14), anchor="center")
        label.pack(expand=True)

    # Start a thread to fetch feed entries in the background
    threading.Thread(target=fetch_feed_entries, daemon=True).start()

    # Schedule the first update
    root.after(UPDATE_INTERVAL, show_next_story)

    # Refresh the feed every 30 intervals (5 minutes)
    def refresh_feed():
        """
        Refresh the feeds periodically by refetching them in the background.
        """
        logging.debug(f"Refreshing feeds for category: {category_name}")
        threading.Thread(target=fetch_feed_entries, daemon=True).start()
        root.after(UPDATE_INTERVAL * 30, refresh_feed)

    # Start the feed refresh process
    refresh_feed()

def clear_and_display_story(content_frame, story, sentiment_frame):
    """
    Clears the current content from the content_frame and displays a new story.
    Additionally, updates the sentiment analysis widget in the sentiment_frame.

    Args:
        content_frame (ttk.Frame): The frame where the news story will be displayed.
        story (feedparser.FeedParserDict): The RSS feed story object containing the story data.
        sentiment_frame (ttk.Frame): The frame where sentiment analysis will be displayed.

    This function first clears any existing widgets in the content_frame and sentiment_frame,
    then populates it with the new story and its associated sentiment analysis. A progress bar
    is also added to visually indicate the time until the next story appears.
    """
    logging.debug(f"Clearing and displaying new story in content frame. Story title: {story.title}")

    # Step 1: Clear existing content in the content_frame
    logging.debug("Clearing all existing widgets in content_frame.")
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Step 2: Clear existing sentiment analysis in sentiment_frame
    logging.debug("Clearing all existing widgets in sentiment_frame.")
    for widget in sentiment_frame.winfo_children():
        widget.destroy()

    # Step 3: Display the new story card (headline, image, description, link)
    try:
        logging.debug(f"Displaying new story: {story.title}")
        display_story_card(story, content_frame, sentiment_frame)
    except Exception as e:
        logging.error(f"Error displaying story: {e}")

    # Step 4: Display the progress bar at the bottom of the content frame
    try:
        logging.debug("Displaying progress bar in content_frame.")
        display_progress_bar(content_frame)
    except Exception as e:
        logging.error(f"Error displaying progress bar: {e}")

def display_story_card(story, parent_frame, sentiment_frame):
    """
    Displays a news story's headline, image, description, and source link within a parent frame.
    Also performs sentiment analysis in the background and updates the sentiment_frame with the result.
    
    Args:
        story (feedparser.FeedParserDict): The RSS feed story object containing title, description, etc.
        parent_frame (ttk.Frame): The frame where the news story will be displayed.
        sentiment_frame (ttk.Frame): The frame where sentiment analysis results will be displayed.
    """
    # Safely extract headline and description
    headline = story.get("title", "No title available")
    description = sanitize_html(story.get("description", "No description available."))
    image_url = story.get("media_content", [{}])[0].get("url", None)

    logging.debug(f"Displaying story: {headline}")

    def analyze_sentiment():
        """Analyze the sentiment of the story description in a background thread."""
        try:
            logging.debug(f"Analyzing sentiment for the story: {headline}")
            sentiment = analyze_text(description, model="llama3:latest")
            parent_frame.after(0, lambda: update_sentiment_display(sentiment))
        except Exception as e:
            logging.error(f"Sentiment analysis failed for {headline}: {e}")
            parent_frame.after(0, lambda: update_sentiment_display("Sentiment analysis failed"))

    def update_sentiment_display(sentiment):
        """Update the sentiment_frame with the sentiment analysis result."""
        logging.debug(f"Updating sentiment display with: {sentiment}")
        for widget in sentiment_frame.winfo_children():
            widget.destroy()  # Clear previous widgets
        sentiment_label = ttkb.Label(sentiment_frame, text=f"Sentiment: {sentiment}", font=("Helvetica", 18, "bold"), bootstyle="secondary")
        sentiment_label.pack(padx=10, pady=10)

        # Add the story summary to the TTS queue
        summary = f"Headline: {headline}. Sentiment: {sentiment}."
        tts_queue.put(summary)

    threading.Thread(target=analyze_sentiment, daemon=True).start()  # Run sentiment analysis in the background

    # Create canvas for displaying the story
    canvas = tk.Canvas(parent_frame, width=450, height=400, bg="#FFFFFF", bd=2, highlightthickness=2, highlightbackground="blue")
    canvas.pack(padx=10, pady=10)

    # Create a frame inside the canvas to hold the story content
    story_frame = ttkb.Frame(canvas, padding=10, style="Glass.TFrame")
    story_frame.place(x=20, y=20, width=410, height=360)

    # Display headline
    headline_label = ttkb.Label(story_frame, text=headline, wraplength=380, anchor="center", justify="center", font=("Helvetica", 18, "bold"), bootstyle="info")
    headline_label.pack(pady=10)

    # Display the image if available
    if image_url:
        logging.debug(f"Fetching image from: {image_url}")
        
        def load_image():
            try:
                image = fetch_image(image_url, 380, 180)
                if image:
                    parent_frame.after(0, lambda: display_image(image))
                else:
                    logging.warning(f"Failed to load image from: {image_url}")
            except Exception as e:
                logging.error(f"Error fetching image from {image_url}: {e}")

        def display_image(image):
            """Display the fetched image in the story frame."""
            image_label = tk.Label(story_frame, image=image, bg="#FFFFFF")
            image_label.image = image  # Prevent the image from being garbage collected
            image_label.pack(pady=10)

        threading.Thread(target=load_image, daemon=True).start()  # Load image in the background

    # Display description
    description_label = ttkb.Label(story_frame, text=description, wraplength=380, anchor="w", justify="left", font=("Helvetica", 14), bootstyle="light")
    description_label.pack(pady=10)

    # Display source link
    source = story.get("link", "Unknown Source")
    source_label = ttkb.Label(story_frame, text=f"Read more at: {source}", anchor="center", font=("Helvetica", 12, "italic"), cursor="hand2", bootstyle="info")
    source_label.pack(pady=10)
    source_label.bind("<Button-1>", lambda e: open_link(source))

    logging.debug(f"Story display complete for: {headline}")

def display_progress_bar(parent_frame):
    """
    Displays a progress bar to indicate the transition period between stories.
    """
    progress_frame = ttkb.Frame(parent_frame)
    progress_frame.pack(fill="x", pady=5)

    progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
    progress_bar.pack(fill="x", padx=10)
    progress_bar["maximum"] = 100
    progress_bar["value"] = 0

    def update_bar(step=0):
        if step < 100:
            progress_bar["value"] = step
            progress_bar.after(UPDATE_INTERVAL // 100, update_bar, step + 1)

    update_bar()

def fade_in_story(content_frame, story, sentiment_frame):
    """
    Fades in the story when displayed and calls sentiment analysis.
    """
    logging.info(f"Displaying story: {story.get('title', 'No title available')} in category")
    clear_and_display_story(content_frame, story, sentiment_frame)
    story_frame = content_frame.winfo_children()[0]

    fade_canvas = tk.Canvas(story_frame, width=450, height=400, bg="black")
    fade_canvas.place(x=0, y=0, relwidth=1, relheight=1)

    def fade(step=0):
        if step <= 1.0:
            alpha = int(step * 255)
            fade_canvas.configure(bg=f'#{alpha:02x}{alpha:02x}{alpha:02x}')
            story_frame.after(50, fade, step + 0.05)
        else:
            fade_canvas.destroy()

    fade()

def open_link(url):
    """
    Opens the provided URL in the default web browser.
    """
    import webbrowser
    webbrowser.open(url)

def add_category_label(parent_frame, category_name):
    """
    Adds a category label to the news feed display.
    """
    label = ttkb.Label(parent_frame, text=category_name, font=("Helvetica", 20, "bold"), bootstyle="primary")
    label.pack(pady=10)

def setup_main_frame(root):
    """
    Set up the main application frame within the root Tkinter window.
    This includes sections for general news, financial news, video games, and other categories.

    Args:
        root: The root Tkinter window.

    Returns:
        ttkb.Frame: The main frame of the application with news sections and a stock ticker.
    """
    logging.debug("Setting up main frame...")

    # Get the absolute path of the project root directory (StreamPulse)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # Go two directories up
    bg_image_path = os.path.join(project_root, 'images', 'bg.png')  # Correct path to 'images/bg.png'

    # Check if the image exists
    if not os.path.exists(bg_image_path):
        logging.error(f"Background image not found at path: {bg_image_path}")
        root.configure(bg="black")  # Fallback background color if image is missing
        return

    # Load the background image
    try:
        bg_image = Image.open(bg_image_path)
        bg_image = bg_image.resize((1920, 1080), Image.Resampling.LANCZOS)
        bg_photo = ImageTk.PhotoImage(bg_image)
    except Exception as e:
        logging.error(f"Error loading background image: {e}")
        root.configure(bg="black")
        return

    # Create a Canvas to hold the background
    canvas = ttkb.Canvas(root, width=1920, height=1080)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")

    # Create the main frame to hold content above the background
    main_frame = ttkb.Frame(canvas)
    canvas.create_window(0, 0, window=main_frame, anchor="nw")

    # Set the weight of the grid for proper layout
    main_frame.grid_columnconfigure(0, weight=3)  # Left: news sections
    main_frame.grid_columnconfigure(1, weight=3)
    main_frame.grid_columnconfigure(2, weight=3)
    main_frame.grid_columnconfigure(3, weight=1)  # Right: global stats and world clock
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)

    # Helper to set up each news section
    def create_news_section(row, col, category_name, internal_category):
        logging.debug(f"Setting up {category_name} section at row {row}, column {col}")
        
        label = ttkb.Label(main_frame, text=f"{category_name} News", font=("Helvetica", 18, "bold"), bootstyle="primary")
        label.grid(row=row, column=col, padx=10, pady=5, sticky="n")
        
        content_frame = ttkb.Frame(main_frame)
        content_frame.grid(row=row + 1, column=col, padx=10, pady=5, sticky="nsew")

        sentiment_frame = ttkb.Frame(main_frame)
        sentiment_frame.grid(row=row + 1, column=col + 1, padx=10, pady=5, sticky="nsew")

        # Trigger feed update
        root.after(100 * (row + col), update_feed, get_feeds_by_category(internal_category), content_frame, root, f"{category_name} News", sentiment_frame)

    # Add sections for news, categories, etc.
    create_news_section(0, 0, "General", "general")
    create_news_section(0, 1, "Financial", "financial")
    create_news_section(0, 2, "Video Games", "video_games")
    create_news_section(2, 0, "Science & Tech", "science_tech")
    create_news_section(2, 1, "Health & Environment", "health_environment")
    create_news_section(2, 2, "Entertainment", "entertainment")

    # Right column (global stats and world clock)
    stats_clock_frame = ttkb.Frame(main_frame)
    stats_clock_frame.grid(row=0, column=3, rowspan=2, padx=10, pady=5, sticky="nsew")
    stats_clock_frame.grid_columnconfigure(0, weight=1)

    # Add Global Stats and World Clock
    add_global_stats(stats_clock_frame)
    add_world_clock(stats_clock_frame)

    # Create Stock Ticker at the bottom
    stock_ticker_frame = ttkb.Frame(canvas, padding=10, bootstyle="info")
    canvas.create_window(960, 1050, window=stock_ticker_frame, anchor="center")
    create_stock_ticker_frame(stock_ticker_frame)

    logging.debug("Main frame setup complete.")
    return main_frame
