import unittest
from unittest.mock import patch
from ui.feeds import get_feeds_by_category, load_feeds_in_thread, RSS_FEEDS
from utils.threading import run_in_thread
import time
from concurrent.futures import TimeoutError

class TestFeeds(unittest.TestCase):

    def test_get_feeds_by_valid_category(self):
        """Test fetching feeds for a valid category."""
        category = "general"
        feeds = get_feeds_by_category(category)
        self.assertEqual(feeds, RSS_FEEDS[category.lower()])

    def test_get_feeds_by_invalid_category(self):
        """Test fetching feeds for an invalid category."""
        category = "invalid_category"
        with self.assertLogs('root', level='ERROR') as log:
            feeds = get_feeds_by_category(category)
            self.assertEqual(feeds, [])
            self.assertIn("Invalid feed category", log.output[0])

    def test_get_feeds_by_category_case_insensitivity(self):
        """Test that categories are case insensitive."""
        category = "GENERAL"
        feeds = get_feeds_by_category(category)
        self.assertEqual(feeds, RSS_FEEDS[category.lower()])

    @patch('time.sleep', return_value=None)  # Mock sleep to avoid delays in the test
    def test_load_feeds_in_thread(self, mock_sleep):
        """Test loading a feed in a thread and updating progress."""
        loaded_feeds = [0]
        total_feeds = len(RSS_FEEDS["general"])

        def update_progress(progress):
            """Mock function to simulate progress update."""
            self.assertTrue(0 <= progress <= 100)

        # Use run_in_thread to load feeds in background threads
        futures = []
        for feed in RSS_FEEDS["general"]:
            future = run_in_thread(load_feeds_in_thread, feed, update_progress, total_feeds, loaded_feeds)
            futures.append(future)

        # Wait for all futures to complete with a timeout
        try:
            for future in futures:
                future.result(timeout=5)  # Set a 5-second timeout for each thread
        except TimeoutError:
            self.fail("Thread execution timed out")

        # Check that the loaded feeds counter is updated correctly
        self.assertEqual(loaded_feeds[0], len(RSS_FEEDS["general"]))

if __name__ == '__main__':
    unittest.main()
