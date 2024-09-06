# StreamPulse
StreamPulse is a dynamic news and stock ticker display application designed for live streaming. It scrapes multiple RSS news feeds across different categories and displays stories in a visually appealing way, while also fetching real-time stock prices using the Alpha Vantage API.

## Features
- **News Feeds**: Displays stories from categories like General, Financial, Video Games, and Science/Tech.
- **Stock Ticker**: Real-time stock prices.
- **UI Design**: Optimized for full-screen display on a 1080p monitor.

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

## Adding Feeds
You can manage the RSS feeds in the `feeds.py` file. Simply add or remove feeds by modifying the appropriate category lists.

## License
This project is licensed under the MIT License.