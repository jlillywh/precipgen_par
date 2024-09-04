# data_download.py

import logging
import requests
import pandas as pd
from io import StringIO

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_ghcn_data(station_id: str) -> pd.DataFrame:
    """
    Download and process GHCN data for a given station ID.
    
    Args:
        station_id (str): The GHCN station ID.
    
    Returns:
        pd.DataFrame: Processed daily precipitation data.
    """
    logger.info(f"Downloading data for station {station_id}")
    
    # URL for the data file
    url = f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/{station_id}.dly"
    
    try:
        # Download the data
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses
        
        # Read the data into a DataFrame
        data = StringIO(response.text)
        df = pd.read_fwf(data, widths=[11, 4, 2, 4] + [5, 1, 1, 1]*31,
                         names=['ID', 'YEAR', 'MONTH', 'ELEMENT'] +
                               [f'VALUE{i}' for i in range(1, 32)] +
                               [f'MFLAG{i}' for i in range(1, 32)] +
                               [f'QFLAG{i}' for i in range(1, 32)] +
                               [f'SFLAG{i}' for i in range(1, 32)])
        
        logger.info("Data downloaded successfully, processing...")
        
        # Filter for precipitation data
        df = df[df['ELEMENT'] == 'PRCP']
        
        # Process the data
        data_list = []
        for _, row in df.iterrows():
            year = int(row['YEAR'])
            month = int(row['MONTH'])
            days_in_month = pd.Timestamp(year, month, 1).days_in_month
            
            for day in range(1, days_in_month + 1):
                value = row[f'VALUE{day}']
                try:
                    value = int(value)
                    if value != -9999:  # -9999 indicates missing data
                        date = pd.Timestamp(year, month, day)
                        prcp = value / 10  # Convert to mm
                        data_list.append({'DATE': date, 'PRCP': prcp})
                except ValueError:
                    continue
        
        # Create a new DataFrame from the processed data
        result_df = pd.DataFrame(data_list)
        
        # Sort by date and reset index
        result_df = result_df.sort_values('DATE').reset_index(drop=True)
        
        logger.info(f"Processed {len(result_df)} records")
        return result_df
    
    except requests.RequestException as e:
        logger.error(f"Failed to download data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise

if __name__ == "__main__":
    # Example usage
    station_id = "USC00026621"  # Caribou, ME
    try:
        df = get_ghcn_data(station_id)
        print(df.head())
        print(f"Total records: {len(df)}")
    except Exception as e:
        print(f"Error: {e}")