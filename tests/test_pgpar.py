import unittest
import os
import sys
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from time_series import TimeSeries
from pgpar import calculate_params

class TestPrecipGenPAR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file_path = os.path.join(os.path.dirname(__file__), "USW00023066_data.csv")
        if not os.path.exists(cls.file_path):
            raise FileNotFoundError(f"The file {cls.file_path} does not exist.")
        
        # Load and preprocess the CSV file
        timeseries = TimeSeries()
        timeseries.load_and_preprocess(cls.file_path)
        timeseries.trim(1900, 2023)

        # Initialize PrecipGenPAR with the DataFrame (params are calculated upon initialization)
        cls.obj = calculate_params(timeseries.get_data())
        
        # Expected results
        cls.expected_params = pd.DataFrame({
            'PWW': [0.434574, 0.414975, 0.419248, 0.423077, 0.458115, 0.374745, 0.379913, 0.393629, 0.445609, 0.452967, 0.386399, 0.392053],
            'PWD': [0.154817, 0.172198, 0.177051, 0.166898, 0.132186, 0.095135, 0.136248, 0.181235, 0.140345, 0.121145, 0.127119, 0.152899],
            'ALPHA': [0.998000, 0.998000, 0.982768, 0.914160, 0.891204, 0.867014, 0.839977, 0.831021, 0.830143, 0.861214, 0.965841, 0.983633],
            'BETA': [2.279680, 2.242268, 2.908405, 3.305968, 3.645938, 3.199876, 3.360819, 4.223135, 4.881152, 4.868470, 3.170488, 2.571250]
        })
        
    def test_calculate_params(self):
        # Check that the actual params are close to the expected params within 0.1% relative error
        for col in self.expected_params.columns:
            self.assertTrue(np.allclose(self.obj[col], self.expected_params[col], rtol=0.001),
                            msg=f"Values in column {col} are not within 0.1% relative error.")

if __name__ == '__main__':
    unittest.main()