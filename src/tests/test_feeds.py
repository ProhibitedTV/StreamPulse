import unittest
from urllib.parse import urlparse
from src.ui.feeds import (
    GENERAL_RSS_FEEDS, FINANCIAL_RSS_FEEDS, 
    VIDEO_GAMES_RSS_FEEDS, SCIENCE_TECH_RSS_FEEDS, 
    HEALTH_ENVIRONMENT_RSS_FEEDS, ENTERTAINMENT_RSS_FEEDS
)

class TestRSSFeeds(unittest.TestCase):
    
    def validate_feed_list(self, feed_list, feed_type):
        """
        Helper method to validate RSS feed lists.
        
        :param feed_list: The list of RSS feed URLs to validate.
        :param feed_type: A string representing the type of feed (used for error messages).
        """
        self.assertIsInstance(feed_list, list, f"{feed_type} RSS feed list should be a list.")
        self.assertGreater(len(feed_list), 0, f"{feed_type} RSS feed list should not be empty.")
        
        for feed_url in feed_list:
            with self.subTest(feed_url=feed_url):
                self.assertIsInstance(feed_url, str, f"Each feed URL in {feed_type} should be a string.")
                parsed_url = urlparse(feed_url)
                self.assertTrue(parsed_url.scheme in ["http", "https"], f"Invalid URL scheme in {feed_url}")
                self.assertTrue(parsed_url.netloc, f"Invalid domain in {feed_url}")
                self.assertTrue(parsed_url.path, f"URL path is missing in {feed_url}")

    def test_general_rss_feeds(self):
        """Test the validity of General News RSS feeds."""
        self.validate_feed_list(GENERAL_RSS_FEEDS, "General")

    def test_financial_rss_feeds(self):
        """Test the validity of Financial News RSS feeds."""
        self.validate_feed_list(FINANCIAL_RSS_FEEDS, "Financial")
    
    def test_video_games_rss_feeds(self):
        """Test the validity of Video Games RSS feeds."""
        self.validate_feed_list(VIDEO_GAMES_RSS_FEEDS, "Video Games")

    def test_science_tech_rss_feeds(self):
        """Test the validity of Science & Tech RSS feeds."""
        self.validate_feed_list(SCIENCE_TECH_RSS_FEEDS, "Science & Tech")

    def test_health_environment_rss_feeds(self):
        """Test the validity of Health & Environment RSS feeds."""
        self.validate_feed_list(HEALTH_ENVIRONMENT_RSS_FEEDS, "Health & Environment")

    def test_entertainment_rss_feeds(self):
        """Test the validity of Entertainment RSS feeds."""
        self.validate_feed_list(ENTERTAINMENT_RSS_FEEDS, "Entertainment")

if __name__ == '__main__':
    unittest.main()
