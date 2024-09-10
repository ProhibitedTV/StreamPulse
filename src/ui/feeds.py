import logging
import time
from utils.threading import run_in_thread

# Logger for error tracking
logging.basicConfig(level=logging.INFO)

# Feed structure using a dictionary to categorize
RSS_FEEDS = {
    "general": [
        "http://rss.cnn.com/rss/edition_americas.rss",  
        "http://feeds.bbci.co.uk/news/world/rss.xml",  
        "https://www.npr.org/rss/rss.php?id=1001",  
        "https://feeds.washingtonpost.com/rss/world",  
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",  
        "https://www.theguardian.com/world/rss",  
        "https://news.un.org/feed/subscribe/en/news/all/rss.xml",  
        "https://www.aljazeera.com/xml/rss/all.xml",  
        "https://www.france24.com/en/rss",  
        "https://feeds.thelocal.com/rss/es"  
    ],
    "financial": [
        "https://www.investing.com/rss/news_25.rss",  
        "https://feeds.marketwatch.com/marketwatch/topstories",  
        "https://seekingalpha.com/feed.xml",  
        "https://www.fool.com/feeds/index.aspx",  
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",  
        "https://www.kiplinger.com/feed/all",  
        "https://www.bloomberg.com/feed/podcast/trillions.xml",  
        "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml",  
        "https://www.moneycontrol.com/rss/latestnews.xml",  
    ],
    "video_games": [
        "https://kotaku.com/rss",  
        "https://feeds.feedburner.com/Polygon",  
        "https://www.theverge.com/rss/frontpage",  
        "https://www.pcgamer.com/rss/",  
        "https://www.gamespot.com/feeds/news/",  
        "https://feeds.feedburner.com/RockPaperShotgun",  
        "https://www.eurogamer.net/?format=rss",  
        "https://www.reddit.com/r/gaming.rss",  
    ],
    "science_tech": [
        "https://techcrunch.com/feed/",  
        "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",  
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",  
        "https://www.tomshardware.com/feeds/all",  
        "https://www.wired.com/feed/rss",  
        "https://feeds.arstechnica.com/arstechnica/index/",  
        "https://www.engadget.com/rss.xml",  
        "https://www.newscientist.com/subject/space/feed/",  
    ],
    "health_environment": [
        "https://www.who.int/feeds/entity/csr/don/en/rss.xml",  
        "https://feeds.washingtonpost.com/rss/lifestyle/wellness",  
        "https://www.npr.org/rss/rss.php?id=1027",  
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",  
        "https://www.nationalgeographic.com/content/natgeo/en_us/rss/index.rss",  
        "https://www.climatechangenews.com/feed/",  
        "https://feeds.feedburner.com/theecologist",  
        "https://www.bbc.co.uk/news/science_and_environment/rss.xml",  
    ],
    "entertainment": [
        "https://variety.com/feed/",  
        "https://feeds.feedburner.com/ewallstreeter",  
        "https://www.tmz.com/rss.xml",  
        "https://www.hollywoodreporter.com/t/entertainment/feed/",  
        "https://rss.etonline.com/latest",  
        "https://www.vanityfair.com/feed/rss",  
        "https://www.billboard.com/feed",  
        "https://feeds.feedburner.com/slashfilm",  
        "https://www.reddit.com/r/movies.rss",  
    ]
}

def get_feeds_by_category(category):
    """
    Returns the RSS feeds of a given category. Logs an error if the category is not found.
    
    Args:
        category (str): Category of the RSS feeds ("general", "financial", etc.). Case-insensitive.
    
    Returns:
        list: List of RSS feed URLs for the category, or an empty list if the category is invalid.
    """
    category = category.lower().strip()  # Ensure case-insensitivity and trim spaces
    if category in RSS_FEEDS:
        logging.info(f"Fetching feeds for category: {category}")
        return RSS_FEEDS[category]
    else:
        valid_categories = ", ".join(RSS_FEEDS.keys())
        logging.error(f"Invalid feed category '{category}'. Valid categories are: {valid_categories}")
        return []

def load_feeds_in_thread(feed, update_progress, total_feeds, loaded_feeds):
    """
    Loads a single feed in a separate thread, simulating network delay, and updates the progress.

    Args:
        feed (str): The RSS feed URL to be loaded.
        update_progress (function): Function to update the progress bar.
        total_feeds (int): The total number of feeds to be loaded.
        loaded_feeds (list): A shared list to keep track of the number of loaded feeds.
    """
    try:
        time.sleep(0.5)  # Simulate network delay
        loaded_feeds[0] += 1
        progress = (loaded_feeds[0] / total_feeds) * 100
        update_progress(progress)  # Update progress bar
        logging.info(f"Loaded feed: {feed}")
    except Exception as e:
        logging.error(f"Error loading feed {feed}: {e}")

def load_feeds(main_frame, update_progress):
    """
    Loads all feeds concurrently using threads and updates the progress bar accordingly.
    
    Args:
        main_frame: The main frame where the feed content will be displayed.
        update_progress (function): Function to update the loading progress.
    """
    total_feeds = sum(len(feeds) for feeds in RSS_FEEDS.values())
    loaded_feeds = [0]  # Use a list to store the count of loaded feeds, so it can be updated by threads

    for category, feeds in RSS_FEEDS.items():
        for feed in feeds:
            # Start loading each feed in a separate thread
            run_in_thread(load_feeds_in_thread, feed, update_progress, total_feeds, loaded_feeds)
