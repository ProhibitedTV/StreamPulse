import unittest
from unittest.mock import patch
from src.ui.stats_widgets import fetch_us_debt, fetch_global_co2_emissions

class TestStatsWidgets(unittest.TestCase):
    """
    Unit test class for testing stats widgets functionalities, including fetching US debt
    and global CO2 emissions.
    """

    @patch('ui.stats_widgets.requests.get')
    def test_fetch_us_debt(self, mock_get):
        """
        Test the fetch_us_debt function.

        Mocks the API response to simulate fetching US national debt
        and asserts that the function returns the expected formatted debt value.
        """
        # Mock response simulating the US debt API
        mock_response = {
            'data': [{
                'tot_pub_debt_out_amt': '28000000000000'
            }]
        }
        mock_get.return_value.json.return_value = mock_response

        # Run the function and assert the formatted output
        result = fetch_us_debt()
        self.assertEqual(result, "$28,000,000,000,000.00")  # Adjusted to match formatted output

    @patch('ui.stats_widgets.requests.get')
    def test_fetch_global_co2_emissions(self, mock_get):
        """
        Test the fetch_global_co2_emissions function.

        Mocks the API response to simulate fetching global CO2 emissions data
        and asserts that the function returns the expected formatted CO2 value.
        """
        # Mock response simulating the World Bank CO2 API
        mock_response = [
            {},  # Metadata
            [{'value': 36440000}]  # Actual data
        ]
        mock_get.return_value.json.return_value = mock_response

        # Run the function and assert the formatted output
        result = fetch_global_co2_emissions()
        self.assertEqual(result, "36,440,000 kt CO2")  # Adjusted to match formatted output

if __name__ == '__main__':
    unittest.main()
