# StreamPulse

StreamPulse is a dynamic news and stock ticker display application designed for live streaming. It scrapes multiple RSS news feeds across different categories and displays stories in a visually appealing, quadrant-based layout. Additionally, it provides real-time stock prices using the Alpha Vantage and Yahoo Finance APIs, making it perfect for capturing with OBS for live streaming purposes.

## Features

- **News Feeds**: Displays stories from categories like General, Financial, Video Games, and Science/Tech, dynamically updating them in their respective quadrants.
- **Stock Ticker**: Real-time stock prices displayed in a scrolling ticker at the bottom of the screen, utilizing fallback support to Yahoo Finance in case Alpha Vantage's API limit is hit.
- **UI Design**: Optimized for full-screen display on a 1080p monitor, with transitions between news stories and a smooth-scrolling stock ticker for an enhanced visual experience.
  
## Recent Improvements

- **Smooth Scrolling Stock Ticker**: The stock ticker now scrolls across the bottom of the screen, ensuring that all stock prices are visible without requiring manual scrolling. The ticker speed can be easily adjusted for a smoother display, and fallback to Yahoo Finance ensures reliability even when the Alpha Vantage API hits its request limit.
- **Yahoo Finance Fallback**: If Alpha Vantage’s API rate limit is reached, the application seamlessly switches to Yahoo Finance for retrieving stock data. This guarantees continuous updates without interruptions.
- **Improved Responsiveness**: The overall UI responsiveness has been enhanced to ensure smooth transitions between news stories and a visually appealing experience for viewers.

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ProhibitedTV/StreamPulse.git
   cd StreamPulse
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Windows, use 'venv\Scripts\activate'
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the Alpha Vantage API Key**:
   - Create a `.env` file in the root directory and add your Alpha Vantage API key:
     ```bash
     ALPHA_VANTAGE_API_KEY=your_api_key_here
     ```

## Running the Application

To run the application:
```bash
python main.py
```

## Stock Ticker Customization

The stock ticker scrolls smoothly across the bottom of the screen, and its speed can be adjusted by modifying the `scroll_ticker` function in `stock_ticker.py`. You can also add or remove stock symbols by modifying the `STOCKS` list in `stock_ticker.py`.

## Adding Feeds

You can manage the RSS feeds in the `feeds.py` file. Simply add or remove feeds by modifying the appropriate category lists.

## License

This project is licensed under the MIT License.