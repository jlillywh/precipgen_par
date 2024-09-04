import requests
import pandas as pd
from io import StringIO
from pgpar import PrecipGenPAR
import logging
from typing import Optional
from datetime import datetime 

def fetch_ghcn_data(station_id: str) -> Optional[str]:
    """
    Fetch GHCN data for a given station ID.
    
    Args:
        station_id (str): The GHCN station ID.
    
    Returns:
        Optional[str]: The raw CSV data as a string, or None if fetch fails.
    """
    base_url = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/"
    url = f"{base_url}{station_id}.csv"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None

def parse_ghcn_data(raw_data: str) -> Optional[pd.DataFrame]:
    """
    Parse the raw GHCN CSV data into a pandas DataFrame.
    
    Args:
        raw_data (str): The raw CSV data as a string.
    
    Returns:
        Optional[pd.DataFrame]: The parsed data as a DataFrame, or None if parsing fails.
    """
    try:
        # Specify dtypes for known columns and use 'object' for others
        dtypes = {
            'DATE': str,
            'PRCP': float,
            'TMAX': float,
            'TMIN': float,
            'TAVG': float,
            'SNOW': float,
            'SNWD': float
        }
        
        # Read only the columns we need
        df = pd.read_csv(
            StringIO(raw_data),
            usecols=['DATE', 'PRCP', 'TMAX', 'TMIN', 'TAVG', 'SNOW', 'SNWD'],
            dtype=dtypes,
            na_values=['', 'NA', '-9999'],
            keep_default_na=False
        )
        
        # Convert DATE to datetime
        df['DATE'] = pd.to_datetime(df['DATE'], format='%Y-%m-%d')
        
        # Drop rows with missing DATE or PRCP
        df = df.dropna(subset=['DATE', 'PRCP'])
        
        # Convert DATE back to string in the desired format
        df['DATE'] = df['DATE'].dt.strftime('%m/%d/%Y')
        
        return df
    except Exception as e:
        logging.error(f"Error parsing data: {e}")
        return None

def fetch_ghcn_stations() -> Optional[str]:
    """
    Fetch GHCN stations metadata.
    
    Returns:
        Optional[str]: The raw stations data as a string, or None if fetch fails.
    """
    url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching stations data: {e}")
        return None

def parse_ghcn_stations(raw_data: str) -> Optional[pd.DataFrame]:
    """
    Parse the raw GHCN stations data into a pandas DataFrame.
    
    Args:
        raw_data (str): The raw stations data as a string.
    
    Returns:
        Optional[pd.DataFrame]: The parsed stations data as a DataFrame, or None if parsing fails.
    """
    colspecs = [(0, 11), (12, 20), (21, 30), (31, 37), (38, 40), (41, 71), (72, 75), (76, 79), (80, 85)]
    names = ['ID', 'LATITUDE', 'LONGITUDE', 'ELEVATION', 'STATE', 'NAME', 'GSN_FLAG', 'HCN_CRN_FLAG', 'WMO_ID']
    
    try:
        df = pd.read_fwf(StringIO(raw_data), colspecs=colspecs, header=None, names=names)
        return df
    except Exception as e:
        logging.error(f"Error parsing stations data: {e}")
        return None

def get_station_info(station_id: str) -> Optional[pd.Series]:
    """
    Get information for a specific station.
    
    Args:
        station_id (str): The GHCN station ID.
    
    Returns:
        Optional[pd.Series]: The station information, or None if not found.
    """
    raw_data = fetch_ghcn_stations()
    if raw_data:
        stations_df = parse_ghcn_stations(raw_data)
        if stations_df is not None:
            station_info = stations_df[stations_df['ID'] == station_id]
            if not station_info.empty:
                return station_info.iloc[0]
    return None

def summarize_dataset(df: pd.DataFrame, station_info: Optional[pd.Series], pgp: PrecipGenPAR) -> None:
    """
    Print a summary of the dataset, including station info, precipitation stats, and autocorrelation.
    
    Args:
        df (pd.DataFrame): The DataFrame containing the dataset.
        station_info (Optional[pd.Series]): The station information.
        pgp (PrecipGenPAR): The PrecipGenPAR object for additional calculations.
    """
    print("\nDataset Summary:")
    if station_info is not None:
        print(f"Station Name: {station_info['NAME']}")
        print(f"Station ID: {station_info['ID']}")
        print(f"Location: {station_info['STATE']}")
        print(f"Coordinates: {station_info['LATITUDE']}, {station_info['LONGITUDE']}")
        print(f"Elevation: {station_info['ELEVATION']} meters")
    else:
        print("Station information not available.")
    
    # Determine precipitation units
    units = "inches" if df['PRCP'].max() < 100 else "mm"
    print(f"Precipitation units: {units}")
    
    print(f"Date Range: {df['DATE'].min()} to {df['DATE'].max()}")
    print(f"Total Records: {len(df)}")
    
    # Calculate average annual precipitation
    df['YEAR'] = df['DATE'].apply(lambda x: datetime.strptime(x, '%m/%d/%Y').year)
    annual_precip = df.groupby('YEAR')['PRCP'].sum()
    avg_annual_precip = annual_precip.mean()
    
    print(f"Precipitation Stats:")
    print(f"  Average Annual Precipitation: {avg_annual_precip:.2f} {units}")
    print(f"  Mean Daily Precipitation: {df['PRCP'].mean():.2f} {units}")
    print(f"  Standard Deviation: {df['PRCP'].std():.2f} {units}")
    
    # Calculate and print autocorrelation
    try:
        autocorrelation, optimal_lag = pgp.calculate_autocorrelation_ann_precip()
        print(f"\nAnnual Precipitation Autocorrelation:")
        print(f"  Autocorrelation: {autocorrelation:.4f}")
        print(f"  Optimal Lag: {optimal_lag} year(s)")
    except Exception as e:
        logging.error(f"Error calculating annual autocorrelation: {e}")
        print("\nUnable to calculate annual precipitation autocorrelation.")

def main() -> None:
    """
    Main function to fetch, parse, and analyze GHCN data.
    """
    station_id = input("Enter the GHCN station ID: ")
    
    print(f"Fetching data for station {station_id}...")
    station_info = get_station_info(station_id)
    raw_data = fetch_ghcn_data(station_id)
    
    if raw_data:
        df = parse_ghcn_data(raw_data)
        
        if df is not None and not df.empty:
            # Create PrecipGenPAR object
            pgp = PrecipGenPAR(df)
            
            # Summarize dataset (now includes autocorrelation)
            summarize_dataset(df, station_info, pgp)
            
            # Determine units (assuming inches if max PRCP < 100, otherwise mm)
            units = "inches" if df['PRCP'].max() < 100 else "mm"
            print(f"\nPrecipitation units: {units}")
            
            # Get parameters
            params = pgp.get_parameters()
            
            # Prepare output
            output_file = f"{station_id}_precipitation_parameters.csv"
            with open(output_file, 'w') as f:
                for condition in ['dry', 'all', 'wet']:
                    f.write(f"{condition.capitalize()} Years Parameters:\n")
                    params[condition].to_csv(f, index=False)
                    f.write("\n")
                    print(f"\n{condition.capitalize()} Years Parameters:")
                    print(params[condition].to_string(index=False))
                    print()
            print(f"\nResults saved to {output_file}")
        else:
            print("No valid data to process.")
    else:
        print("Failed to fetch data. Please check the station ID and try again.")

if __name__ == "__main__":
    main()