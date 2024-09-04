# sandbox.py

import pandas as pd
import matplotlib.pyplot as plt
from data_download import get_ghcn_data

def plot_annual_precipitation(df: pd.DataFrame):
    """
    Plot annual total precipitation from a DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with 'DATE' and 'PRCP' columns.
    """
    annual_precip = df.groupby(df['DATE'].dt.year)['PRCP'].sum()
    
    plt.figure(figsize=(12, 6))
    annual_precip.plot(kind='bar')
    plt.title('Annual Total Precipitation')
    plt.xlabel('Year')
    plt.ylabel('Precipitation (mm)')
    plt.tight_layout()
    plt.show()

def analyze_data(station_id: str):
    """
    Download data for a station and perform some basic analysis.
    
    Args:
        station_id (str): The GHCN station ID.
    """
    try:
        # Download the data
        df = get_ghcn_data(station_id)
        
        # Print basic statistics
        print(f"Data summary for station {station_id}:")
        print(df.describe())
        
        # Plot annual precipitation
        plot_annual_precipitation(df)
        
    except Exception as e:
        print(f"Error analyzing data: {e}")

if __name__ == "__main__":
    # Example usage
    station_id = "USC00026621"  # Caribou, ME
    analyze_data(station_id)