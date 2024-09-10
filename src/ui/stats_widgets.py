import requests
import logging
from datetime import datetime
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from pytz import timezone
import pytz
from utils.threading import run_in_thread

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_us_debt():
    """
    Fetches the U.S. National Debt using the Treasury Fiscal Data API.

    Returns:
        str: Formatted U.S. national debt amount or "Data Unavailable" if an error occurs.
    """
    try:
        logging.info("Fetching U.S. National Debt data...")
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mspd/mspd_debt"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'data' in data and len(data['data']) > 0:
            latest_debt = data['data'][0]['tot_pub_debt_out_amt']
            debt_formatted = f"${float(latest_debt):,.2f}"
            logging.info(f"Fetched U.S. National Debt: {debt_formatted}")
            return debt_formatted
        else:
            logging.error("Debt data unavailable in the response.")
            return "Data Unavailable"

    except requests.exceptions.RequestException as e:
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
        url = "https://api.worldbank.org/v2/country/WLD/indicator/EN.ATM.CO2E.KT?format=json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if response.status_code == 200 and len(data) > 1 and 'value' in data[1][0]:
            co2 = data[1][0]['value']
            co2_formatted = f"{co2:,} kt CO2" if co2 is not None else "Data Unavailable"
            logging.info(f"Fetched Global CO2 Emissions: {co2_formatted}")
            return co2_formatted
        else:
            logging.error("CO2 emissions data unavailable in the response.")
            return "Data Unavailable"

    except Exception as e:
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
        logging.info("Updating U.S. National Debt information...")
        us_debt = fetch_us_debt()
        if us_debt_label and us_debt_label.isVisible():
            us_debt_label.setText(f"US National Debt: {us_debt}")
            logging.info(f"U.S. National Debt updated: {us_debt}")

    def update_global_co2_emissions():
        """Updates the Global CO2 Emissions label with fetched data."""
        logging.info("Updating Global CO2 Emissions information...")
        global_emission = fetch_global_co2_emissions()
        if co2_emission_label and co2_emission_label.isVisible():
            co2_emission_label.setText(f"Global CO2 Emissions: {global_emission}")
            logging.info(f"Global CO2 Emissions updated: {global_emission}")

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

    time_format_24hr = True  # Set time format; change to False for 12-hour format

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
        if not world_clock_widget.isVisible():
            logging.warning("World clock widget is not visible. Stopping clock updates.")
            return

        now_utc = datetime.now(pytz.utc)
        for city, tz in cities.items():
            local_time = now_utc.astimezone(timezone(tz))
            time_string = local_time.strftime('%Y-%m-%d %H:%M:%S') if time_format_24hr else local_time.strftime('%Y-%m-%d %I:%M:%S %p')

            logging.debug(f"Attempting to update time for {city}: {time_string}")

            # Ensure the QLabel still exists and is visible
            if city in time_labels and time_labels[city] is not None and time_labels[city].isVisible():
                try:
                    time_labels[city].setText(f"{city}: {time_string}")
                    logging.debug(f"Updated time for {city}: {time_string}")
                except RuntimeError as e:
                    logging.error(f"Error updating time label for {city}: {e}")
            else:
                logging.warning(f"Label for {city} is not visible, deleted, or doesn't exist.")

        # Refresh the time every second
        QTimer.singleShot(1000, update_time)

    # Start the clock updates
    logging.info("Starting world clock updates...")
    update_time()

    return world_clock_widget
