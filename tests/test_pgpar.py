import unittest
import os
import sys
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from precip_stats import mean_monthly_totals

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from time_series import TimeSeries
from pgpar import calculate_params

class TestPrecipGenPAR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file_path = os.path.join(os.path.dirname(__file__), "USW00023066_data1.csv")
        if not os.path.exists(cls.file_path):
            raise FileNotFoundError(f"The file {cls.file_path} does not exist.")
        
        # Load and preprocess the CSV file
        cls.precip_ts = TimeSeries()
        cls.precip_ts.load_and_preprocess(cls.file_path)
        cls.trim(1900, 2023)

    def test_mean_monthly_totals(self):
        # Expected result
        expected_data = {
            'Month': list(range(1, 13)),
            'Average Monthly Total': [
                15.2, 14.3, 20.7, 20.3, 19.8, 11.0, 15.7, 25.0, 24.7, 23.5, 15.8, 15.7
            ]
        }
        expected_df = pd.DataFrame(expected_data)

        # Calculate the mean monthly totals
        result_df = mean_monthly_totals(self.precip_ts.get_data())

        # Assert the result is as expected
        pd.testing.assert_frame_equal(result_df, expected_df)

    def test_calculate_params(self):
        # Check that the actual params are close to the expected params within 0.1% relative error
        for col in self.expected_params.columns:
            self.assertTrue(np.allclose(self.obj[col], self.expected_params[col], rtol=0.001),
                            msg=f"Values in column {col} are not within 0.1% relative error.")

if __name__ == '__main__':
    unittest.main()