import pandas as pd
import requests
from io import StringIO
import logging
from collections import defaultdict
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_ghcn_inventory():
    url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching inventory data: {e}")
        return None

def parse_ghcn_inventory(raw_data):
    colspecs = [(0, 11), (12, 20), (21, 30), (31, 35), (36, 40), (41, 45)]
    names = ['ID', 'LATITUDE', 'LONGITUDE', 'ELEMENT', 'FIRSTYEAR', 'LASTYEAR']
    try:
        df = pd.read_fwf(StringIO(raw_data), colspecs=colspecs, header=None, names=names)
        return df
    except Exception as e:
        logging.error(f"Error parsing inventory data: {e}")
        return None

def fetch_station_data(station_id):
    url = f"https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/{station_id}.csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching data for station {station_id}: {e}")
        return None

def analyze_data_format(raw_data, station_id):
    lines = raw_data.split('\n')
    if not lines:
        return "Empty file"

    first_line = lines[0].strip().split(',')
    num_columns = len(first_line)

    if num_columns == 7:
        return "Standard GHCN format: ID, DATE, ELEMENT, VALUE, MFLAG, QFLAG, SFLAG"
    elif num_columns > 7:
        if station_id.startswith('ASN'):
            return f"Australian format: ID, YEAR, MONTH, ELEMENT, VALUE1-VALUE31, FLAG1-FLAG31 (Total columns: {num_columns})"
        else:
            return f"Unknown wide format with {num_columns} columns"
    else:
        return f"Unknown format with {num_columns} columns"

def analyze_inventory_and_formats(num_samples_per_country=5):
    inventory_data = fetch_ghcn_inventory()
    if inventory_data is None:
        return

    inventory_df = parse_ghcn_inventory(inventory_data)
    if inventory_df is None:
        return

    # Group stations by country (first three characters of ID)
    stations_by_country = defaultdict(list)
    for _, row in inventory_df.iterrows():
        country_code = row['ID'][:3]
        stations_by_country[country_code].append(row['ID'])

    # Analyze sample stations from each country
    format_analysis = {}
    for country_code, stations in stations_by_country.items():
        sample_stations = random.sample(stations, min(num_samples_per_country, len(stations)))
        country_formats = []
        for station_id in sample_stations:
            raw_data = fetch_station_data(station_id)
            if raw_data:
                format_description = analyze_data_format(raw_data, station_id)
                country_formats.append((station_id, format_description))
        format_analysis[country_code] = country_formats

    return format_analysis

def print_format_analysis(format_analysis):
    print("GHCN Data Format Analysis:")
    print("==========================")
    for country_code, formats in format_analysis.items():
        print(f"\nCountry Code: {country_code}")
        for station_id, format_description in formats:
            print(f"  Station {station_id}: {format_description}")

if __name__ == "__main__":
    format_analysis = analyze_inventory_and_formats()
    if format_analysis:
        print_format_analysis(format_analysis)
    else:
        print("Failed to analyze GHCN data formats.")