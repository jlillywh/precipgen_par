"""
Integration test for end-to-end workflow: station search → download → analysis.

This test validates the complete practitioner workflow from finding suitable stations
through data download and analysis, testing the data acquisition modules that are not
covered by unit tests.
"""

import unittest
import time
import pandas as pd
from precipgen.data.find_stations import fetch_ghcn_inventory, parse_ghcn_inventory
from precipgen.data.ghcn_data import GHCNData
from precipgen.core.time_series import TimeSeries


class TestEndToEndWorkflow(unittest.TestCase):
    """Test the complete workflow from station search to data analysis"""
    
    def test_end_to_end_workflow(self):
        """
        Test complete practitioner workflow: search → download → analyze
        
        This test:
        1. Fetches GHCN station inventory from NOAA
        2. Finds stations with >75 years of precipitation data
        3. Downloads data for a suitable station
        4. Performs analysis and validates results
        
        Validates Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
        """
        max_retries = 3
        timeout = 60
        
        # Step 1: Fetch station inventory with retry logic
        print("\n=== Step 1: Fetching GHCN station inventory ===")
        inventory_data = None
        for attempt in range(max_retries):
            try:
                inventory_data = self._fetch_with_timeout(fetch_ghcn_inventory, timeout)
                if inventory_data:
                    print(f"Successfully fetched inventory data (attempt {attempt + 1})")
                    break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        self.assertIsNotNone(inventory_data, "Failed to fetch GHCN inventory after retries")
        
        # Step 2: Parse inventory data
        print("\n=== Step 2: Parsing inventory data ===")
        inventory_df = parse_ghcn_inventory(inventory_data)
        self.assertIsNotNone(inventory_df, "Failed to parse inventory data")
        self.assertGreater(len(inventory_df), 0, "Inventory is empty")
        print(f"Parsed {len(inventory_df)} inventory records")
        
        # Step 3: Find suitable station with >75 years of PRCP data
        print("\n=== Step 3: Finding station with >75 years of data ===")
        suitable_station = self._find_suitable_station(inventory_df)
        self.assertIsNotNone(suitable_station, "No station with >75 years of data found")
        print(f"Found suitable station: {suitable_station}")
        
        # Step 4: Download data from GHCN NOAA database with retry logic
        print("\n=== Step 4: Downloading station data ===")
        ghcn_data = None
        for attempt in range(max_retries):
            try:
                ghcn_data = GHCNData()
                ghcn_data.fetch(suitable_station)
                if ghcn_data.data is not None and not ghcn_data.data.empty:
                    print(f"Successfully downloaded data (attempt {attempt + 1})")
                    break
            except Exception as e:
                print(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        self.assertIsNotNone(ghcn_data, "Failed to create GHCNData object")
        self.assertIsNotNone(ghcn_data.data, "Failed to download station data")
        self.assertFalse(ghcn_data.data.empty, "Downloaded data is empty")
        print(f"Downloaded {len(ghcn_data.data)} records")
        
        # Step 5: Perform analysis on downloaded data
        print("\n=== Step 5: Analyzing precipitation data ===")
        
        # Verify data has required columns
        self.assertIn('PRCP', ghcn_data.data.columns, "PRCP column missing from data")
        
        # Calculate basic statistics
        prcp_data = ghcn_data.data['PRCP']
        
        # Calculate wet day probability (days with PRCP > 0)
        total_days = len(prcp_data)
        wet_days = (prcp_data > 0).sum()
        wet_day_prob = wet_days / total_days if total_days > 0 else 0
        
        print(f"Total days: {total_days}")
        print(f"Wet days: {wet_days}")
        print(f"Wet day probability: {wet_day_prob:.4f}")
        
        # Validate wet day probability is between 0 and 1
        self.assertGreaterEqual(wet_day_prob, 0, "Wet day probability is negative")
        self.assertLessEqual(wet_day_prob, 1, "Wet day probability exceeds 1")
        
        # Additional validation: check data quality
        self.assertGreater(total_days, 365 * 75, "Dataset has less than 75 years of data")
        
        # Verify mean precipitation is reasonable (non-negative)
        mean_prcp = prcp_data.mean()
        self.assertGreaterEqual(mean_prcp, 0, "Mean precipitation is negative")
        print(f"Mean precipitation: {mean_prcp:.2f} mm/day")
        
        print("\n=== Integration test completed successfully ===")
    
    def _fetch_with_timeout(self, func, timeout):
        """Execute a function with timeout handling"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Operation timed out")
        
        # Note: signal.alarm only works on Unix systems
        # For Windows compatibility, we'll just call the function directly
        try:
            return func()
        except Exception as e:
            raise e
    
    def _find_suitable_station(self, inventory_df):
        """
        Find a station with >75 years of PRCP data
        
        Args:
            inventory_df: DataFrame with columns ['ID', 'LATITUDE', 'LONGITUDE', 
                         'ELEMENT', 'FIRSTYEAR', 'LASTYEAR']
        
        Returns:
            Station ID string or None if no suitable station found
        """
        # Filter for PRCP element only
        prcp_stations = inventory_df[inventory_df['ELEMENT'] == 'PRCP'].copy()
        
        # Calculate years of data
        prcp_stations['YEARS'] = prcp_stations['LASTYEAR'] - prcp_stations['FIRSTYEAR']
        
        # Filter for stations with >75 years
        long_term_stations = prcp_stations[prcp_stations['YEARS'] > 75]
        
        if len(long_term_stations) == 0:
            return None
        
        # Sort by years of data (descending) and take the first one
        long_term_stations = long_term_stations.sort_values('YEARS', ascending=False)
        
        # Return the station ID with most years of data
        return long_term_stations.iloc[0]['ID']


if __name__ == '__main__':
    unittest.main()
