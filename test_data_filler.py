#!/usr/bin/env python3
"""
Test suite for the data filling module.

Tests the various gap filling methods and their effectiveness.
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import os
from datetime import datetime, timedelta
import sys
import warnings

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_filler import PrecipitationDataFiller, fill_precipitation_data

class TestDataFiller(unittest.TestCase):
    """Test suite for precipitation data filling functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.filler = PrecipitationDataFiller()
        
        # Create synthetic test data
        start_date = datetime(2000, 1, 1)
        end_date = datetime(2005, 12, 31)
        dates = pd.date_range(start_date, end_date, freq='D')
        
        # Generate realistic precipitation data
        np.random.seed(42)  # For reproducible tests
        
        # Seasonal pattern with random variations
        day_of_year = dates.dayofyear
        seasonal_pattern = 0.5 + 0.3 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
          # Add random precipitation events
        precip_events = np.random.exponential(0.8, len(dates)) * seasonal_pattern
        
        # Create dry days (60% of days are dry)
        dry_mask = np.random.random(len(dates)) < 0.6
        precip_events = np.array(precip_events)  # Convert to numpy array for mutability
        precip_events[dry_mask] = 0.0
        
        self.test_data = pd.DataFrame({
            'DATE': dates,
            'PRCP': precip_events
        })
        
        # Create version with missing data
        self.test_data_with_gaps = self.test_data.copy()
        
    def create_gap(self, start_date, end_date):
        """Helper to create gaps in test data."""
        mask = (self.test_data_with_gaps['DATE'] >= start_date) & \
               (self.test_data_with_gaps['DATE'] <= end_date)
        self.test_data_with_gaps.loc[mask, 'PRCP'] = np.nan
        
    def test_identify_gaps(self):
        """Test gap identification."""
        # Create specific gaps
        self.create_gap(datetime(2002, 3, 15), datetime(2002, 3, 16))  # 2-day gap
        self.create_gap(datetime(2003, 7, 10), datetime(2003, 7, 15))  # 6-day gap
        
        gaps = self.filler._identify_gaps(self.test_data_with_gaps, 'DATE', 'PRCP')
        
        self.assertEqual(len(gaps), 2)
        self.assertEqual(gaps[0]['length'], 2)
        self.assertEqual(gaps[1]['length'], 6)
        
    def test_linear_interpolation(self):
        """Test linear interpolation for short gaps."""
        # Create a 2-day gap
        self.create_gap(datetime(2002, 6, 15), datetime(2002, 6, 16))
        
        # Get before and after values
        before_val = self.test_data_with_gaps[
            self.test_data_with_gaps['DATE'] == datetime(2002, 6, 14)
        ]['PRCP'].iloc[0]
        after_val = self.test_data_with_gaps[
            self.test_data_with_gaps['DATE'] == datetime(2002, 6, 17)
        ]['PRCP'].iloc[0]
        
        # Apply filling
        filled_data, report = self.filler.fill_missing_data(
            self.test_data_with_gaps.copy()
        )
        
        # Check that gap was filled
        filled_vals = filled_data[
            (filled_data['DATE'] >= datetime(2002, 6, 15)) &
            (filled_data['DATE'] <= datetime(2002, 6, 16))
        ]['PRCP'].values
        
        self.assertEqual(len(filled_vals), 2)
        self.assertFalse(np.any(np.isnan(filled_vals)))
        self.assertTrue(report['methods_used']['linear_interpolation'] > 0)
        
    def test_climatological_fill(self):
        """Test climatological filling for medium gaps."""
        # Create a 5-day gap in summer
        self.create_gap(datetime(2002, 7, 15), datetime(2002, 7, 19))
        
        filled_data, report = self.filler.fill_missing_data(
            self.test_data_with_gaps.copy()
        )
        
        # Check that gap was filled
        filled_vals = filled_data[
            (filled_data['DATE'] >= datetime(2002, 7, 15)) &
            (filled_data['DATE'] <= datetime(2002, 7, 19))
        ]['PRCP'].values
        
        self.assertEqual(len(filled_vals), 5)
        self.assertFalse(np.any(np.isnan(filled_vals)))
        self.assertTrue(all(val >= 0 for val in filled_vals))  # No negative precipitation
        
    def test_analogous_year_fill(self):
        """Test analogous year method for longer gaps."""
        # Create a 10-day gap
        self.create_gap(datetime(2002, 8, 15), datetime(2002, 8, 24))
        
        filled_data, report = self.filler.fill_missing_data(
            self.test_data_with_gaps.copy()
        )
        
        # Check that gap was filled
        filled_vals = filled_data[
            (filled_data['DATE'] >= datetime(2002, 8, 15)) &
            (filled_data['DATE'] <= datetime(2002, 8, 24))
        ]['PRCP'].values
        
        self.assertEqual(len(filled_vals), 10)
        self.assertFalse(np.any(np.isnan(filled_vals)))
        self.assertTrue(all(val >= 0 for val in filled_vals))
        
    def test_year_similarity_calculation(self):
        """Test the year similarity calculation."""
        similarity = self.filler._calculate_year_similarity(
            self.test_data, 2002, 2003, 'DATE', 'PRCP'
        )
        
        # Should be a valid correlation coefficient
        self.assertTrue(-1 <= similarity <= 1)
        
    def test_validation_results(self):
        """Test validation of filled data."""
        # Create some gaps
        self.create_gap(datetime(2002, 3, 15), datetime(2002, 3, 16))
        self.create_gap(datetime(2003, 7, 10), datetime(2003, 7, 15))
        
        filled_data, report = self.filler.fill_missing_data(
            self.test_data_with_gaps.copy()
        )
        
        # Check validation results
        validation = report['validation_results']
        self.assertIn('quality_good', validation)
        self.assertIn('mean_change', validation)
        self.assertIn('std_change', validation)
        self.assertEqual(validation['filled_data_negative'], 0)
        
    def test_maximum_gap_size(self):
        """Test that very large gaps are not filled."""
        # Create a 40-day gap (exceeds default max of 30)
        self.create_gap(datetime(2002, 6, 1), datetime(2002, 7, 10))
        
        filled_data, report = self.filler.fill_missing_data(
            self.test_data_with_gaps.copy()
        )
        
        # Gap should remain unfilled
        self.assertTrue(report['methods_used']['unfilled_gaps'] > 0)
        
        # Check that gap still exists
        gap_vals = filled_data[
            (filled_data['DATE'] >= datetime(2002, 6, 1)) &
            (filled_data['DATE'] <= datetime(2002, 7, 10))
        ]['PRCP']
        
        self.assertTrue(gap_vals.isna().any())
        
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with no missing data
        filled_data, report = self.filler.fill_missing_data(self.test_data.copy())
        self.assertEqual(report['status'], 'no_missing_data')
        
        # Test with all missing data
        all_missing = self.test_data.copy()
        all_missing['PRCP'] = np.nan
        
        filled_data, report = self.filler.fill_missing_data(all_missing)
        self.assertTrue(report['methods_used']['unfilled_gaps'] > 0)
        
    def test_file_io(self):
        """Test file input/output functionality."""
        # Create test gaps
        self.create_gap(datetime(2002, 3, 15), datetime(2002, 3, 16))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, 'test_input.csv')
            output_file = os.path.join(temp_dir, 'test_output.csv')
            
            # Save test data
            self.test_data_with_gaps.to_csv(input_file, index=False)
            
            # Use convenience function
            report = fill_precipitation_data(input_file, output_file)
            
            # Check that output file exists
            self.assertTrue(os.path.exists(output_file))
            
            # Check that report file exists
            report_file = output_file.replace('.csv', '_filling_report.json')
            self.assertTrue(os.path.exists(report_file))
            
            # Verify filled data
            filled_data = pd.read_csv(output_file)
            self.assertEqual(len(filled_data), len(self.test_data_with_gaps))
            
    def test_custom_parameters(self):
        """Test custom filling parameters."""
        filler = PrecipitationDataFiller(
            min_similarity_threshold=0.8,
            max_fill_gap_days=20,
            seasonal_window_days=10
        )
        
        # Create a gap
        self.create_gap(datetime(2002, 5, 10), datetime(2002, 5, 15))
        
        filled_data, report = filler.fill_missing_data(
            self.test_data_with_gaps.copy()
        )
        
        # Should still work with custom parameters
        self.assertTrue(report['summary']['values_filled'] > 0)
        
    def test_multiple_gaps_different_sizes(self):
        """Test filling multiple gaps of different sizes."""
        # Create various gap sizes
        self.create_gap(datetime(2001, 3, 15), datetime(2001, 3, 15))    # 1 day
        self.create_gap(datetime(2002, 6, 10), datetime(2002, 6, 11))    # 2 days
        self.create_gap(datetime(2003, 9, 5), datetime(2003, 9, 9))      # 5 days
        self.create_gap(datetime(2004, 12, 15), datetime(2004, 12, 25))  # 11 days
        
        filled_data, report = self.filler.fill_missing_data(
            self.test_data_with_gaps.copy()
        )
        
        # Check that different methods were used
        methods = report['methods_used']
        self.assertTrue(methods['linear_interpolation'] > 0)
        self.assertTrue(methods['climatological_normal'] > 0 or methods['analogous_year'] > 0)
        
        # Check overall success rate
        self.assertTrue(report['summary']['fill_success_rate'] > 80)
        
    def test_seasonal_patterns_preserved(self):
        """Test that seasonal patterns are preserved after filling."""
        # Create gaps throughout the year
        self.create_gap(datetime(2002, 3, 15), datetime(2002, 3, 17))   # Spring
        self.create_gap(datetime(2002, 7, 10), datetime(2002, 7, 12))   # Summer
        self.create_gap(datetime(2002, 11, 5), datetime(2002, 11, 7))   # Fall
        
        filled_data, report = self.filler.fill_missing_data(
            self.test_data_with_gaps.copy()
        )
        
        # Calculate seasonal means before and after
        original_seasonal = self.test_data.groupby(self.test_data['DATE'].dt.month)['PRCP'].mean()
        filled_seasonal = filled_data.groupby(filled_data['DATE'].dt.month)['PRCP'].mean()
        
        # Seasonal patterns should be similar
        correlation = np.corrcoef(original_seasonal, filled_seasonal)[0, 1]
        self.assertTrue(correlation > 0.9)


