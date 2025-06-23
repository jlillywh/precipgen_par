#!/usr/bin/env python3
"""
Simple gap analysis tests that should work correctly
"""

import unittest
import sys
import os
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gap_analyzer import analyze_gaps

class TestGapAnalysisSimple(unittest.TestCase):
    """Simple gap analysis tests"""
    
    def setUp(self):
        # Create test data with known gaps
        dates = pd.date_range('2020-01-01', '2020-01-31', freq='D')
        data = np.ones(len(dates))
        # Insert some NaN values to create gaps
        data[10:15] = np.nan  # 5-day gap
        data[20:22] = np.nan  # 2-day gap
        
        self.test_data_with_gaps = pd.DataFrame({
            'PRCP': data
        }, index=dates)
        
        # Create data without gaps
        self.test_data_no_gaps = pd.DataFrame({
            'PRCP': np.ones(len(dates))
        }, index=dates)
    
    def test_analyze_gaps_with_gaps(self):
        """Test gap analysis with data containing gaps"""
        result = analyze_gaps(self.test_data_with_gaps, 'PRCP', 3)
        self.assertIsInstance(result, dict)
        # Should detect the gaps we inserted
        self.assertGreater(result.get('total_missing_days', 0), 0)
    
    def test_analyze_gaps_no_gaps(self):
        """Test gap analysis with complete data"""
        result = analyze_gaps(self.test_data_no_gaps, 'PRCP', 3)
        self.assertIsInstance(result, dict)
        # Should report no gaps
        self.assertEqual(result.get('total_missing_days', 0), 0)
    
    def test_analyze_gaps_empty_data(self):
        """Test gap analysis with empty data"""
        empty_data = pd.DataFrame({'PRCP': []}, index=pd.DatetimeIndex([]))
        result = analyze_gaps(empty_data, 'PRCP', 5)
        self.assertIsNone(result)  # Function returns None for empty data
    
    def test_analyze_gaps_invalid_column(self):
        """Test gap analysis with missing column"""
        bad_data = pd.DataFrame({'TEMP': [1, 2, 3]}, index=pd.date_range('2020-01-01', periods=3))
        result = analyze_gaps(bad_data, 'PRCP', 5)
        self.assertIsNone(result)  # Function returns None for missing columns

if __name__ == '__main__':
    unittest.main(verbosity=2)
