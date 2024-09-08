import unittest
from unittest.mock import patch
import sys
import os

# Add src directory to the system path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from stats_widgets import fetch_us_debt, fetch_global_co2_emissions

class TestStatsWidgets(unittest.TestCase):

    @patch('stats_widgets.requests.get')
    def test_fetch_us_debt_success(self, mock_get):
        # Mock a successful API response
        mock_response = {
            'data': [
                {'tot_pub_debt_out_amt': '33000000000000'}
            ]
        }
        mock_get.return_value.json.return_value = mock_response
        
        result = fetch_us_debt()
        self.assertEqual(result, "$33,000,000,000,000.00")

    @patch('stats_widgets.requests.get')
    def test_fetch_us_debt_failure(self, mock_get):
        # Mock an unsuccessful API response
        mock_get.side_effect = Exception("API Error")
        
        result = fetch_us_debt()
        self.assertEqual(result, "Data Unavailable")

    @patch('stats_widgets.requests.get')
    def test_fetch_global_co2_emissions_success(self, mock_get):
        # Mock a successful API response
        mock_response = [
            {},  # The first element is metadata in the World Bank API response
            [{'value': 36000000}]
        ]
        mock_get.return_value.json.return_value = mock_response
        
        result = fetch_global_co2_emissions()
        self.assertEqual(result, "36,000,000 kt CO2")

    @patch('stats_widgets.requests.get')
    def test_fetch_global_co2_emissions_failure(self, mock_get):
        # Mock an unsuccessful API response
        mock_get.side_effect = Exception("API Error")
        
        result = fetch_global_co2_emissions()
        self.assertEqual(result, "Data Unavailable")

if __name__ == '__main__':
    unittest.main()
