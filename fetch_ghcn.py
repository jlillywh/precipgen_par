import requests
import logging
from typing import Optional

def fetch_ghcn_data(station_id: str) -> Optional[str]:
    base_url = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/"
    url = f"{base_url}{station_id}.csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None

def fetch_ghcn_stations() -> Optional[str]:
    url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching stations data: {e}")
        return None