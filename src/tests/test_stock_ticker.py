import unittest
from unittest.mock import patch, MagicMock
from ui.stock_ticker import create_stock_ticker, create_stock_ticker_frame
import ttkbootstrap as ttkb

class TestStockTicker(unittest.TestCase):

    @patch('ui.stock_ticker.fetch_stock_price')
    @patch('ui.stock_ticker.STOCKS', ['AAPL', 'GOOGL', 'MSFT'])
    def test_get_ticker_text(self, mock_fetch_stock_price):
        """Test that stock prices are fetched and ticker text is correctly formatted."""
        # Mock stock prices
        mock_fetch_stock_price.side_effect = [150.12, 2800.55, 300.78]

        # Create mock Tkinter frame and root
        mock_root = MagicMock()
        mock_stock_frame = MagicMock()

        # Call the function to create the stock ticker
        create_stock_ticker(mock_stock_frame, mock_root)

        # Check that stock prices were fetched correctly
        self.assertEqual(mock_fetch_stock_price.call_count, 3)  # Should be called for each stock

        # Extract the label and verify the text was set correctly
        ticker_text = "AAPL: $150.12  |  GOOGL: $2800.55  |  MSFT: $300.78  |  "
        mock_stock_frame.pack.assert_called_once()  # Ensure the label was packed
        self.assertIn(ticker_text, mock_stock_frame.children.values()[0].cget("text"))  # Check if the ticker text was set

    @patch('ui.stock_ticker.fetch_stock_price')
    @patch('ui.stock_ticker.STOCKS', ['AAPL'])
    @patch('ttkbootstrap.Frame')
    def test_create_stock_ticker_frame(self, mock_frame, mock_fetch_stock_price):
        """Test the creation of the stock ticker frame."""
        # Mock stock price for AAPL
        mock_fetch_stock_price.return_value = 150.12

        # Mock root Tkinter window
        mock_root = MagicMock()

        # Call the function to create the stock ticker frame
        create_stock_ticker_frame(mock_root)

        # Ensure the stock ticker frame is packed
        mock_frame.assert_called_once()
        self.assertTrue(mock_frame.return_value.pack.called)

        # Ensure the stock price was fetched and the ticker was initialized
        mock_fetch_stock_price.assert_called_once_with('AAPL')

    @patch('ui.stock_ticker.fetch_stock_price')
    @patch('ttkbootstrap.Frame')
    def test_scroll_ticker(self, mock_frame, mock_fetch_stock_price):
        """Test that the ticker scrolls correctly."""
        # Mock stock price for one stock
        mock_fetch_stock_price.return_value = 150.12

        # Mock root Tkinter window
        mock_root = MagicMock()
        mock_root.after = MagicMock()

        # Call the function to create the stock ticker
        create_stock_ticker(mock_frame, mock_root)

        # Simulate the scrolling of the ticker
        initial_text = "AAPL: $150.12  |  "
        stock_label = mock_frame.return_value.children.values()[0]
        stock_label.cget.return_value = initial_text
        create_stock_ticker(mock_frame, mock_root)

        # Ensure that the text scrolls as expected
        updated_text = initial_text[1:] + initial_text[0]
        stock_label.config.assert_called_with(text=updated_text)
        mock_root.after.assert_called()

if __name__ == '__main__':
    unittest.main()
