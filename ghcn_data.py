import pandas as pd
import numpy as np
import requests
import logging
import os
import logging

# Configure logging to write to a file
logging.basicConfig(filename='ghcn_stations.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GHCNData:
    def __init__(self):
        self.station_name = "no-name"
        self.station_id = None
        self.latitude = None
        self.longitude = None
        self.metadata_url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
        self.data_url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/"
        self.data = None
        self.start_date = None
        self.end_date = None
        self.coverage = None
        self.output_path = self.update_output_path()

    def update_output_path(self, folder: str = "C:\\Users\\jason\\Downloads"):
        if self.station_id:
            self.output_path = os.path.join(folder, f"{self.station_id}_data.csv")

    def load_from_csv(self, path: str):
        """Load data from a CSV file into the GHCNData object."""
        with open(path, 'r') as f:
            lines = f.readlines()
            
            # Extract metadata from the CSV file
            self.station_name = lines[1].split(',')[1].strip()
            self.station_id = lines[2].split(',')[1].strip()
            self.latitude = float(lines[3].split(',')[1].strip().split()[0])
            self.longitude = float(lines[3].split(',')[3].strip().split()[0])
            self.start_date = lines[4].split(',')[1].strip()
            self.end_date = lines[4].split(',')[3].strip()
            self.coverage = float(lines[5].split(',')[1].strip().split('%')[0])
            
            # Read the data into a pandas DataFrame, skipping the metadata lines
            self.data = pd.read_csv(path, skiprows=7)
            
        print(f"Data loaded from {path}")

    def fetch(self, station_id: str):
        """Fetch the data for the location and save it within the object as a pandas dataframe."""
        url = f"{self.data_url}{station_id}.dly"
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.data = self._parse_dly_data(response.text)
            self.station_id = station_id
            self.update_output_path()
            self._fetch_station_metadata(station_id)
            self._handle_outliers()
            
            # Calculate data coverage, start year, and end year
            self.coverage = self.get_coverage()
            self.start_date = self.data['DATE'].min().year
            self.end_date = self.data['DATE'].max().year
            #print(f"Successfully fetched data for station {station_id}")

        except requests.RequestException as e:
            logging.error(f"Error fetching data: {e}")
            print(f"Failed to fetch data for station {station_id}. Error: {e}")
            self.data = None

    def _parse_dly_data(self, dly_text: str) -> pd.DataFrame:
        """Parse the .dly file content into a pandas DataFrame with specific columns."""
        data = []
        for line in dly_text.splitlines():
            year = int(line[11:15])
            month = int(line[15:17])
            element = line[17:21]
            if element not in ['PRCP', 'TMAX', 'TMIN']:
                continue  # Skip elements we're not interested in
            for day in range(31):
                value = int(line[21 + day * 8:26 + day * 8])
                if value != -9999:  # -9999 is often used to indicate missing data
                    data.append([year, month, day + 1, element, value])
        
        df = pd.DataFrame(data, columns=["YEAR", "MONTH", "DAY", "ELEMENT", "VALUE"])
        df["DATE"] = pd.to_datetime(df[["YEAR", "MONTH", "DAY"]])
        df = df.pivot(index="DATE", columns="ELEMENT", values="VALUE").reset_index()
        df = df[['DATE', 'PRCP', 'TMAX', 'TMIN']]  # Select only the columns we want
        return df

    def _handle_outliers(self):
        """Detect and handle outliers in the data."""
        if self.data is None:
            return

        # Convert temperatures from tenths of degrees Celsius to Celsius
        self.data['TMAX'] = self.data['TMAX'] / 10
        self.data['TMIN'] = self.data['TMIN'] / 10

        # Convert precipitation from tenths of mm to mm
        self.data['PRCP'] = self.data['PRCP'] / 10

        # Define reasonable limits for each variable
        limits = {
            'PRCP': (0, 1000),  # 0 to 1000 mm per day
            'TMAX': (-50, 60),  # -50°C to 60°C
            'TMIN': (-60, 50)   # -60°C to 50°C
        }

        for column, (low, high) in limits.items():
            # Identify outliers
            outliers = self.data[(self.data[column] < low) | (self.data[column] > high)]
            if not outliers.empty:
                logging.info(f"Found {len(outliers)} outliers in {column}:")
                logging.debug(outliers)
                
                # Remove outliers
                self.data = self.data[(self.data[column] >= low) & (self.data[column] <= high)]
                logging.info(f"Removed outliers from {column}")

    def _fetch_station_metadata(self, station_id: str):
        """Fetch station metadata from ghcnd-stations.txt."""
        try:
            response = requests.get(self.metadata_url)
            response.raise_for_status()
            stations_text = response.text
            for line in stations_text.splitlines():
                if line.startswith(station_id):
                    self.station_name = line[41:71].strip()
                    self.latitude = float(line[12:20].strip())
                    self.longitude = float(line[21:30].strip())
                    #print(f"Station metadata: Name: {self.station_name}, Lat: {self.latitude}, Lon: {self.longitude}")
                    return
            print(f"No metadata found for station {station_id}")
        except requests.RequestException as e:
            logging.error(f"Error fetching station metadata: {e}")
            print(f"Failed to fetch station metadata. Error: {e}")

    def summarize(self):
        """Print the average annual total rainfall, tmax, tmin."""
        if self.data is None:
            print("No data available. Please fetch data first.")
            return
        
        # Print station name and ID
        print(f"Station Name: {self.station_name}")
        print(f"Station ID: {self.station_id}")
        print(f"Latitude: {self.latitude:.4f}°, Longitude: {self.longitude:.4f}°")
        print(f"Start Date: {self.start_date}, End Date: {self.end_date}")
        print(f"Data Coverage: {self.coverage:.2f}%")

        yearly_data = self.data.set_index('DATE').resample('YE').agg({
            'PRCP': 'sum',
            'TMAX': 'mean',
            'TMIN': 'mean'
        })
        summary = yearly_data.mean()
        print(f"Average Annual Total Rainfall: {summary['PRCP']:.2f} mm")
        print(f"Average Annual Tmax: {summary['TMAX']:.2f}°C")
        print(f"Average Annual Tmin: {summary['TMIN']:.2f}°C")

    def print_first_rows(self, rows=4):
        """Print the first few lines to the screen."""
        if self.data is None:
            print("No data available. Please fetch data first.")
        else:
            print(self.data.head(rows))

    def get_dataframe(self) -> pd.DataFrame:
        """Return a pandas dataframe of the time series."""
        return self.data

    def save_to_csv(self):
        """Save the GHCNData object to a CSV file."""
        if self.data is None:
            print("No data available. Please fetch data first.")
            return
        
        if self.station_id is None:
            print("No station ID available. Please fetch data for a station first.")
            return
        
        metadata = self._prepare_metadata()
        with open(self.output_path, 'w', newline='') as f:
            # Write metadata
            for row in metadata:
                f.write(','.join(map(str, row)) + '\n')
            
            # Write an empty line to separate metadata from data
            f.write('\n')
            
            # Write data
            self.data.to_csv(f, index=False)

        print(f"Data saved to {self.output_path}")

    def _prepare_metadata(self):
        """Prepare metadata for the GHCNData object."""
        self.start_date = self.data['DATE'].min().strftime('%Y-%m-%d')
        self.end_date = self.data['DATE'].max().strftime('%Y-%m-%d')

        self.metadata = [
            ["GHCN daily data, "],
            ["Station Name", self.station_name],
            ["Station ID", self.station_id],
            ["Latitude", f"{self.latitude:.4f} deg", "Longitude", f"{self.longitude:.4f} deg"],
            ["Start Date", self.start_date, "End Date", self.end_date],
            ["Data Coverage", f"{self.coverage:.2f}%"]
        ]
        return self.metadata

    def get_name(self) -> str:
        """Return the station name."""
        return self.station_name
    
    def get_coverage(self) -> float:
        """Return the data coverage percentage based on the most complete data element."""
        if self.data is None:
            return 0
        
        # Calculate the total number of days in the data range
        total_days = (self.data['DATE'].max() - self.data['DATE'].min()).days + 1
        
        # Calculate the completeness for each data element
        elements = ['PRCP', 'TMAX', 'TMIN']
        completeness = {element: self.data[element].notna().sum() / total_days for element in elements}
        
        # Find the maximum completeness among the elements
        max_completeness = max(completeness.values())
        
        # Calculate the overall data coverage percentage
        data_coverage = max_completeness * 100
        return data_coverage