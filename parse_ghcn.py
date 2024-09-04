import pandas as pd
from io import StringIO
import logging
from typing import Optional

def parse_ghcn_data(raw_data: str) -> Optional[pd.DataFrame]:
    try:
        dtypes = {
            'DATE': str,
            'PRCP': float,
            'TMAX': float,
            'TMIN': float,
            'TAVG': float,
            'SNOW': float,
            'SNWD': float
        }
        df = pd.read_csv(
            StringIO(raw_data),
            usecols=['DATE', 'PRCP', 'TMAX', 'TMIN', 'TAVG', 'SNOW', 'SNWD'],
            dtype=dtypes,
            na_values=['', 'NA', '-9999'],
            keep_default_na=False
        )
        df['DATE'] = pd.to_datetime(df['DATE'], format='%Y-%m-%d')
        df = df.dropna(subset=['DATE', 'PRCP'])
        df['DATE'] = df['DATE'].dt.strftime('%m/%d/%Y')
        return df
    except Exception as e:
        logging.error(f"Error parsing data: {e}")
        return None

def parse_ghcn_stations(raw_data: str) -> Optional[pd.DataFrame]:
    colspecs = [(0, 11), (12, 20), (21, 30), (31, 37), (38, 40), (41, 71), (72, 75), (76, 79), (80, 85)]
    names = ['ID', 'LATITUDE', 'LONGITUDE', 'ELEVATION', 'STATE', 'NAME', 'GSN_FLAG', 'HCN_CRN_FLAG', 'WMO_ID']
    try:
        df = pd.read_fwf(StringIO(raw_data), colspecs=colspecs, header=None, names=names)
        return df
    except Exception as e:
        logging.error(f"Error parsing stations data: {e}")
        return None