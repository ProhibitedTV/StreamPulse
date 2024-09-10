import os
import logging
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Internal Project Imports
from api.fetchers import fetch_image, sanitize_html
from utils.threading import run_in_thread
from utils.web import open_link
from api.tts_engine import tts_queue
from api.sentiment import analyze_text

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

    # Set default image path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    default_image_path = os.path.join(project_root, 'images', 'default.png')

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
        sentiment_label = ttk.Label(sentiment_frame, text=f"Sentiment: {sentiment}", font=("Helvetica", 18, "bold"), bootstyle="secondary")
        sentiment_label.pack(padx=10, pady=10)

        # Add the story summary to the TTS queue
        summary = f"Headline: {headline}. Sentiment: {sentiment}."
        tts_queue.put(summary)

    run_in_thread(analyze_sentiment)  # Run sentiment analysis in the background

    # Create canvas for displaying the story
    canvas = tk.Canvas(parent_frame, width=450, height=400, bg="#FFFFFF", bd=2, highlightthickness=2, highlightbackground="blue")
    canvas.pack(padx=10, pady=10)

    # Create a frame inside the canvas to hold the story content
    story_frame = ttk.Frame(canvas, padding=10, style="Glass.TFrame")
    story_frame.place(x=20, y=20, width=410, height=360)

    # Display headline
    headline_label = ttk.Label(story_frame, text=headline, wraplength=380, anchor="center", justify="center", font=("Helvetica", 18, "bold"), bootstyle="info")
    headline_label.pack(pady=10)

    # To hold the image reference
    if not hasattr(parent_frame, 'image_references'):
        parent_frame.image_references = []

    # Display the image if available or fallback to the default image
    def load_default_image():
        """Load and display the default image if the main image fails."""
        try:
            default_image = Image.open(default_image_path)
            default_image = default_image.resize((380, 180), Image.Resampling.LANCZOS)
            display_image(default_image)
        except FileNotFoundError:
            logging.error(f"Default image not found at {default_image_path}. Please ensure the file exists.")
        except Exception as e:
            logging.error(f"Error loading default image: {e}")

    def display_image(image):
        """Display the fetched or default image in the story frame."""
        try:
            img = ImageTk.PhotoImage(image)
            image_label = tk.Label(story_frame, image=img, bg="#FFFFFF")
            image_label.image = img  # Prevent the image from being garbage collected
            image_label.pack(pady=10)

            # Ensure the reference to the image is kept
            parent_frame.image_references.append(img)  
        except Exception as e:
            logging.error(f"Error displaying image: {e}")
            load_default_image()  # Fallback to default image if display fails

    if image_url:
        logging.debug(f"Fetching image from: {image_url}")
        def load_image():
            try:
                image = fetch_image(image_url, 380, 180)
                if image:
                    parent_frame.after(0, lambda: display_image(image))
                else:
                    logging.warning(f"Failed to load image from: {image_url}, loading default image.")
                    parent_frame.after(0, load_default_image)  # Load default image on failure
            except Exception as e:
                logging.error(f"Error fetching image from {image_url}: {e}")
                parent_frame.after(0, load_default_image)  # Load default image on error

        run_in_thread(load_image)  # Load image in the background
    else:
        logging.warning(f"No image URL provided for story: {headline}, using default image.")
        load_default_image()

    # Display description
    description_label = ttk.Label(story_frame, text=description, wraplength=380, anchor="w", justify="left", font=("Helvetica", 14), bootstyle="light")
    description_label.pack(pady=10)

    # Display source link
    source = story.get("link", "Unknown Source")
    source_label = ttk.Label(story_frame, text=f"Read more at: {source}", anchor="center", font=("Helvetica", 12, "italic"), cursor="hand2", bootstyle="info")
    source_label.pack(pady=10)
    source_label.bind("<Button-1>", lambda e: open_link(source))

    logging.debug(f"Story display complete for: {headline}")

def display_progress_bar(parent_frame):
    """
    Displays a progress bar to indicate the transition period between stories.
    """
    progress_frame = ttk.Frame(parent_frame)
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

def clear_and_display_story(content_frame, story, sentiment_frame):
    """
    Clears the current content and displays a new story. Updates sentiment analysis widget.
    
    Args:
        content_frame (ttk.Frame): Frame where the news story will be displayed.
        story (feedparser.FeedParserDict): The RSS feed story object containing story data.
        sentiment_frame (ttk.Frame): Frame for displaying sentiment analysis results.
    """
    logging.debug(f"Clearing and displaying new story in content frame. Story title: {story.get('title', 'No title available')}")

    for widget in content_frame.winfo_children():
        widget.destroy()
    for widget in sentiment_frame.winfo_children():
        widget.destroy()

    try:
        display_story_card(story, content_frame, sentiment_frame)
    except Exception as e:
        logging.error(f"Error displaying story: {e}")
