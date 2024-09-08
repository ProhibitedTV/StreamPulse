import requests
import ttkbootstrap as ttkb
import tkinter as tk
from datetime import datetime
from pytz import timezone
import pytz

def fetch_us_debt():
    """
    Fetches the U.S. National Debt using the Treasury Fiscal Data API.

    Returns:
        str: Formatted U.S. national debt amount or "Data Unavailable" if an error occurs.
    """
    try:
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mspd/mspd_debt"
        response = requests.get(url)
        data = response.json()

        if 'data' in data and len(data['data']) > 0:
            latest_debt = data['data'][0]['tot_pub_debt_out_amt']
            return f"${float(latest_debt):,.2f}"  # Format the number with commas
        else:
            return "Data Unavailable"
    except Exception as e:
        print(f"Error fetching US national debt: {e}")
        return "Data Unavailable"

def fetch_global_co2_emissions():
    """
    Fetches global CO2 emissions data from the World Bank API.

    Returns:
        str: Formatted global CO2 emissions amount or "Data Unavailable" if an error occurs.
    """
    try:
        url = "https://api.worldbank.org/v2/country/WLD/indicator/EN.ATM.CO2E.KT?format=json"
        response = requests.get(url)
        data = response.json()

        # Ensure valid data is present before formatting
        if response.status_code == 200 and len(data) > 1 and 'value' in data[1][0]:
            co2 = data[1][0]['value']
            return f"{co2:,} kt CO2" if co2 is not None else "Data Unavailable"
        else:
            return "Data Unavailable"
    except Exception as e:
        print(f"Error fetching global CO2 emissions: {e}")
        return "Data Unavailable"

def add_global_stats(global_stats_frame):
    """
    Adds global statistics such as U.S. National Debt and Global CO2 Emissions to the provided Tkinter frame.

    Args:
        global_stats_frame (ttkb.Frame): The frame where the stats will be displayed.
    """
    global_stats_label = ttkb.Label(global_stats_frame, text="Global Stats", font=("Helvetica", 18, "bold"))
    global_stats_label.pack(pady=10)

    # US National Debt section
    us_debt_label = ttkb.Label(global_stats_frame, text="US National Debt: Fetching...", font=("Helvetica", 14))
    us_debt_label.pack(pady=5)

    def update_us_debt():
        us_debt = fetch_us_debt()
        us_debt_label.config(text=f"US National Debt: {us_debt}")
    
    update_us_debt()
    global_stats_frame.after(60000, update_us_debt)  # Update every 60 seconds

    # Global CO2 Emissions section
    co2_emission_label = ttkb.Label(global_stats_frame, text="Global CO2 Emissions: Fetching...", font=("Helvetica", 14))
    co2_emission_label.pack(pady=5)

    def update_global_co2_emissions():
        global_emission = fetch_global_co2_emissions()
        co2_emission_label.config(text=f"Global CO2 Emissions: {global_emission}")
    
    update_global_co2_emissions()
    global_stats_frame.after(60000, update_global_co2_emissions)  # Update every 60 seconds

def add_world_clock(clock_frame):
    """
    Adds a live world clock to the provided Tkinter frame that updates every second.

    Args:
        clock_frame (ttkb.Frame): The frame where the clocks will be displayed.
    """
    # List of cities and their time zones
    cities = {
        "New York": "America/New_York",
        "London": "Europe/London",
        "Tokyo": "Asia/Tokyo",
        "Sydney": "Australia/Sydney",
        "UTC": "UTC"
    }
    
    # 12-hour or 24-hour format toggle
    time_format_24hr = True  # Change to False for 12-hour format
    
    clock_label = ttkb.Label(clock_frame, text="World Clock", font=("Helvetica", 18, "bold"))
    clock_label.pack(pady=10)

    time_labels = {}
    
    for city in cities:
        city_label = ttkb.Label(clock_frame, text=f"{city}: Fetching...", font=("Helvetica", 14))
        city_label.pack(pady=5)
        time_labels[city] = city_label

    def update_time():
        now_utc = datetime.now(pytz.utc)
        for city, tz in cities.items():
            local_time = now_utc.astimezone(timezone(tz))
            if time_format_24hr:
                time_string = local_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_string = local_time.strftime('%Y-%m-%d %I:%M:%S %p')

            time_labels[city].config(text=f"{city}: {time_string}")
        
        # Refresh every second
        clock_frame.after(1000, update_time)

    update_time()