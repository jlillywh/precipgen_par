import requests
from math import radians, sin, cos, sqrt, atan2
import time
from requests.exceptions import RequestException
from tqdm import tqdm
import json
import sys
from datetime import datetime, timedelta

# ABANDONED CODE 
#
# Decided that noaa ghcn dataset download is better for the project
#
# ABANDONED CODE 

# Your NOAA API Token
token = 'epYpWKsbKCJPAoLnGLSZrjykTwfmkHrc'
station_id = 'GHCND:USW00024233'

# Set up the API endpoint
base_url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/'

# Set headers with your token
# VIDEO: Note that Claude sent me on a wild goose chase telling me to make 'token' be 'Token' but it should be 'token'
headers = {'token': token}

# Rate limiting variables
request_count = 0
last_request_time = time.time()
last_reset_time = time.time()

def make_request_with_rate_limiting(url, params=None):
    global request_count, last_request_time, last_reset_time
    
    current_time = time.time()

    # Reset request count if 24 hours have passed
    if current_time - last_reset_time >= 86400:  # 86400 seconds in 24 hours
        request_count = 0
        last_reset_time = current_time

    # Check daily limit
    if request_count >= 10000:
        raise Exception("Daily request limit reached")
    
    # Ensure time between requests is compliant with rate limit
    time_since_last_request = current_time - last_request_time
    if time_since_last_request < 0.2:  # 200ms
        time.sleep(0.2 - time_since_last_request)
        print(f"Request rate is limited. Sleeping for {0.2 - time_since_last_request:.2f} seconds...")
    
    # Make the API request
    response = requests.get(url, headers=headers, params=params)
    
    # Update request count and last request time
    request_count += 1
    last_request_time = time.time()
    
    return response

def check_noaa_api_status():
    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets"
    headers = {'token': 'epYpWKsbKCJPAoLnGLSZrjykTwfmkHrc'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text[:500]}...")  # Print first 500 characters of response
        if response.status_code == 200:
            print("NOAA API is up and running.")
            return True
        else:
            print(f"NOAA API might be having issues. Status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Error connecting to NOAA API: {e}")
        return False

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def get_stations_within_radius(lat, lon, radius_km, max_retries=3, delay=5):
    stations_url = f'{base_url}stations'
    
    params = {
        'limit': 1000,
        'datasetid': 'GHCND',
        'extent': f'{lon-1},{lat-1},{lon+1},{lat+1}'
    }
    
    all_stations = []
    offset = 1
    
    print(f"Request URL: {stations_url}")
    print(f"Request Headers: {headers}")
    print(f"Request Parameters: {params}")
    
    with tqdm(desc="Fetching stations", unit=" stations") as pbar:
        while True:
            params['offset'] = offset
            for attempt in range(max_retries):
                try:
                    response = make_request_with_rate_limiting(stations_url, params)
                    
                    print(f"\nResponse Status Code: {response.status_code}")
                    print(f"Response Headers: {response.headers}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        print(f"\nAPI Response:\n{json.dumps(data, indent=2)}")
                        
                        if 'results' not in data:
                            print("\nNo 'results' field in the API response.")
                            return sorted(all_stations, key=lambda x: x['distance'])
                        
                        for station in data['results']:
                            distance = haversine_distance(lat, lon, float(station['latitude']), float(station['longitude']))
                            if distance <= radius_km:
                                station['distance'] = distance
                                all_stations.append(station)
                        
                        pbar.update(len(data['results']))
                        
                        if 'metadata' in data and 'resultset' in data['metadata']:
                            if data['metadata']['resultset']['offset'] + len(data['results']) >= data['metadata']['resultset']['count']:
                                return sorted(all_stations, key=lambda x: x['distance'])
                            else:
                                offset += len(data['results'])
                        else:
                            print("\nNo 'metadata' field in the API response. Assuming all data has been fetched.")
                            return sorted(all_stations, key=lambda x: x['distance'])
                    
                    elif response.status_code == 503:
                        print(f"\nServer unavailable. Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        print(f"\nUnexpected status code: {response.status_code}")
                        print(f"Response content: {response.text}")
                        response.raise_for_status()
                    
                except RequestException as e:
                    if attempt < max_retries - 1:
                        print(f"\nAn error occurred: {e}. Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        print(f"\nFailed after {max_retries} attempts. Last error: {e}")
                        raise
                
                break  # Break the retry loop if successful


def test_simple_request():
    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/datatypes"
    headers = {'token': 'epYpWKsbKCJPAoLnGLSZrjykTwfmkHrc'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text[:500]}...")
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error connecting to NOAA API: {e}")
        return False

# Example usage
if __name__ == "__main__":

    print("Testing simple request:")
    test_simple_request()
    
    if not check_noaa_api_status():
        print("Unable to proceed due to NOAA API issues. Please try again later.")
        sys.exit(1)

    try:
        latitude = 37.7749  # Example: San Francisco
        longitude = -122.4194
        radius = 50  # 50 km radius

        print(f"\nSearching for stations within {radius} km of coordinates ({latitude}, {longitude}):")
        stations = get_stations_within_radius(latitude, longitude, radius)

        print(f"\nFound {len(stations)} stations within the specified radius:")
        for station in stations:
            print(f"\nName: {station['name']}")
            print(f"ID: {station['id']}")
            print(f"Distance: {station['distance']:.2f} km")
            print(f"Latitude: {station['latitude']}, Longitude: {station['longitude']}")
            print(f"Elevation: {station.get('elevation', 'N/A')}")
    except Exception as e:
        print(f"An error occurred: {e}")