import pandas as pd
from datetime import datetime
import logging
from typing import Optional
from pgpar import PrecipGenPAR

def get_station_info(station_id: str) -> Optional[pd.Series]:
    from fetch_ghcn import fetch_ghcn_stations
    from parse_ghcn import parse_ghcn_stations

    raw_data = fetch_ghcn_stations()
    if raw_data:
        stations_df = parse_ghcn_stations(raw_data)
        if stations_df is not None:
            station_info = stations_df[stations_df['ID'] == station_id]
            if not station_info.empty:
                return station_info.iloc[0]
    return None

def summarize_dataset(df: pd.DataFrame, station_info: Optional[pd.Series], pgp: PrecipGenPAR) -> None:
    print("\nDataset Summary:")
    if station_info is not None:
        print(f"Station Name: {station_info['NAME']}")
        print(f"Station ID: {station_info['ID']}")
        print(f"Location: {station_info['STATE']}")
        print(f"Coordinates: {station_info['LATITUDE']}, {station_info['LONGITUDE']}")
        print(f"Elevation: {station_info['ELEVATION']} meters")
    else:
        print("Station information not available.")
    
    units = "inches" if df['PRCP'].max() < 100 else "mm"
    print(f"Precipitation units: {units}")
    
    print(f"Date Range: {df['DATE'].min()} to {df['DATE'].max()}")
    print(f"Total Records: {len(df)}")
    
    df['YEAR'] = df['DATE'].apply(lambda x: datetime.strptime(x, '%m/%d/%Y').year)
    annual_precip = df.groupby('YEAR')['PRCP'].sum()
    avg_annual_precip = annual_precip.mean()
    
    print(f"Precipitation Stats:")
    print(f"  Average Annual Precipitation: {avg_annual_precip:.2f} {units}")
    print(f"  Mean Daily Precipitation: {df['PRCP'].mean():.2f} {units}")
    print(f"  Standard Deviation: {df['PRCP'].std():.2f} {units}")
    
    try:
        autocorrelation, optimal_lag = pgp.calculate_autocorrelation_ann_precip()
        print(f"\nAnnual Precipitation Autocorrelation:")
        print(f"  Autocorrelation: {autocorrelation:.4f}")
        print(f"  Optimal Lag: {optimal_lag} year(s)")
    except Exception as e:
        logging.error(f"Error calculating annual autocorrelation: {e}")
        print("\nUnable to calculate annual precipitation autocorrelation.")