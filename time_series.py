# time_series.py
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeSeries:
    def __init__(self):
        self.metadata = {}
        self.data = pd.DataFrame()

    import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeSeries:
    def __init__(self):
        self.metadata = {}
        self.data = pd.DataFrame()

    def load_and_preprocess(self, file_path : str) -> None:
        """
        Load and preprocess a CSV file containing metadata and time series data.

        The file is expected to have two sections:
        1. Metadata: Lines starting with '#' containing key-value pairs separated by commas.
        Required metadata fields:
        - "Type": Specifies the type of data (e.g., "PRCP" for precipitation).
        - "Unit": Specifies the unit of the data (e.g., "mm" for millimeters).
        2. Data: A tabular section with columns 'DATE' and 'VALUE' containing the time series data.

        The function:
        - Parses metadata and stores it in the `self.metadata` dictionary.
        - Reads and validates the data section into a pandas DataFrame (`self.data`).
        - Converts 'DATE' to datetime format and ensures 'VALUE' is numeric.

        Parameters:
        ----------
        file_path : str
            Path to the CSV file to be loaded.

        Raises:
        -------
        ValueError:
            If required metadata fields ("Type", "Unit") are missing.
            If the data section is missing required columns ('DATE', 'VALUE').
            If 'DATE' column values cannot be parsed as valid dates.

        Side Effects:
        -------------
        - Updates the `self.metadata` dictionary with parsed metadata fields.
        - Updates the `self.data` attribute with the preprocessed pandas DataFrame.

        Example:
        --------
        A sample CSV file might look like this:

        ```
        # Type,PRCP
        # Unit,mm
        DATE,VALUE
        2023-01-01,0.5
        2023-01-02,1.2
        2023-01-03,0.0
        ```

        After processing:
        - `self.metadata` contains:
            {'Type': 'PRCP', 'Unit': 'mm'}
        - `self.data` contains a DataFrame with the 'DATE' column as the index and 'VALUE' as the data column.
        """
        try:
            # Step 1: Read all lines from the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Step 2: Separate metadata and data sections
            metadata_lines = []
            data_lines = []
            data_section_found = False

            for line in lines:
                stripped_line = line.strip()

                # Collect metadata (lines starting with '#')
                if stripped_line.startswith('#'):
                    metadata_lines.append(stripped_line)

                # Detect the start of the data section ("DATE, VALUE")
                elif not data_section_found and "DATE" in stripped_line and "VALUE" in stripped_line:
                    data_section_found = True  # Mark the start of the data section
                    data_lines.append(stripped_line)  # Include the header line

                # Collect data lines after the header
                elif data_section_found:
                    data_lines.append(stripped_line)

            # Raise an error if "DATE, VALUE" header is not found
            if not data_section_found:
                raise ValueError("Could not locate the 'DATE, VALUE' header in the file.")

            # Step 3: Parse metadata
            for line in metadata_lines:
                line = line.lstrip('#').strip()  # Remove '#' and strip spaces
                if ',' in line:
                    key, value = line.split(',', 1)
                    self.metadata[key.strip()] = value.strip()

            # Ensure required metadata fields exist
            required_fields = ["Type", "Unit"]
            for field in required_fields:
                if field not in self.metadata:
                    raise ValueError(f"Missing required metadata field: '{field}'")

            logger.info("Metadata successfully parsed and saved.")

            # Step 4: Read the data section into a DataFrame
            df = pd.read_csv(pd.io.common.StringIO('\n'.join(data_lines)))

            # Step 5: Validate that the required columns exist
            if "DATE" not in df.columns or "VALUE" not in df.columns:
                raise ValueError("Expected columns 'DATE' and 'VALUE' not found in the data section!")

            # Step 6: Convert 'DATE' column to datetime
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
            if df['DATE'].isnull().any():
                logger.warning("Some 'DATE' values could not be parsed as datetime.")
            df.set_index('DATE', inplace=True)

            # Step 7: Ensure 'VALUE' column is numeric
            df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')

            # Save the DataFrame
            self.data = df
            logger.info("CSV file loaded and preprocessed successfully.")

        except Exception as e:
            logger.error(f"Error loading and preprocessing CSV file: {e}")
            exit()

    def get_metadata(self) -> dict:
        """
        Retrieve the metadata associated with the time series.

        Returns:
        -------
        dict
            A dictionary containing metadata fields and their corresponding values.
            Example:
            {
                "Station ID": "USW000",
                "Type": "PRCP",
                "Unit": "mm",
                ...
            }
        Notes:
        -----
        - Metadata is extracted from the lines starting with '#' in the input file.
        - Common metadata fields include "Type" (e.g., PRCP) and "Unit" (e.g., mm).
        """
        return self.metadata

    def get_data(self) -> pd.DataFrame:
        """
        Retrieve the preprocessed time series data.

        Returns:
        -------
        pd.DataFrame
            A pandas DataFrame containing the time series data.
            The DataFrame has the following structure:
            - Index: 'DATE' (datetime format).
            - Columns: ['VALUE'], representing the time series values.

        Notes:
        -----
        - The 'DATE' column is converted to datetime and used as the DataFrame index.
        - The 'VALUE' column contains numeric data, which is coerced during preprocessing.
        - Ensure that the data has been loaded and preprocessed before calling this method.
        """
        return self.data

    def get_trimmed_df(self, start_year : int, end_year : int) -> pd.DataFrame:
        """
        Trim the time series data to include only complete years within the specified range.

        This function removes any partial years (e.g., years with incomplete data at the beginning
        or end of the time series) and filters the data to the specified range of years.

        Parameters:
        ----------
        start_year : int
            The first year (inclusive) to include in the trimmed data.
        end_year : int
            The last year (inclusive) to include in the trimmed data.

        Returns:
        -------
        pd.DataFrame
            A pandas DataFrame containing only complete years within the specified range.
            - Index: 'DATE' (datetime format).
            - Columns: ['VALUE'].

        Raises:
        -------
        ValueError:
            If the time series data has not been loaded or is unavailable.

        Notes:
        -----
        - A "complete year" is defined as a year with data for all 12 months (Jan-Dec).
        - The function assumes the data has already been loaded using `load_and_preprocess()`.
        """
        # Check if data is loaded
        if self.data is None:
            logger.error("DataFrame is not loaded. Please call load_and_preprocess() first.")
            raise ValueError("DataFrame is not loaded. Please call load_and_preprocess() first.")

        # Step 1: Filter the DataFrame to the specified date range
        filtered_df = self.data[(self.data.index.year >= start_year) & (self.data.index.year <= end_year)]

        # Step 2: Identify years with complete data
        complete_years = filtered_df.index.year.value_counts()
        complete_years = complete_years[complete_years == 365].index  # Only years with 365 days (or 366 for leap years)

        # Step 3: Retain only complete years in the filtered data
        trimmed_df = filtered_df[filtered_df.index.year.isin(complete_years)]

        logger.info(f"DataFrame trimmed to complete years {start_year}-{end_year}.")

        return trimmed_df
    
    def trim(self, start_year : int, end_year : int) -> None:
        """
        Trim the time series data to include only complete years within the specified range 
        and update the object's data in place.

        This function removes any partial years (e.g., years with incomplete data at the beginning
        or end of the time series) and modifies the `self.data` attribute.

        Parameters:
        ----------
        start_year : int
            The first year (inclusive) to include in the trimmed data.
        end_year : int
            The last year (inclusive) to include in the trimmed data.

        Raises:
        -------
        ValueError:
            If the time series data has not been loaded or is unavailable.

        Notes:
        -----
        - A "complete year" is defined as a year with data for all 12 months (365 or 366 days).
        - This function modifies `self.data` in place. If you need a separate DataFrame, use `get_trimmed_df`.
        """
        # Check if data is loaded
        if self.data is None:
            logger.error("DataFrame is not loaded. Please call load_and_preprocess() first.")
            raise ValueError("DataFrame is not loaded. Please call load_and_preprocess() first.")

        # Step 1: Filter data to the specified date range
        start_date = f"{start_year}-01-01"
        end_date = f"{end_year}-12-31"
        filtered_data = self.data[(self.data.index >= start_date) & (self.data.index <= end_date)]

        # Step 2: Resample data to ensure each year has data for all 12 months
        resampled_data = filtered_data.resample('Y').sum(min_count=12)
        complete_years = resampled_data.dropna().index.year

        # Step 3: Retain only complete years in the data
        self.data = filtered_data[filtered_data.index.year.isin(complete_years)]
        logger.info(f"TimeSeries.data trimmed to complete years {start_year}-{end_year} in place.")

    def monthly_means(self) -> pd.DataFrame:
        """
        Calculate the monthly means of the time series data over all years on record.

        This function computes the mean 'VALUE' for each month (January through December)
        across all years in the dataset.

        Returns:
        -------
        pd.DataFrame
            A DataFrame where the index is the month number (1 for January, 2 for February, etc.)
            and the column is the mean 'VALUE' for that month.
            Example:
                | Month | Mean  |
                |-------|-------|
                | 1     | 12.3  |
                | 2     | 8.4   |
                | ...   | ...   |
                | 12    | 9.1   |

        Raises:
        -------
        ValueError:
            If the time series data has not been loaded or is unavailable.

        Notes:
        -----
        - Ensure the data has been preprocessed and loaded into `self.data` before calling this function.
        - Months with no data will return `NaN` as their mean.
        """
        # Check if data is loaded
        if self.data is None:
            logger.error("DataFrame is not loaded. Please call load_and_preprocess() first.")
            raise ValueError("DataFrame is not loaded. Please call load_and_preprocess() first.")

        # Calculate the monthly mean
        monthly_means = self.data.groupby(self.data.index.month)['VALUE'].mean()

        # Convert the result to a DataFrame
        monthly_mean_df = monthly_means.reset_index()
        monthly_mean_df.columns = ['Month', 'Mean']

        logger.info("Monthly means calculated successfully.")
        return monthly_mean_df
    
    def total(self) -> float:
        if self.data is None:
            logger.error("DataFrame is not loaded. Please call load_and_preprocess() first.")
            raise ValueError("DataFrame is not loaded. Please call load_and_preprocess() first.")

        total_sum = self.data['VALUE'].sum()
        logger.info("Sum of all values calculated successfully.")
        return total_sum