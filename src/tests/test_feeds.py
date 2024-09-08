import unittest
from urllib.parse import urlparse
from ui.feeds import (GENERAL_RSS_FEEDS, FINANCIAL_RSS_FEEDS, 
                      VIDEO_GAMES_RSS_FEEDS, SCIENCE_TECH_RSS_FEEDS, 
                      HEALTH_ENVIRONMENT_RSS_FEEDS, ENTERTAINMENT_RSS_FEEDS)

class TestRSSFeeds(unittest.TestCase):
    
    def validate_feed_list(self, feed_list):
        self.assertIsInstance(feed_list, list, "RSS feed list should be of type list.")
        self.assertGreater(len(feed_list), 0, "RSS feed list should not be empty.")
        for feed_url in feed_list:
            self.assertIsInstance(feed_url, str, "Each feed URL should be a string.")
            parsed_url = urlparse(feed_url)
            self.assertTrue(parsed_url.scheme in ["http", "https"], f"Invalid URL scheme in {feed_url}")
            self.assertTrue(parsed_url.netloc, f"Invalid URL domain in {feed_url}")
    
    def test_general_rss_feeds(self):
        self.validate_feed_list(GENERAL_RSS_FEEDS)

    def test_financial_rss_feeds(self):
        self.validate_feed_list(FINANCIAL_RSS_FEEDS)
    
    def test_video_games_rss_feeds(self):
        self.validate_feed_list(VIDEO_GAMES_RSS_FEEDS)

    def test_science_tech_rss_feeds(self):
        self.validate_feed_list(SCIENCE_TECH_RSS_FEEDS)

    def test_health_environment_rss_feeds(self):
        self.validate_feed_list(HEALTH_ENVIRONMENT_RSS_FEEDS)

    def test_entertainment_rss_feeds(self):
        self.validate_feed_list(ENTERTAINMENT_RSS_FEEDS)

if __name__ == '__main__':
    unittest.main()
