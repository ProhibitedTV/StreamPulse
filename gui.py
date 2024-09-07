import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from fetchers import fetch_rss_feed, fetch_image, sanitize_html
from PIL import Image, ImageTk
import time
from datetime import datetime
import requests

UPDATE_INTERVAL = 10000  # 10 seconds

def update_feed(rss_feeds, content_frame, root, category_name):
    """
    Fetch and display the RSS feed content dynamically, updating it every 10 seconds.

    Args:
        rss_feeds (list): List of RSS feed URLs.
        content_frame (ttkb.Frame): Frame where the feed will be displayed.
        root (ttkb.Window): Main window of the GUI.
        category_name (str): The category of news (General, Finance, etc.).
    """
    current_story_index = 0
    feed_entries = []

    def fetch_feed_entries():
        nonlocal feed_entries
        feed_entries = []
        for feed_url in rss_feeds:
            try:
                feed = fetch_rss_feed(feed_url)
                if feed:
                    feed_entries.extend(feed.entries[:3])
            except Exception as e:
                print(f"Error fetching feed from {feed_url}: {e}")

    def show_next_story():
        nonlocal current_story_index
        if feed_entries:
            story = feed_entries[current_story_index]
            current_story_index = (current_story_index + 1) % len(feed_entries)
            fade_in_story(content_frame, story)

        root.after(UPDATE_INTERVAL, show_next_story)

    def refresh_feed():
        fetch_feed_entries()
        root.after(UPDATE_INTERVAL * 30, refresh_feed)

    fetch_feed_entries()
    show_next_story()
    refresh_feed()

def clear_and_display_story(content_frame, story):
    """
    Clears the frame and displays the new story.

    Args:
        content_frame (ttkb.Frame): The frame to clear and display the new story.
        story (feedparser.FeedParserDict): The story data to display.
    """
    for widget in content_frame.winfo_children():
        widget.destroy()
    display_story_card(story, content_frame)
    display_progress_bar(content_frame)

def display_story_card(story, parent_frame):
    """
    Displays the headline, image, description, and link for a given news story.

    Args:
        story (feedparser.FeedParserDict): The story data.
        parent_frame (ttkb.Frame): The frame where the story card will be displayed.
    """
    headline = story.title
    description = sanitize_html(story.get("description", "No description available."))
    image_url = story.get("media_content", [{}])[0].get("url")

    # Create a canvas for the story
    canvas = tk.Canvas(parent_frame, width=450, height=400, bg="#FFFFFF", bd=0, highlightthickness=0)
    canvas.pack(padx=10, pady=10)
    
    # Create a rectangle to simulate a 'glass' effect
    canvas.create_rectangle(10, 10, 440, 390, outline="", fill="#DDDDDD")  # Light gray as a substitute for transparency
    
    # Create a frame inside the canvas for content
    story_frame = ttkb.Frame(canvas, padding=10, style="Glass.TFrame")
    story_frame.place(x=20, y=20, width=410, height=360)

    # Headline
    headline_label = ttkb.Label(story_frame, text=headline, wraplength=380, anchor="center", justify="center", font=("Helvetica", 18, "bold"), bootstyle="info")
    headline_label.pack(pady=10)

    # Display the image if available
    if image_url:
        image = fetch_image(image_url, 380, 180)
        if image:
            image_label = tk.Label(story_frame, image=image, bg="#FFFFFF")
            image_label.image = image  # Keep a reference
            image_label.pack(pady=10)

    # Description label
    description_label = ttkb.Label(story_frame, text=description, wraplength=380, anchor="w", justify="left", font=("Helvetica", 14), bootstyle="light")
    description_label.pack(pady=10)

    # Source label with clickable link
    source = story.get("link", "Unknown Source")
    source_label = ttkb.Label(story_frame, text=f"Read more at: {source}", anchor="center", font=("Helvetica", 12, "italic"), cursor="hand2", bootstyle="info")
    source_label.pack(pady=10)
    source_label.bind("<Button-1>", lambda e: open_link(source))

def display_progress_bar(parent_frame):
    """
    Displays a progress bar to indicate the story transition period.

    Args:
        parent_frame (ttkb.Frame): The frame where the progress bar will be displayed.
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

def fade_in_story(content_frame, story):
    """
    Fades in the story when displayed.

    Args:
        content_frame (ttkb.Frame): The frame where the story will be displayed.
        story (feedparser.FeedParserDict): The story data.
    """
    clear_and_display_story(content_frame, story)
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
    Opens the given URL in the default web browser.

    Args:
        url (str): The URL to open.
    """
    import webbrowser
    webbrowser.open(url)

def add_category_label(parent_frame, category_name):
    """
    Adds a category label to the feed display.

    Args:
        parent_frame (ttkb.Frame): The frame where the label will be placed.
        category_name (str): The name of the news category.
    """
    label = ttkb.Label(parent_frame, text=category_name, font=("Helvetica", 20, "bold"), bootstyle="primary")
    label.pack(pady=10)
