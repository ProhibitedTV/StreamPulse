import os
import requests
import yfinance as yf
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
    Fetches real-time stock data from Alpha Vantage or falls back to Yahoo Finance API.
    
    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT).
    
    Returns:
        str: Stock price if successful, otherwise "N/A".
    """
    alpha_vantage_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(alpha_vantage_url)
        data = response.json()
        
        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            return data["Global Quote"]["05. price"]
        else:
            print(f"No price data for {symbol}. Full response: {data}")
            raise Exception("Alpha Vantage API rate limit hit or no data.")
    
    except Exception as e:
        print(f"Error fetching stock data from Alpha Vantage for {symbol}: {e}")
        return fetch_from_yahoo_finance(symbol)

def fetch_from_yahoo_finance(symbol):
    """
    Fetches real-time stock data from Yahoo Finance as a fallback using yfinance.
    
    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT).
    
    Returns:
        str: Stock price if successful, otherwise "N/A".
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            print(f"Fetched price for {symbol} from Yahoo Finance: {price}")
            return f"{price:.2f}"
        else:
            print(f"No historical data available for {symbol}")
            return "N/A"
    except Exception as e:
        print(f"Error fetching stock data from Yahoo Finance for {symbol}: {e}")
        return "N/A"

def create_stock_ticker(stock_frame, root):
    """
    Creates a scrolling ticker that displays stock prices.
    
    Args:
        stock_frame (ttkb.Frame): The frame where the ticker will be displayed.
        root (ttkb.Window): Tkinter root window.
    """
    stock_label = ttkb.Label(stock_frame, font=("Helvetica", 14), anchor="w")
    stock_label.pack(side="left", fill="x", expand=True)

    def get_ticker_text():
        """
        Fetches stock prices and creates a ticker text string.
        
        Returns:
            str: Stock symbols and their corresponding prices formatted for ticker display.
        """
        ticker_text = ""
        for symbol in STOCKS:
            price = fetch_stock_price(symbol)
            ticker_text += f"{symbol}: ${price}  |  "
        return ticker_text

    def scroll_ticker():
        """
        Scrolls the stock ticker from right to left.
        """
        current_text = stock_label.cget("text")
        stock_label.config(text=current_text[1:] + current_text[0])  # Scroll text
        root.after(50, scroll_ticker)

    # Initialize the ticker with the stock data
    ticker_text = get_ticker_text()
    stock_label.config(text=ticker_text)
    
    scroll_ticker()  # Start scrolling

def create_stock_ticker_frame(root):
    """
    Creates a stock ticker frame at the bottom of the screen.

    Args:
        root (ttkb.Window): The root window.
    """
    stock_frame = ttkb.Frame(root, padding=10, bootstyle="info")
    stock_frame.pack(side="bottom", fill="x")
    create_stock_ticker(stock_frame, root)
