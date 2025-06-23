# time_series.py
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeSeries:
    def __init__(self):
        self.data = pd.DataFrame(columns=['DATE', 'PRCP'])

    def load_and_preprocess(self, file_path):
        try:
            # Read the CSV file, skipping the first 6 lines of metadata and specifying the header row
            df = pd.read_csv(file_path, skiprows=6, header=0)
            
            # Convert 'DATE' column to datetime
            df['DATE'] = pd.to_datetime(df['DATE'])
            
            # Set 'DATE' as the index
            df.set_index('DATE', inplace=True)
            
            # Ensure 'PRCP' column is numeric
            df['PRCP'] = pd.to_numeric(df['PRCP'], errors='coerce')
            self.data = df   
            logger.info("CSV file loaded and preprocessed successfully.")
            
        except Exception as e:
            logger.error(f"Error loading and preprocessing CSV file: {e}")
            raise

    def get_data(self):
        if self.data.empty:
            return None
        return self.data

    def get_trimmed_df(self, start_year, end_year):
        """
        Trim the DataFrame to include only complete years within the specified range.

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame with 'DATE' as the index.
        start_year : int
            The start year for the trim.
        end_year : int
            The end year for the trim.

        Returns
        -------
        pd.DataFrame
            The trimmed DataFrame containing only complete years within the specified range.
        """
        if self.data is None or self.data.empty:
            logger.error("DataFrame is not loaded. Please call load_and_preprocess() first.")
            raise ValueError("DataFrame is not loaded. Please call load_and_preprocess() first.")

        # Filter the DataFrame to include only the specified date range
        trimmed_df = self.data[(self.data.index.year >= start_year) & (self.data.index.year <= end_year)]

        # Ensure only complete years are included
        complete_years = trimmed_df.index.year.unique()
        complete_years = complete_years[(complete_years >= start_year) & (complete_years <= end_year)]

        # Filter out partial years
        trimmed_df = trimmed_df[trimmed_df.index.year.isin(complete_years)]
        logger.info(f"DataFrame trimmed to complete years {start_year}-{end_year}.")

        return trimmed_df
    
    def trim(self, start_year, end_year):
        """
        Trim the DataFrame to include only complete years within the specified range and update the object's data.

        Parameters
        ----------
        start_year : int
            The start year for the trim.
        end_year : int
            The end year for the trim.
        """
        if self.data is None or self.data.empty:
            logger.error("DataFrame is not loaded. Please call load_and_preprocess() first.")
            raise ValueError("DataFrame is not loaded. Please call load_and_preprocess() first.")

        # Filter the DataFrame to include only the specified date range
        self.data = self.data[(self.data.index.year >= start_year) & (self.data.index.year <= end_year)]

        # Ensure only complete years are included
        complete_years = self.data.index.year.unique()
        complete_years = complete_years[(complete_years >= start_year) & (complete_years <= end_year)]

        # Filter out partial years
        self.data = self.data[self.data.index.year.isin(complete_years)]
        logger.info(f"DataFrame trimmed to complete years {start_year}-{end_year} in place.")