class TestRealWorldScenarios(unittest.TestCase):
    """Test data filling with realistic precipitation patterns."""
    
    def test_dry_period_filling(self):
        """Test filling gaps during typically dry periods."""
        # Create data with realistic dry season pattern
        dates = pd.date_range('2000-01-01', '2003-12-31', freq='D')
        
        # Simulate Mediterranean climate (dry summers)
        day_of_year = dates.dayofyear
        summer_dry = np.where((day_of_year >= 150) & (day_of_year <= 250), 0.1, 1.0)
        
        precip = np.random.exponential(0.5, len(dates)) * summer_dry
        dry_mask = np.random.random(len(dates)) < 0.7
        precip[dry_mask] = 0.0
        
        test_data = pd.DataFrame({'DATE': dates, 'PRCP': precip})
        
        # Create gap in dry season
        gap_mask = (test_data['DATE'] >= '2001-07-15') & (test_data['DATE'] <= '2001-07-20')
        test_data.loc[gap_mask, 'PRCP'] = np.nan
        
        filler = PrecipitationDataFiller()
        filled_data, report = filler.fill_missing_data(test_data)
        
        # Check that dry season characteristics are preserved
        filled_summer = filled_data[
            (filled_data['DATE'] >= '2001-07-15') & (filled_data['DATE'] <= '2001-07-20')
        ]['PRCP']
        
        # Values should be small (appropriate for dry season)
        self.assertTrue(filled_summer.mean() < 1.0)
        self.assertFalse(filled_summer.isna().any())
        
    def test_extreme_event_preservation(self):
        """Test that extreme precipitation events are handled appropriately."""
        # Create data with some extreme events
        dates = pd.date_range('2000-01-01', '2002-12-31', freq='D')
        precip = np.random.exponential(0.3, len(dates))
        
        # Add some extreme events
        extreme_days = np.random.choice(len(dates), 10, replace=False)
        precip[extreme_days] = np.random.uniform(5, 15, 10)  # Extreme events
        
        # Most days are dry
        dry_mask = np.random.random(len(dates)) < 0.8
        precip[dry_mask] = 0.0
        
        test_data = pd.DataFrame({'DATE': dates, 'PRCP': precip})
        
        # Create gaps near extreme events
        gap_mask = (test_data['DATE'] >= '2001-06-10') & (test_data['DATE'] <= '2001-06-15')
        test_data.loc[gap_mask, 'PRCP'] = np.nan
        
        filler = PrecipitationDataFiller()
        filled_data, report = filler.fill_missing_data(test_data)
        
        # Validation should flag if extreme values were created inappropriately
        validation = report['validation_results']
        self.assertTrue(validation['filled_data_extreme'] < 5)  # Should be reasonable


if __name__ == '__main__':
    # Suppress warnings for cleaner test output
    warnings.filterwarnings('ignore')
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    for test_class in [TestDataFiller, TestRealWorldScenarios]:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
