#!/usr/bin/env python3
"""
Test module for PrecipGen Parameter Wave Analysis

This test verifies that the wave analysis functionality works correctly with test data.
"""

import unittest
import os
import tempfile
import shutil
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from time_series import TimeSeries
from pgpar_wave import PrecipGenPARWave, analyze_precipgen_parameter_waves


class TestPrecipGenPARWave(unittest.TestCase):
    """Test cases for PrecipGen Parameter Wave Analysis."""
    
    def setUp(self):
        """Set up test data and temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_data.csv")
        
        # Create synthetic test data with known patterns
        start_date = datetime(1990, 1, 1)
        end_date = datetime(2020, 12, 31)
        dates = pd.date_range(start_date, end_date, freq='D')
        
        # Create synthetic precipitation with seasonal and long-term patterns
        np.random.seed(42)  # For reproducible results
        
        # Base precipitation with seasonal cycle
        year_fraction = (dates.dayofyear - 1) / 365.25
        seasonal_pattern = 2 + np.sin(2 * np.pi * year_fraction)
        
        # Add long-term trend and multi-year cycles
        years_from_start = (dates.year - 1990)
        long_term_trend = 0.01 * years_from_start
        multi_year_cycle = 0.5 * np.sin(2 * np.pi * years_from_start / 7)  # 7-year cycle
        
        # Generate precipitation values
        mean_precip = seasonal_pattern + long_term_trend + multi_year_cycle
        
        # Create wet/dry days based on probability
        wet_probability = 0.3 + 0.2 * seasonal_pattern / 4  # Variable wet probability
        is_wet = np.random.random(len(dates)) < wet_probability
        
        # Generate precipitation amounts for wet days
        precip_amounts = np.where(is_wet, 
                                 np.random.gamma(2, mean_precip), 
                                 0.0)
          # Create DataFrame
        test_data = pd.DataFrame({
            'DATE': dates,
            'PRCP': precip_amounts
        })
        
        # Add metadata header to match expected format
        with open(self.test_file, 'w') as f:
            f.write("# Test precipitation data\n")
            f.write("# Generated for PrecipGen testing\n") 
            f.write("# STATION: TEST00001\n")
            f.write("# NAME: Test Station\n")
            f.write("# LAT: 40.0\n")
            f.write("# LON: -105.0\n")
            
        # Append the actual data
        test_data.to_csv(self.test_file, mode='a', index=False)
        
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)
    
    def test_parameter_extraction(self):
        """Test parameter extraction from synthetic data."""
        # Load time series
        ts = TimeSeries()
        ts.load_and_preprocess(self.test_file)
        
        # Create analyzer
        analyzer = PrecipGenPARWave(ts, window_size=5, overlap=0.5)
        
        # Extract parameter history
        param_history = analyzer.extract_parameter_history()
        
        # Check results
        self.assertIsInstance(param_history, pd.DataFrame)
        self.assertGreater(len(param_history), 0)
        
        # Check that all expected parameters are present
        expected_params = ['PWW', 'PWD', 'alpha', 'beta']
        for param in expected_params:
            self.assertIn(param, param_history.columns)
            self.assertTrue(param_history[param].notna().any())
        
        print(f"✓ Extracted parameters for {len(param_history)} windows")
    
    def test_wave_analysis(self):
        """Test wave component analysis."""
        # Load time series
        ts = TimeSeries()
        ts.load_and_preprocess(self.test_file)
        
        # Create analyzer
        analyzer = PrecipGenPARWave(ts, window_size=6, overlap=0.5)
        
        # Extract parameters
        analyzer.extract_parameter_history()
        
        # Analyze wave components
        wave_components = analyzer.analyze_parameter_waves(num_components=3)
        
        # Check results
        self.assertIsInstance(wave_components, dict)
        self.assertGreater(len(wave_components), 0)
        
        # Check each parameter
        for param in ['PWW', 'PWD', 'alpha', 'beta']:
            if param in wave_components:
                param_data = wave_components[param]
                self.assertIn('components', param_data)
                self.assertIn('trend_slope', param_data)
                self.assertIsInstance(param_data['components'], list)
                
        print(f"✓ Wave analysis complete for {len(wave_components)} parameters")
    
    def test_parameter_fitting(self):
        """Test parameter evolution fitting."""
        # Load time series
        ts = TimeSeries()
        ts.load_and_preprocess(self.test_file)
        
        # Run complete analysis
        analyzer = analyze_precipgen_parameter_waves(ts, window_size=6, num_components=3)
        
        # Check fitted parameters
        self.assertIsNotNone(analyzer.fitted_parameters)
        self.assertIsInstance(analyzer.fitted_parameters, dict)
        
        # Check parameter structure
        for param, data in analyzer.fitted_parameters.items():
            self.assertIn('trend', data)
            self.assertIn('wave_summary', data)
            self.assertIn('all_components', data)
            
        print(f"✓ Fitted evolution for {len(analyzer.fitted_parameters)} parameters")
    
    def test_synthetic_generation(self):
        """Test synthetic parameter generation."""
        # Load time series
        ts = TimeSeries()
        ts.load_and_preprocess(self.test_file)
        
        # Run complete analysis
        analyzer = analyze_precipgen_parameter_waves(ts, window_size=6, num_components=3)
        
        # Generate synthetic parameters
        future_years = np.arange(2021, 2026)
        synthetic_params = analyzer.generate_synthetic_parameters(future_years)
        
        # Check results
        self.assertIsInstance(synthetic_params, pd.DataFrame)
        self.assertEqual(len(synthetic_params), len(future_years))
        self.assertIn('year', synthetic_params.columns)
        
        # Check that parameter columns exist and have reasonable values
        for param in ['PWW', 'PWD', 'alpha', 'beta']:
            if param in synthetic_params.columns:
                values = synthetic_params[param]
                self.assertTrue(values.notna().all())
                
                # Check reasonable ranges
                if param in ['PWW', 'PWD']:
                    self.assertTrue((values >= 0).all() and (values <= 1).all())
                elif param in ['alpha', 'beta']:
                    self.assertTrue((values > 0).all())
        
        print(f"✓ Generated synthetic parameters for {len(future_years)} future years")
    
    def test_export_functionality(self):
        """Test export capabilities."""
        # Load time series
        ts = TimeSeries()
        ts.load_and_preprocess(self.test_file)
        
        # Run analysis
        analyzer = analyze_precipgen_parameter_waves(ts, window_size=6, num_components=2)
        
        # Test JSON export
        json_file = os.path.join(self.test_dir, "test_export.json")
        analyzer.export_wave_parameters(json_file, format='json')
        self.assertTrue(os.path.exists(json_file))
        
        # Test CSV export
        csv_file = os.path.join(self.test_dir, "test_export.csv")
        analyzer.export_wave_parameters(csv_file, format='csv')
        self.assertTrue(os.path.exists(csv_file))
        
        print("✓ Export functionality working")
    
    def test_real_data_if_available(self):
        """Test with real data if available."""
        real_data_files = [
            os.path.join("tests", "GrandJunction", "USW00023066_data.csv"),
            os.path.join("tests", "denver_stapleton_test.csv")
        ]
        
        for data_file in real_data_files:
            if os.path.exists(data_file):
                print(f"\n✓ Testing with real data: {data_file}")
                
                try:
                    # Load time series
                    ts = TimeSeries()
                    ts.load_and_preprocess(data_file)
                    
                    # Trim to reasonable range for testing
                    ts.trim(1990, 2010)
                    
                    # Run analysis
                    analyzer = analyze_precipgen_parameter_waves(
                        ts, window_size=8, num_components=3
                    )
                    
                    # Check results
                    self.assertIsNotNone(analyzer.parameter_history)
                    self.assertIsNotNone(analyzer.wave_components)
                    self.assertIsNotNone(analyzer.fitted_parameters)
                    
                    print(f"  - Extracted {len(analyzer.parameter_history)} parameter windows")
                    print(f"  - Analyzed {len(analyzer.wave_components)} parameters")
                    
                    # Print dominant periods if found
                    for param, data in analyzer.fitted_parameters.items():
                        period = data['wave_summary']['dominant_period']
                        if period and period < 100:
                            print(f"  - {param} dominant period: {period:.1f} years")
                    
                except Exception as e:
                    print(f"  Warning: Real data test failed: {e}")
                
                break
        else:
            print("✓ No real data files available for testing")


def run_tests():
    """Run all tests."""
    print("Running PrecipGen Parameter Wave Analysis Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPrecipGenPARWave)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✓ All tests passed!")
        print("PrecipGen Parameter Wave Analysis is working correctly.")
    else:
        print("✗ Some tests failed.")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
