import pandas as pd
from tqdm import tqdm
import logging
from precipgen.data.ghcn_data import GHCNData

# Configure logging to write to a file
logging.basicConfig(filename='ghcn_stations.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_inventory(file_path):
    """Read the inventory file and return a DataFrame."""
    columns = ["STATION", "LAT", "LONG", "TYPE", "BEGIN", "END"]
    data = []
    with open(file_path, 'r') as file:
        next(file)  # Skip the header line
        for line in file:
            parts = line.split()
            station = parts[0]
            lat = float(parts[1])
            long = float(parts[2])
            type_ = parts[3]
            begin = int(parts[4])
            end = int(parts[5])
            data.append([station, lat, long, type_, begin, end])
    return pd.DataFrame(data, columns=columns)

def get_climate_zones(zone_type):
    """Return the latitude and longitude ranges for the specified climate zone type."""
    climate_zones = {
        "arid": [
            {"lat_range": (25, 40), "long_range": (-125, -100)},  # Southwest USA
            {"lat_range": (-35, -25), "long_range": (115, 145)},  # Western/Central Australia
            {"lat_range": (-30, -15), "long_range": (15, 25)},    # Western Southern Africa
        ],
        "tropical": [
            {"lat_range": (-10, 10), "long_range": (-80, -50)},   # Amazon Basin
            {"lat_range": (-10, 10), "long_range": (100, 140)},   # Southeast Asia
            {"lat_range": (-10, 10), "long_range": (10, 40)},     # Central Africa
        ],
        "temperate": [
            {"lat_range": (30, 50), "long_range": (-100, -70)},   # Eastern USA
            {"lat_range": (40, 60), "long_range": (0, 30)},       # Western Europe
            {"lat_range": (30, 50), "long_range": (120, 150)},    # Eastern China
        ],
        # Add more climate zones as needed
    }
    
    return climate_zones.get(zone_type, [])

def filter_stations_by_climate_zone(df, zone_type):
    """Filter stations located in the specified climate zone with the required data types for at least 90 years, ending after Jan 1, 2024, starting on or before 1900, and > 95% coverage."""
    climate_zones = get_climate_zones(zone_type)
    
    def is_in_zone(lat, long):
        for area in climate_zones:
            if area["lat_range"][0] <= lat <= area["lat_range"][1] and area["long_range"][0] <= long <= area["long_range"][1]:
                return True
        return False

    zone_stations = df[df.apply(lambda row: is_in_zone(row["LAT"], row["LONG"]), axis=1)]
    
    # Group by station and filter based on the required data types and duration
    grouped = zone_stations.groupby("STATION")
    valid_stations = []
    
    # Wrap the loop with tqdm for progress bar, disable output
    progress_bar = tqdm(grouped, desc="Processing stations", disable=True)
    for station, group in progress_bar:
        types = set(group["TYPE"])
        if {"PRCP", "TMAX", "TMIN"}.issubset(types):
            min_begin = group["BEGIN"].min()
            max_end = group["END"].max()
            if max_end - min_begin >= 90 and max_end > 2023 and min_begin <= 1900:
                # Create a GHCNData object, fetch data, and check coverage
                ghcn_data = GHCNData()
                ghcn_data.fetch(station)
                coverage = ghcn_data.get_coverage()
                if coverage > 95:
                    valid_stations.append({
                        "STATION": station,
                        "LAT": group["LAT"].iloc[0],
                        "LONG": group["LONG"].iloc[0],
                        "BEGIN": min_begin,
                        "END": max_end,
                        "COVERAGE": coverage
                    })
                    # Update progress bar with the number of valid stations found
                    progress_bar.set_postfix(valid_stations=len(valid_stations))
                    logging.info(f"Valid stations found: {len(valid_stations)}")
    return valid_stations


def main():
    file_path = "C:\\Users\\jason\\Downloads\\ghcnd-inventory.txt"
    df = read_inventory(file_path)
    zone_type = "temperate"  # Change this to the desired climate zone type
    valid_stations = filter_stations_by_climate_zone(df, zone_type)
    
    if valid_stations:
        logging.info(f"Stations located in {zone_type} areas with PRCP, TMAX, and TMIN data for at least 90 years and > 90% coverage:")
        for station in valid_stations:
            logging.info(station)

if __name__ == "__main__":
    main()