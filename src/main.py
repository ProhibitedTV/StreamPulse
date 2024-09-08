import os
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from PIL import Image, ImageTk
from ui.gui import update_feed
from ui.feeds import GENERAL_RSS_FEEDS, FINANCIAL_RSS_FEEDS, VIDEO_GAMES_RSS_FEEDS, SCIENCE_TECH_RSS_FEEDS, HEALTH_ENVIRONMENT_RSS_FEEDS, ENTERTAINMENT_RSS_FEEDS
from ui.stock_ticker import create_stock_ticker_frame
from ui.stats_widgets import add_global_stats, add_world_clock

# Get the absolute path of the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Construct the path to the images folder
bg_image_path = os.path.join(project_root, 'images', 'bg.png')

# GUI setup
root = ttkb.Window(themename="darkly")
root.title("StreamPulse - Dynamic News Display")
root.attributes("-fullscreen", True)

# Load the background image
bg_image = Image.open(bg_image_path)
bg_image = bg_image.resize((1920, 1080), Image.Resampling.LANCZOS)
bg_photo = ImageTk.PhotoImage(bg_image)

# Create a Canvas to hold the background
canvas = tk.Canvas(root, width=1920, height=1080)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_photo, anchor="nw")

# Main frame to hold content above the background
main_frame = ttkb.Frame(canvas)
canvas.create_window(0, 0, window=main_frame, anchor="nw")

# Set the weight of the grid for proper layout
main_frame.grid_columnconfigure(0, weight=3)  # Left: news sections
main_frame.grid_columnconfigure(1, weight=3)
main_frame.grid_columnconfigure(2, weight=3)
main_frame.grid_columnconfigure(3, weight=1)  # Right: global stats and world clock
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_rowconfigure(1, weight=1)

# News Section layout in 3 columns, 2 rows

# General News Section
general_label = ttkb.Label(main_frame, text="General News", font=("Helvetica", 18, "bold"), bootstyle="primary")
general_label.grid(row=0, column=0, padx=10, pady=5, sticky="n")
general_content_frame = ttkb.Frame(main_frame)
general_content_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, GENERAL_RSS_FEEDS, general_content_frame, root, "General News")

# Financial News Section
financial_label = ttkb.Label(main_frame, text="Financial News", font=("Helvetica", 18, "bold"), bootstyle="primary")
financial_label.grid(row=0, column=1, padx=10, pady=5, sticky="n")
financial_content_frame = ttkb.Frame(main_frame)
financial_content_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, FINANCIAL_RSS_FEEDS, financial_content_frame, root, "Financial News")

# Video Games Section
games_label = ttkb.Label(main_frame, text="Video Games News", font=("Helvetica", 18, "bold"), bootstyle="primary")
games_label.grid(row=0, column=2, padx=10, pady=5, sticky="n")
games_content_frame = ttkb.Frame(main_frame)
games_content_frame.grid(row=1, column=2, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, VIDEO_GAMES_RSS_FEEDS, games_content_frame, root, "Video Games News")

# Science & Tech Section
science_label = ttkb.Label(main_frame, text="Science & Tech News", font=("Helvetica", 18, "bold"), bootstyle="primary")
science_label.grid(row=2, column=0, padx=10, pady=5, sticky="n")
science_content_frame = ttkb.Frame(main_frame)
science_content_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, SCIENCE_TECH_RSS_FEEDS, science_content_frame, root, "Science & Tech News")

# Health & Environment Section
health_label = ttkb.Label(main_frame, text="Health & Environment", font=("Helvetica", 18, "bold"), bootstyle="primary")
health_label.grid(row=2, column=1, padx=10, pady=5, sticky="n")
health_content_frame = ttkb.Frame(main_frame)
health_content_frame.grid(row=3, column=1, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, HEALTH_ENVIRONMENT_RSS_FEEDS, health_content_frame, root, "Health & Environment")

# Entertainment Section
entertainment_label = ttkb.Label(main_frame, text="Entertainment", font=("Helvetica", 18, "bold"), bootstyle="primary")
entertainment_label.grid(row=2, column=2, padx=10, pady=5, sticky="n")
entertainment_content_frame = ttkb.Frame(main_frame)
entertainment_content_frame.grid(row=3, column=2, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, ENTERTAINMENT_RSS_FEEDS, entertainment_content_frame, root, "Entertainment")

# Right column (global stats and world clock)
stats_clock_frame = ttkb.Frame(main_frame)
stats_clock_frame.grid(row=0, column=3, rowspan=2, padx=10, pady=5, sticky="nsew")
stats_clock_frame.grid_columnconfigure(0, weight=1)

# Add Global Stats to the frame
add_global_stats(stats_clock_frame)

# Add World Clock to the same frame below the stats
add_world_clock(stats_clock_frame)

# Create Stock Ticker at the bottom
stock_ticker_frame = ttkb.Frame(canvas, padding=10, bootstyle="info")
canvas.create_window(960, 1050, window=stock_ticker_frame, anchor="center")
create_stock_ticker_frame(stock_ticker_frame)

# Press 'Esc' to exit full screen
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

# Start the Tkinter main loop
root.mainloop()
