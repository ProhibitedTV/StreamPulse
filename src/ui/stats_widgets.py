"""
ui/stats_widgets.py

This module provides widgets for displaying global statistics such as U.S. National Debt, Global CO2 Emissions,
and a live world clock. These widgets are designed to integrate with the PyQt5 interface and update dynamically
with real-time data.
"""

import logging
import requests
from datetime import datetime
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from pytz import timezone
import pytz
from utils.threading import run_in_thread

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for fetching URLs
US_DEBT_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
CO2_EMISSIONS_URL = "https://api.worldbank.org/v2/country/WLD/indicator/EN.ATM.CO2E.KT?format=json"


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
        response = requests.get(US_DEBT_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        logging.debug(f"U.S. National Debt API response: {data}")

        if 'data' in data and len(data['data']) > 0:
            latest_debt = data['data'][0]['tot_pub_debt_out_amt']
            record_date = data['data'][0]['record_date']
            debt_formatted = f"${float(latest_debt):,.2f} (As of {record_date})"
            logging.info(f"Fetched U.S. National Debt: {debt_formatted}")
            return debt_formatted
        else:
            logging.error("Debt data unavailable in the API response structure.")
            return "Data Unavailable"
    except requests.RequestException as e:
        logging.error(f"Error fetching U.S. national debt: {e}")
        return "Data Unavailable"


def fetch_global_co2_emissions():
    """
    Fetches global CO2 emissions data from the World Bank API.

    Returns:
        str: Formatted global CO2 emissions amount or "Data Unavailable" if an error occurs.
    """
    try:
        logging.info("Fetching global CO2 emissions data...")
        response = requests.get(CO2_EMISSIONS_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        logging.debug(f"World Bank CO2 API full response: {data}")

        if response.status_code == 200 and len(data) > 1 and 'value' in data[1][0]:
            co2 = data[1][0]['value']
            co2_formatted = f"{co2:,} kt CO2" if co2 is not None else "Data Unavailable"
            logging.info(f"Fetched Global CO2 Emissions: {co2_formatted}")
            return co2_formatted
        else:
            logging.error("CO2 emissions data unavailable in the response or malformed.")
            return "Data Unavailable"
    except requests.RequestException as e:
        logging.error(f"Error fetching global CO2 emissions: {e}")
        return "Data Unavailable"


def create_global_stats_widget():
    """
    Creates and returns a widget containing global statistics such as U.S. National Debt and Global CO2 Emissions.

    Returns:
        QWidget: The global stats widget.
    """
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
        if not global_stats_widget.isVisible():  # Ensure the widget is still visible before updating
            return
        us_debt = fetch_us_debt()
        us_debt_label.setText(f"US National Debt: {us_debt}")

    def update_global_co2_emissions():
        """Updates the Global CO2 Emissions label with fetched data."""
        if not global_stats_widget.isVisible():  # Ensure the widget is still visible before updating
            return
        global_emission = fetch_global_co2_emissions()
        co2_emission_label.setText(f"Global CO2 Emissions: {global_emission}")

    # Fetch data in background threads
    run_in_thread(update_us_debt)
    run_in_thread(update_global_co2_emissions)

    # Set up recurring updates every 60 seconds
    QTimer.singleShot(60000, lambda: run_in_thread(update_us_debt))
    QTimer.singleShot(60000, lambda: run_in_thread(update_global_co2_emissions))

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

    for city in cities:
        city_label = QLabel(f"{city}: Fetching...", world_clock_widget)
        city_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(city_label)
        time_labels[city] = city_label

    def update_time():
        """Updates the time for each city."""
        if not world_clock_widget.isVisible():  # Ensure the widget is still visible before updating
            return

        now_utc = datetime.now(pytz.utc)
        for city, tz in cities.items():
            if city not in time_labels:
                continue
            local_time = now_utc.astimezone(timezone(tz))
            time_string = local_time.strftime('%Y-%m-%d %H:%M:%S')
            if time_labels[city]:  # Check if the label still exists
                time_labels[city].setText(f"{city}: {time_string}")

        # Refresh the time every second
        QTimer.singleShot(1000, update_time)

    # Start the clock updates
    update_time()

    return world_clock_widget
