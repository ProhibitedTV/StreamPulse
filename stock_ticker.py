import os
import requests
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
STOCKS = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "META",
    "TSLA", "NFLX", "NVDA", "AMD", "INTC",
    "JPM", "BAC", "WFC", "GS", "C",
    "XOM", "CVX", "BP", "COP", "OXY",
    "PFE", "JNJ", "MRNA", "BMY", "LLY"
]

def fetch_stock_price(symbol):
    """
    Fetches real-time stock data from Alpha Vantage API for the given stock symbol.

    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT).

    Returns:
        str: Stock price if successful, otherwise "N/A".
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            return data["Global Quote"]["05. price"]
        else:
            print(f"No price data for {symbol}")
            return "N/A"
    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")
        return "N/A"

def update_stock_ticker(stock_frame, root):
    """
    Updates the stock ticker with current prices and rotates between stocks.

    Args:
        stock_frame (ttkb.Frame): The frame where the stock ticker will be displayed.
        root (ttkb.Window): Tkinter root window.
    """
    for widget in stock_frame.winfo_children():
        widget.destroy()

    for symbol in STOCKS:
        stock_price = fetch_stock_price(symbol)
        stock_label = ttkb.Label(stock_frame, text=f"{symbol}: ${stock_price}", font=("Helvetica", 14), anchor="center")
        stock_label.pack(pady=5)

    # Update the stock prices every 60 seconds
    root.after(60000, update_stock_ticker, stock_frame, root)  # Use root.after instead of time.sleep

def create_stock_ticker_frame(root):
    """
    Creates a stock ticker frame and adds it to the right side of the main window.

    Args:
        root (ttkb.Window): The root window.
    """
    stock_frame = ttkb.Frame(root, padding=10, bootstyle="info")
    stock_frame.pack(side="right", fill="y", padx=20)
    update_stock_ticker(stock_frame, root)  # Pass both stock_frame and root
