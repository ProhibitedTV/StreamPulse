"""
stats_widgets.py

This module provides widgets for displaying real-time global statistics such as U.S. National Debt, 
Global CO2 Emissions, and a live world clock. These widgets are designed to integrate with the PyQt5 
interface and update dynamically through API calls.

Key Features:
- Fetches U.S. National Debt data from the U.S. Treasury API and displays it in a formatted label.
- Fetches global CO2 emissions data from the World Bank API and displays it in a formatted label.
- Provides a live world clock that updates every second for multiple cities and time zones.
- Implements retries and error handling to ensure robustness when fetching data from APIs.
- Utilizes background threads to fetch data asynchronously, avoiding blocking the UI.

Functions:
- fetch_with_retries: Fetches data from a given URL with retry logic for robustness.
- fetch_us_debt: Retrieves the U.S. National Debt from the Treasury API.
- fetch_global_co2_emissions: Retrieves global CO2 emissions from the World Bank API.
- create_global_stats_widget: Creates and returns a PyQt5 widget to display global stats.
- create_world_clock_widget: Creates and returns a PyQt5 widget to display a live world clock.
"""

import logging
import requests
from datetime import datetime
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from pytz import timezone
import pytz
from utils.threading import run_in_thread
import time

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for fetching URLs
US_DEBT_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
CO2_EMISSIONS_URL = "https://api.worldbank.org/v2/country/WLD/indicator/EN.ATM.CO2E.KT?format=json"

def fetch_with_retries(url, params=None, retries=3, delay=2):
    """
    Fetches data from a given URL with retries.

    Args:
        url (str): The URL to fetch data from.
        params (dict, optional): The parameters to pass with the request.
        retries (int): Number of retries to attempt.
        delay (int): Delay between retries.

    Returns:
        dict or None: The JSON response if successful, None otherwise.
    """
    for attempt in range(retries):
        try:
            logging.info(f"Fetching data from {url}, attempt {attempt + 1}...")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching data from {url}: {e}")
            if attempt < retries - 1:
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Failed to fetch data after {retries} attempts.")
    return None

def fetch_us_debt():
    """
    Fetches the U.S. National Debt using the Treasury Fiscal Data API.

    Returns:
        str: Formatted U.S. national debt amount or "Data Unavailable" if an error occurs.
    """
    try:
        logging.info("Fetching U.S. National Debt data...")
        params = {
            "fields": "tot_pub_debt_out_amt,record_date",
            "sort": "-record_date",
            "page[number]": 1,
            "page[size]": 1
        }
        data = fetch_with_retries(US_DEBT_URL, params=params)

        if data and 'data' in data and len(data['data']) > 0:
            latest_debt = data['data'][0]['tot_pub_debt_out_amt']
            record_date = data['data'][0]['record_date']
            debt_formatted = f"${float(latest_debt):,.2f} (As of {record_date})"
            logging.info(f"Fetched U.S. National Debt: {debt_formatted}")
            return debt_formatted
        else:
            logging.error("Debt data unavailable in the API response structure.")
            return "Data Unavailable"
    except Exception as e:
        logging.error(f"Error processing U.S. national debt: {e}")
        return "Data Unavailable"

def fetch_global_co2_emissions():
    """
    Fetches global CO2 emissions data from the World Bank API.

    Returns:
        str: Formatted global CO2 emissions amount or "Data Unavailable" if an error occurs.
    """
    try:
        logging.info("Fetching global CO2 emissions data...")
        data = fetch_with_retries(CO2_EMISSIONS_URL)

        if data and len(data) > 1 and 'value' in data[1][0]:
            co2 = data[1][0]['value']
            co2_formatted = f"{co2:,} kt CO2" if co2 is not None else "Data Unavailable"
            logging.info(f"Fetched Global CO2 Emissions: {co2_formatted}")
            return co2_formatted
        else:
            logging.error("CO2 emissions data unavailable in the response or malformed.")
            return "Data Unavailable"
    except Exception as e:
        logging.error(f"Error processing global CO2 emissions: {e}")
        return "Data Unavailable"

def create_global_stats_widget():
    logging.info("Setting up global statistics widget...")

    global_stats_widget = QWidget()
    layout = QVBoxLayout(global_stats_widget)

    # Add global stats label
    global_stats_label = QLabel("Global Stats", global_stats_widget)
    global_stats_label.setStyleSheet("font-size: 18px; font-weight: bold;")
    layout.addWidget(global_stats_label)

    # Add US National Debt label
    us_debt_label = QLabel("US National Debt: Fetching...", global_stats_widget)
    us_debt_label.setStyleSheet("font-size: 14px;")
    layout.addWidget(us_debt_label)

    # Add Global CO2 Emissions label
    co2_emission_label = QLabel("Global CO2 Emissions: Fetching...", global_stats_widget)
    co2_emission_label.setStyleSheet("font-size: 14px;")
    layout.addWidget(co2_emission_label)

    def update_us_debt():
        """Updates the U.S. National Debt label with fetched data."""
        us_debt = fetch_us_debt()
        us_debt_label.setText(f"US National Debt: {us_debt}")

    def update_global_co2_emissions():
        """Updates the Global CO2 Emissions label with fetched data."""
        global_emission = fetch_global_co2_emissions()
        co2_emission_label.setText(f"Global CO2 Emissions: {global_emission}")

    # Fetch data in background threads
    run_in_thread(update_us_debt)
    run_in_thread(update_global_co2_emissions)

    # Set up recurring updates every 60 seconds using QTimer
    debt_timer = QTimer()
    debt_timer.timeout.connect(lambda: run_in_thread(update_us_debt))
    debt_timer.start(60000)  # Update every 60 seconds

    co2_timer = QTimer()
    co2_timer.timeout.connect(lambda: run_in_thread(update_global_co2_emissions))
    co2_timer.start(60000)  # Update every 60 seconds

    return global_stats_widget

def create_world_clock_widget():
    """
    Creates and returns a widget displaying a live world clock with updates every second.

    Returns:
        QWidget: The world clock widget.
    """
    logging.info("Setting up world clock widget...")

    world_clock_widget = QWidget()
    layout = QVBoxLayout(world_clock_widget)

    # Define cities and time zones
    cities = {
        "New York": "America/New_York",
        "London": "Europe/London",
        "Tokyo": "Asia/Tokyo",
        "Sydney": "Australia/Sydney",
        "UTC": "UTC"
    }

    # Add world clock label
    clock_label = QLabel("World Clock", world_clock_widget)
    clock_label.setStyleSheet("font-size: 18px; font-weight: bold;")
    layout.addWidget(clock_label)

    # Create labels for each city
    time_labels = {}

    for city, tz in cities.items():
        city_label = QLabel(f"{city}: Fetching...", world_clock_widget)
        city_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(city_label)
        time_labels[city] = city_label

    def update_time():
        """Updates the time for each city."""
        now_utc = datetime.now(pytz.utc)
        for city, tz in cities.items():
            local_time = now_utc.astimezone(timezone(tz))
            time_string = local_time.strftime('%Y-%m-%d %H:%M:%S')
            time_labels[city].setText(f"{city}: {time_string}")

        # Refresh the time every second
        QTimer.singleShot(1000, update_time)

    # Start the clock updates
    update_time()

    return world_clock_widget
