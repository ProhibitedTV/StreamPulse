import ttkbootstrap as ttkb
from api.fetchers import fetch_stock_price, STOCKS

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
