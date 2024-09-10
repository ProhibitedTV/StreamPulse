import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from ui.loading_screen import show_loading_screen
import ttkbootstrap as ttkb

class TestLoadingScreen(unittest.TestCase):

    @patch('ui.loading_screen.load_feeds')
    @patch('ui.loading_screen.fetch_stock_price')
    @patch('ui.loading_screen.run_in_thread')
    def test_show_loading_screen(self, mock_run_in_thread, mock_fetch_stock_price, mock_load_feeds):
        """
        Test that the loading screen displays properly and that the progress bar and messages are updated as expected.
        """

        # Mock root Tkinter window
        mock_root = MagicMock()

        # Mock the 'on_complete' function
        mock_on_complete = MagicMock()

        # Call the loading screen function
        show_loading_screen(mock_root, mock_on_complete)

        # Assertions to verify that a loading screen is created
        mock_root.withdraw.assert_called_once()  # Check that the root window is withdrawn
        self.assertTrue(mock_run_in_thread.called)  # Ensure threading is used to prevent blocking the UI

        # Check that the stock prices were fetched and feeds loaded correctly
        self.assertTrue(mock_fetch_stock_price.called)
        self.assertTrue(mock_load_feeds.called)

    @patch('ui.loading_screen.update_progress')
    def test_update_progress(self, mock_update_progress):
        """
        Test that the progress bar updates correctly with the provided values.
        """
        # Mock root Tkinter window
        mock_root = MagicMock()

        # Create a fake loading screen
        mock_loading_screen = tk.Toplevel(mock_root)
        mock_progress_var = tk.DoubleVar()

        # Simulate progress updates
        show_loading_screen(mock_root, lambda: None)

        # Update the progress
        show_loading_screen.update_progress(50, "Loading half complete")
        mock_update_progress.assert_called_with(50, "Loading half complete")

    @patch('ui.loading_screen.run_in_thread')
    @patch('ui.loading_screen.fetch_stock_price')
    def test_load_stock_data(self, mock_fetch_stock_price, mock_run_in_thread):
        """
        Test the stock data loading progress and status updates.
        """

        # Mock root and stock data
        mock_root = MagicMock()

        # Mock stock symbols
        mock_symbols = ['AAPL', 'GOOGL', 'MSFT']

        # Patch the global STOCKS with test symbols
        with patch('ui.loading_screen.STOCKS', mock_symbols):
            show_loading_screen(mock_root, lambda: None)

            # Ensure stock prices are fetched
            for symbol in mock_symbols:
                mock_fetch_stock_price.assert_any_call(symbol)  # Verify each symbol's price is fetched

    @patch('ui.loading_screen.run_in_thread')
    @patch('ui.loading_screen.load_feeds')
    def test_load_feeds(self, mock_load_feeds, mock_run_in_thread):
        """
        Test the feed loading process and its progress updates.
        """
        # Mock root Tkinter window
        mock_root = MagicMock()

        # Call the loading screen
        show_loading_screen(mock_root, lambda: None)

        # Check that the feed loading function was called correctly
        self.assertTrue(mock_load_feeds.called)

if __name__ == '__main__':
    unittest.main()
