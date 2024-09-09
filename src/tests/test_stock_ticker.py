import unittest
from unittest.mock import patch
import pandas as pd
from src.api.stock_ticker import fetch_stock_price, fetch_from_yahoo_finance

class TestStockTicker(unittest.TestCase):
    """
    Unit test class for testing stock ticker functionalities, including fetching stock prices
    from Alpha Vantage and Yahoo Finance.
    """

    def setUp(self):
        """
        Reset the alpha_vantage_failed flag before each test to ensure that 
        Alpha Vantage is retried for each new test run.
        """
        global alpha_vantage_failed
        alpha_vantage_failed = False

    @patch('api.stock_ticker.requests.get')
    def test_fetch_stock_price_alpha_success(self, mock_get):
        """
        Test the fetch_stock_price function with a successful response from Alpha Vantage.
        
        Mocks the Alpha Vantage API response to simulate fetching a stock price and asserts 
        that the function returns the correct price.
        """
        mock_response = {
            "Global Quote": {
                "05. price": "145.23"
            }
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        result = fetch_stock_price("AAPL")
        self.assertEqual(result, "145.23")

    @patch('api.stock_ticker.requests.get')
    @patch('api.stock_ticker.fetch_from_yahoo_finance')
    def test_fetch_stock_price_alpha_failure_yahoo_success(self, mock_yahoo, mock_get):
        """
        Test the fetch_stock_price function when Alpha Vantage fails, 
        and it falls back to Yahoo Finance.

        Mocks an API failure in Alpha Vantage and asserts that the function successfully
        falls back to Yahoo Finance to retrieve the stock price.
        """
        mock_get.side_effect = Exception("API Error")
        mock_yahoo.return_value = "150.00"

        result = fetch_stock_price("AAPL")
        self.assertEqual(result, "150.00")

    @patch('api.stock_ticker.yf.Ticker')
    def test_fetch_from_yahoo_finance_success(self, mock_ticker):
        """
        Test the fetch_from_yahoo_finance function with a successful response.

        Mocks the Yahoo Finance API response to simulate fetching historical stock prices
        and asserts that the function returns the correct stock price.
        """
        mock_history = pd.DataFrame({
            'Close': [150.50]
        })
        mock_ticker.return_value.history.return_value = mock_history

        result = fetch_from_yahoo_finance("AAPL")
        self.assertEqual(result, "150.50")

    @patch('api.stock_ticker.yf.Ticker')
    def test_fetch_from_yahoo_finance_failure(self, mock_ticker):
        """
        Test the fetch_from_yahoo_finance function with a failure in Yahoo Finance.

        Mocks an API failure in Yahoo Finance and asserts that the function returns "N/A"
        when no data is available.
        """
        mock_ticker.side_effect = Exception("API Error")

        result = fetch_from_yahoo_finance("AAPL")
        self.assertEqual(result, "N/A")

if __name__ == '__main__':
    unittest.main()
