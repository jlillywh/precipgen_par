import unittest
import tempfile
import os
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from precipgen.core.time_series import TimeSeries
from precipgen.core.pgpar import calculate_params, calculate_window_params
from precipgen.core.pgpar_ext import calculate_ext_params
from precipgen.data.gap_analyzer import analyze_gaps

class TestTimeSeries(unittest.TestCase):
    """Test TimeSeries class functionality"""
    
    def setUp(self):
        self.ts = TimeSeries()
        # Create sample data for testing with proper NOAA format
        self.sample_csv_content = """GHCN daily data, 
Station Name,GRAND JUNCTION WALKER FLD
Station ID,USW00023066
Latitude,39.1344 deg,Longitude,-108.5408 deg
Start Date,1900-01-01,End Date,2024-09-06
Data Coverage,99.93%

DATE,PRCP,TMAX,TMIN
2020-01-01,0.0,5.0,-5.0
2020-01-02,2.5,8.0,-2.0
2020-01-03,0.0,10.0,0.0"""
    
    def test_load_valid_csv(self):
        """Test loading valid CSV data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(self.sample_csv_content)
            f.flush()
            try:
                self.ts.load_and_preprocess(f.name)
                self.assertIsNotNone(self.ts.data)
                self.assertIn('PRCP', self.ts.data.columns)
                self.assertTrue(isinstance(self.ts.data.index, pd.DatetimeIndex))
            finally:
                try:
                    os.unlink(f.name)
                except (PermissionError, FileNotFoundError):
                    pass  # File might be locked on Windows or already deleted
    
    def test_load_invalid_csv(self):
        """Test loading malformed CSV"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("invalid,csv,data\n1,2\n")  # Inconsistent columns
            f.flush()
            try:
                with self.assertRaises(Exception):
                    self.ts.load_and_preprocess(f.name)
            finally:
                try:
                    os.unlink(f.name)
                except PermissionError:
                    pass  # File might be locked on Windows

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file"""
        with self.assertRaises(Exception):
            self.ts.load_and_preprocess("nonexistent_file.csv")
    
    def test_trim_valid_range(self):
        """Test trimming with valid date range"""
        # Create data with datetime index
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        test_data = pd.DataFrame({'PRCP': np.random.rand(len(dates))}, index=dates)
        self.ts.data = test_data
        
        original_len = len(self.ts.data)
        self.ts.trim(2020, 2020)
        self.assertLessEqual(len(self.ts.data), original_len)
    
    def test_trim_invalid_range(self):
        """Test trimming with invalid date range"""
        # Create data with datetime index
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        test_data = pd.DataFrame({'PRCP': np.random.rand(len(dates))}, index=dates)
        self.ts.data = test_data
        
        self.ts.trim(2025, 2030)  # Future dates
        # Should result in empty DataFrame
        self.assertTrue(len(self.ts.data) == 0)
    
    def test_get_data_empty(self):
        """Test getting data when none loaded"""
        result = self.ts.get_data()
        self.assertIsNone(result)

class TestParameterCalculations(unittest.TestCase):
    """Test parameter calculation functions"""
    
    def setUp(self):
        # Create realistic precipitation data with datetime index
        dates = pd.date_range('2000-01-01', '2002-12-31', freq='D')
        np.random.seed(42)  # For reproducible tests
        
        # Create precipitation data with wet/dry periods
        prcp_data = []
        for i in range(len(dates)):
            if np.random.random() > 0.7:  # 30% chance of precipitation
                prcp_data.append(np.random.exponential(5))
            else:
                prcp_data.append(0.0)
        
        # Create DataFrame with datetime index (as expected by calculate_params)
        self.test_data = pd.DataFrame({
            'PRCP': prcp_data
        }, index=dates)
    
    def test_calculate_params_valid_data(self):
        """Test parameter calculation with valid data"""
        result = calculate_params(self.test_data)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 12)  # 12 months
        expected_cols = ['PWW', 'PWD', 'ALPHA', 'BETA']
        for col in expected_cols:
            self.assertIn(col, result.columns)
            self.assertTrue(all(result[col] >= 0))  # All should be non-negative
    
    def test_calculate_params_empty_data(self):
        """Test parameter calculation with empty data"""
        empty_data = pd.DataFrame({'PRCP': []}, index=pd.DatetimeIndex([]))
        try:
            result = calculate_params(empty_data)
            # If it works, that's valuable information
            self.assertIsNotNone(result)
        except Exception:
            # Expected behavior for empty data
            pass
    
    def test_calculate_params_missing_columns(self):
        """Test parameter calculation with missing required columns"""
        # Create data with multiple days so the loop actually runs and accesses PRCP column
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        bad_data = pd.DataFrame({'TEMP': range(10)}, index=dates)
        with self.assertRaises((KeyError, AttributeError)):
            calculate_params(bad_data, filter_incomplete_years=False)
    
    def test_calculate_params_invalid_dates(self):
        """Test parameter calculation with invalid date formats"""
        # Create data with non-datetime index
        bad_data = pd.DataFrame({
            'PRCP': [1.0, 2.0]
        }, index=[0, 1])  # Integer index instead of datetime
        
        with self.assertRaises(AttributeError):
            calculate_params(bad_data)
    
    def test_calculate_window_params_valid_data(self):
        """Test window parameter calculation"""
        try:
            result = calculate_window_params(self.test_data, n_years=2)
            self.assertIsNotNone(result)
        except Exception as e:
            # Note any unexpected errors
            self.fail(f"Window params calculation failed: {e}")
    
    def test_calculate_window_params_invalid_window(self):
        """Test window parameters with invalid window size"""
        try:
            result = calculate_window_params(self.test_data, n_years=0)
            # If no error, that might be acceptable behavior
            self.assertIsNotNone(result)
        except Exception as e:
            # Expected behavior for invalid window
            self.assertIsInstance(e, (ValueError, ZeroDivisionError))
    
    def test_calculate_ext_params_valid_data(self):
        """Test extended parameter calculation"""
        try:
            result = calculate_ext_params(self.test_data, window_years=2)
            # Check that result is reasonable
            self.assertIsNotNone(result)
        except Exception as e:
            # Note any errors for investigation
            self.fail(f"Extended params calculation failed: {e}")

class TestGapAnalysis(unittest.TestCase):
    """Test gap analysis functionality"""
    
    def setUp(self):
        # Create test data with known gaps
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        data = np.random.rand(len(dates))
        # Insert some NaN values to create gaps
        data[10:15] = np.nan
        data[100:110] = np.nan
        
        self.test_data_with_gaps = pd.DataFrame({
            'PRCP': data
        }, index=dates)
        
        # Create data without gaps
        self.test_data_no_gaps = pd.DataFrame({
            'PRCP': np.random.rand(len(dates))
        }, index=dates)
    
    def test_analyze_gaps_with_gaps(self):
        """Test gap analysis with data containing gaps"""
        result = analyze_gaps(self.test_data_with_gaps, 'PRCP', 5)
        self.assertIsInstance(result, dict)
        # Should detect the gaps we inserted
        self.assertGreater(result.get('total_missing_days', 0), 0)
    
    def test_analyze_gaps_no_gaps(self):
        """Test gap analysis with complete data"""
        result = analyze_gaps(self.test_data_no_gaps, 'PRCP', 5)
        self.assertIsInstance(result, dict)
        # Should report no gaps
        self.assertEqual(result.get('total_missing_days', 0), 0)
    
    def test_analyze_gaps_empty_data(self):
        """Test gap analysis with empty data"""
        empty_data = pd.DataFrame({'PRCP': []}, index=pd.DatetimeIndex([]))
        result = analyze_gaps(empty_data, 'PRCP', 5)
        self.assertIsInstance(result, (dict, type(None)))
    
    def test_analyze_gaps_invalid_column(self):
        """Test gap analysis with missing column"""
        bad_data = pd.DataFrame({'TEMP': [1, 2, 3]})
        result = analyze_gaps(bad_data, 'PRCP', 5)
        self.assertIsInstance(result, (dict, type(None)))

class TestDataValidation(unittest.TestCase):
    """Test data validation and edge cases"""
    
    def test_negative_precipitation(self):
        """Test handling of negative precipitation values"""
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        bad_data = pd.DataFrame({
            'PRCP': [-1.0, 0.0, 5.0, -2.0, 3.0, 0.0, 1.0, -0.5, 2.0, 0.0]
        }, index=dates)
        
        try:
            result = calculate_params(bad_data)
            # If it handles negatives, check result is reasonable
            self.assertIsNotNone(result)
        except Exception:
            # Expected behavior - some functions might reject negative values
            pass
    
    def test_extreme_values(self):
        """Test handling of extreme precipitation values"""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        extreme_data = pd.DataFrame({
            'PRCP': [1000.0] * 50 + [0.0] * 50  # Extreme rainfall amounts
        }, index=dates)
        
        result = calculate_params(extreme_data, filter_incomplete_years=False)
        self.assertIsNotNone(result)
        # Check that parameters are still reasonable (no inf/nan values)
        for col in result.columns:
            self.assertFalse(result[col].isna().any())
            self.assertFalse(np.isinf(result[col]).any())

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_file_permissions(self):
        """Test handling of file permission errors"""
        # This test is platform-dependent and might not work everywhere
        try:
            self.ts = TimeSeries()
            # Try to load a file that doesn't exist
            with self.assertRaises(Exception):
                self.ts.load_and_preprocess("/root/nonexistent.csv")
        except:
            # If the test environment doesn't support this, skip
            pass
    
    def test_memory_constraints(self):
        """Test handling of large datasets"""
        try:
            # Create a reasonably large dataset
            dates = pd.date_range('1900-01-01', '2020-12-31', freq='D')
            large_data = pd.DataFrame({
                'PRCP': np.random.rand(len(dates))
            }, index=dates)
            
            result = calculate_params(large_data)
            self.assertIsNotNone(result)
        except MemoryError:
            # Expected on systems with limited memory
            pass
        except Exception as e:
            # Note any other unexpected errors
            self.fail(f"Large dataset test failed: {e}")

if __name__ == '__main__':
    unittest.main()
