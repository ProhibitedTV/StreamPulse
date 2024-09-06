import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from fetchers import fetch_rss_feed, fetch_image, sanitize_html
import time

# Configurable update interval (in milliseconds)
UPDATE_INTERVAL = 10000  # 10 seconds

def update_feed(rss_feeds, content_frame, root, category_name):
    """
    Fetches and updates the feed for a given category, cycling through stories every 10 seconds.
    
    Args:
        rss_feeds (list): List of RSS feed URLs.
        content_frame (ttkb.Frame): The frame where the content will be displayed.
        root (ttkb.Window): The root window to handle refresh.
        category_name (str): The name of the category being displayed.
    """
    current_story_index = 0
    feed_entries = []

    # Fetch and combine top 3 stories from each feed
    for feed_url in rss_feeds:
        try:
            feed = fetch_rss_feed(feed_url)
            if feed:
                feed_entries.extend(feed.entries[:3])
        except Exception as e:
            print(f"Error fetching feed from {feed_url}: {e}")

    def show_next_story():
        """
        Displays the next story in the feed, replacing the previous one.
        Cycles through stories every UPDATE_INTERVAL.
        """
        nonlocal current_story_index
        if feed_entries:
            story = feed_entries[current_story_index]
            current_story_index = (current_story_index + 1) % len(feed_entries)

            # Use root.after() to ensure UI updates are done on the main thread
            fade_in_story(content_frame, story)

            # Recursively schedule the next story update
            root.after(UPDATE_INTERVAL, show_next_story)

    # Start cycling through stories
    root.after(0, show_next_story)

def clear_and_display_story(content_frame, story):
    """
    Clears the current content and displays the new story.
    
    Args:
        content_frame (ttkb.Frame): The frame where the story content will be displayed.
        story (dict): The story to display.
    """
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Display the new story
    display_story_card(story, content_frame)
    display_progress_bar(content_frame)

def display_story_card(story, parent_frame):
    """
    Displays a single story card with headline, description, and optional image.
    
    Args:
        story (dict): The RSS story entry.
        parent_frame (ttkb.Frame): The frame where the story card will be displayed.
    """
    headline = story.title
    description = sanitize_html(story.get("description", "No description available."))
    image_url = story.get("media_content", [{}])[0].get("url")

    # Set a fixed size for the story frame (quadrants) based on a 1080p display
    story_frame = ttkb.Frame(parent_frame, padding=10, bootstyle="secondary", width=450, height=400)
    story_frame.pack_propagate(0)  # Prevent the frame from resizing to fit content
    story_frame.pack(fill="both", expand=False, padx=5, pady=5)
    story_frame.config(relief="raised", borderwidth=5)

    # Headline label
    headline_label = ttkb.Label(story_frame, text=headline, wraplength=400, anchor="center", justify="center", font=("Helvetica", 16, "bold"))
    headline_label.pack(pady=10)

    # Display the image if available
    if image_url:
        image = fetch_image(image_url, 400, 200)
        if image:
            image_label = tk.Label(story_frame, image=image)
            image_label.image = image  # Keep reference to avoid garbage collection
            image_label.pack(pady=10)

    # Description label, limited to a fixed height
    description_label = ttkb.Label(story_frame, text=description, wraplength=400, anchor="w", justify="left", font=("Helvetica", 12))
    description_label.pack(pady=10)

    # Source label with clickable link
    source = story.get("link", "Unknown Source")
    source_label = ttkb.Label(story_frame, text=f"Read more at: {source}", anchor="center", font=("Helvetica", 12, "italic"), cursor="hand2")
    source_label.pack(pady=10)
    source_label.bind("<Button-1>", lambda e: open_link(source))

def display_progress_bar(parent_frame):
    """
    Displays a progress bar that updates over the duration of the story display time.
    
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
        """
        Updates the progress bar incrementally until the next refresh.
        """
        if step < 100:
            progress_bar["value"] = step
            progress_bar.after(UPDATE_INTERVAL // 100, update_bar, step + 1)

    update_bar()

def fade_in_story(content_frame, story):
    """
    Creates a fade-in effect for displaying the new story.
    
    Args:
        content_frame (ttkb.Frame): The frame where the story will be displayed.
        story (dict): The story to display.
    """
    clear_and_display_story(content_frame, story)

    # Retrieve the story frame to apply fade
    story_frame = content_frame.winfo_children()[0]

    # Create a canvas overlay to simulate fade-in effect
    fade_canvas = tk.Canvas(story_frame, width=450, height=400, bg="black")
    fade_canvas.place(x=0, y=0, relwidth=1, relheight=1)

    def fade(step=0):
        if step <= 1.0:
            # Decrease canvas opacity to simulate fade-in
            alpha = int(step * 255)
            fade_canvas.configure(bg=f'#{alpha:02x}{alpha:02x}{alpha:02x}')
            story_frame.after(50, fade, step + 0.05)
        else:
            fade_canvas.destroy()  # Remove the overlay once the fade-in is complete

    fade()

def open_link(url):
    """
    Opens a URL in the default web browser.
    
    Args:
        url (str): The URL to open.
    """
    import webbrowser
    webbrowser.open(url)

def add_category_label(parent_frame, category_name):
    """
    Adds a label to indicate the category of news being displayed.
    
    Args:
        parent_frame (ttkb.Frame): The frame where the label will be added.
        category_name (str): The name of the news category (e.g., 'Financial News').
    """
    label = ttkb.Label(parent_frame, text=category_name, font=("Helvetica", 18, "bold"), bootstyle="primary")
    label.pack(pady=10)
