import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from gui import update_feed
from feeds import GENERAL_RSS_FEEDS, FINANCIAL_RSS_FEEDS, VIDEO_GAMES_RSS_FEEDS, SCIENCE_TECH_RSS_FEEDS
from stock_ticker import create_stock_ticker_frame  # Import stock ticker function

# GUI setup
root = ttkb.Window(themename="darkly")
root.title("StreamPulse - Dynamic News Display")
root.attributes("-fullscreen", True)

main_frame = ttkb.Frame(root)
main_frame.pack(fill="both", expand=True)

quadrant_frame = ttkb.Frame(main_frame)
quadrant_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# General News Section
general_content_frame = ttkb.Frame(quadrant_frame)
general_content_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, GENERAL_RSS_FEEDS, general_content_frame, root)

# Financial News Section
financial_content_frame = ttkb.Frame(quadrant_frame)
financial_content_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, FINANCIAL_RSS_FEEDS, financial_content_frame, root)

# Video Games Section
games_content_frame = ttkb.Frame(quadrant_frame)
games_content_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, VIDEO_GAMES_RSS_FEEDS, games_content_frame, root)

# Science & Tech Section
science_content_frame = ttkb.Frame(quadrant_frame)
science_content_frame.grid(row=3, column=1, padx=10, pady=5, sticky="nsew")
root.after(0, update_feed, SCIENCE_TECH_RSS_FEEDS, science_content_frame, root)

# Create Stock Ticker on the right side
create_stock_ticker_frame(root)

# Press 'Esc' to exit full screen
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

# Start the Tkinter main loop
root.mainloop()
