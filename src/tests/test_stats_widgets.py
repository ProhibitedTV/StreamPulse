import unittest
from unittest.mock import patch, MagicMock
from ui.stats_widgets import fetch_us_debt, fetch_global_co2_emissions, add_global_stats, add_world_clock
import requests


class TestStatsWidgets(unittest.TestCase):

    @patch('ui.stats_widgets.requests.get')
    def test_fetch_us_debt_success(self, mock_get):
        """Test successful fetching of U.S. National Debt data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [{'tot_pub_debt_out_amt': '28200000000000.00'}]
        }
        mock_get.return_value = mock_response

        result = fetch_us_debt()
        self.assertEqual(result, "$28,200,000,000,000.00")

    @patch('ui.stats_widgets.requests.get')
    def test_fetch_us_debt_failure(self, mock_get):
        """Test failure when fetching U.S. National Debt data."""
        mock_get.side_effect = requests.RequestException("Error fetching data")
        result = fetch_us_debt()
        self.assertEqual(result, "Data Unavailable")

    @patch('ui.stats_widgets.requests.get')
    def test_fetch_global_co2_emissions_success(self, mock_get):
        """Test successful fetching of Global CO2 emissions."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {}, [{'value': 35000000}]
        ]
        mock_get.return_value = mock_response

        result = fetch_global_co2_emissions()
        self.assertEqual(result, "35,000,000 kt CO2")

    @patch('ui.stats_widgets.requests.get')
    def test_fetch_global_co2_emissions_no_data(self, mock_get):
        """Test no data case when fetching Global CO2 emissions."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{}, []]
        mock_get.return_value = mock_response

        result = fetch_global_co2_emissions()
        self.assertEqual(result, "Data Unavailable")

    @patch('ui.stats_widgets.requests.get')
    def test_fetch_global_co2_emissions_failure(self, mock_get):
        """Test failure case when fetching Global CO2 emissions."""
        mock_get.side_effect = requests.RequestException("Error fetching data")
        result = fetch_global_co2_emissions()
        self.assertEqual(result, "Data Unavailable")

    @patch('ui.stats_widgets.run_in_thread')
    @patch('ui.stats_widgets.fetch_us_debt', return_value="$28,200,000,000,000.00")
    @patch('ttkbootstrap.Frame')
    def test_add_global_stats(self, mock_frame, mock_fetch_us_debt, mock_run_in_thread):
        """Test adding global stats to a Tkinter frame."""
        add_global_stats(mock_frame)
        self.assertTrue(mock_run_in_thread.called)
        self.assertTrue(mock_fetch_us_debt.called)

    @patch('ui.stats_widgets.run_in_thread')
    @patch('ui.stats_widgets.fetch_global_co2_emissions', return_value="35,000,000 kt CO2")
    @patch('ttkbootstrap.Frame')
    def test_add_global_stats_co2(self, mock_frame, mock_fetch_global_co2_emissions, mock_run_in_thread):
        """Test adding global CO2 stats to a Tkinter frame."""
        add_global_stats(mock_frame)
        self.assertTrue(mock_run_in_thread.called)
        self.assertTrue(mock_fetch_global_co2_emissions.called)

    @patch('ttkbootstrap.Frame')
    @patch('ui.stats_widgets.datetime')
    @patch('ui.stats_widgets.timezone')
    def test_add_world_clock(self, mock_timezone, mock_datetime, mock_frame):
        """Test adding world clock to a Tkinter frame."""
        mock_now = MagicMock()
        mock_now.astimezone.return_value.strftime.return_value = "2024-09-01 12:00:00"
        mock_datetime.now.return_value = mock_now

        add_world_clock(mock_frame)
        mock_now.astimezone.assert_called()  # Verify that astimezone was called
        self.assertTrue(mock_frame.after.called)  # Ensure that the clock updates continuously


if __name__ == '__main__':
    unittest.main()
