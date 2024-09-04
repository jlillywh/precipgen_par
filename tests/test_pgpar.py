import unittest
import os
import sys
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pgpar import PrecipGenPAR

class TestPrecipGenPAR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file_path = os.path.join(os.path.dirname(__file__), "Example_TS.csv")
        if not os.path.exists(cls.file_path):
            raise FileNotFoundError(f"The file {cls.file_path} does not exist.")
        
        # Read the CSV file into a DataFrame
        df = pd.read_csv(cls.file_path)
        
        # Initialize PrecipGenPAR with the DataFrame
        cls.obj = PrecipGenPAR(df)

    def test_initialization_with_dataframe(self):
        df = pd.DataFrame({
            'DATE': pd.date_range(start='1/1/2021', periods=365),
            'PRCP': np.random.rand(365)
        })
        obj = PrecipGenPAR(df)
        self.assertIsInstance(obj.ts, pd.DataFrame)
        self.assertEqual(obj.value_col, 'PRCP')

    def test_initialization_with_invalid_input(self):
        with self.assertRaises(ValueError):
            PrecipGenPAR([1, 2, 3])  # Invalid input type

    def test_calculate_monthly_totals(self):
        monthly_totals = self.obj.calculate_monthly_totals()
        self.assertIsInstance(monthly_totals, pd.DataFrame)
        self.assertEqual(monthly_totals.index.name, 'Month')
        self.assertIn(self.obj.value_col, monthly_totals.columns)
        self.assertEqual(len(monthly_totals), 12)  # Ensure we have 12 months
        expected_months = pd.date_range(start='2000-01-01', periods=12, freq='ME').strftime('%B')
        self.assertListEqual(list(monthly_totals.index), list(expected_months))

    def test_calculate_mean_daily(self):
        self.obj.calculate_mean_daily()
        self.assertIn('Mean', self.obj.params.columns)
        self.assertEqual(len(self.obj.params['Mean']), 12)
        self.assertTrue(all(self.obj.params['Mean'] >= 0))

    def test_calculate_sd_daily(self):
        self.obj.calculate_sd_daily()
        self.assertIn('SD', self.obj.params.columns)
        self.assertEqual(len(self.obj.params['SD']), 12)
        self.assertTrue(all(self.obj.params['SD'] >= 0))

    def test_calculate_wet_dry_days(self):
        self.obj.calculate_wet_dry_days()
        self.assertIn('is_wet', self.obj.ts.columns)
        self.assertIn('is_dry', self.obj.ts.columns)
        self.assertIn('prev_day_wet', self.obj.ts.columns)
        self.assertIn('prev_day_dry', self.obj.ts.columns)
        self.assertTrue(all(self.obj.ts['is_wet'] == (self.obj.ts['PRCP'] > 0)))
        self.assertTrue(all(self.obj.ts['is_dry'] == (self.obj.ts['PRCP'] == 0)))

    def test_calculate_probabilities(self):
        self.obj.calculate_probabilities()
        self.assertIn('PWW', self.obj.params.columns)
        self.assertIn('PWD', self.obj.params.columns)
        self.assertEqual(len(self.obj.params['PWW']), 12)
        self.assertEqual(len(self.obj.params['PWD']), 12)
        self.assertTrue(all((0 <= self.obj.params['PWW']) & (self.obj.params['PWW'] <= 1)))
        self.assertTrue(all((0 <= self.obj.params['PWD']) & (self.obj.params['PWD'] <= 1)))

    def test_get_parameters(self):
        params = self.obj.get_parameters()
        for condition in ['dry', 'all', 'wet']:
            self.assertIn(condition, params)
            self.assertIsInstance(params[condition], pd.DataFrame)
            self.assertEqual(params[condition].shape, (12, 5))
            expected_columns = ['Month', 'Mean', 'SD', 'PWW', 'PWD']
            self.assertListEqual(params[condition].columns.tolist(), expected_columns)

    @patch('pgpar.PrecipGenPAR.calculate_autocorrelation_ann_precip')
    def test_get_obs_stats(self, mock_autocorr):
        mock_autocorr.return_value = (0.5, 1)  # Mock autocorrelation result
        obs_stats = self.obj.get_obs_stats()
        
        self.assertIsInstance(obs_stats, pd.DataFrame)
        expected_columns = ['MonthNum', 'min', 'max', 'mean']
        self.assertListEqual(list(obs_stats.columns), expected_columns)
        self.assertEqual(len(obs_stats), 12)
        self.assertListEqual(obs_stats['MonthNum'].tolist(), list(range(1, 13)))
        
        for column in ['min', 'max', 'mean']:
            self.assertTrue(np.issubdtype(obs_stats[column].dtype, np.number))
        
        self.assertTrue(all(obs_stats['min'] <= obs_stats['mean']))
        self.assertTrue(all(obs_stats['mean'] <= obs_stats['max']))

    def test_calculate_monthly_distribution(self):
        distribution = self.obj.calculate_monthly_distribution()
        self.assertIsInstance(distribution, pd.DataFrame)
        self.assertIn('Month', distribution.columns)
        self.assertIn('Total', distribution.columns)
        self.assertIn('Probability', distribution.columns)
        self.assertTrue(all(distribution['Probability'] >= 0) and all(distribution['Probability'] <= 1))

    def test_longest_run_of_dry_days(self):
        longest_dry = self.obj.longest_run_of_dry_days()
        self.assertIsInstance(longest_dry, int)
        self.assertGreaterEqual(longest_dry, 0)

    def test_longest_run_of_wet_days(self):
        longest_wet = self.obj.longest_run_of_wet_days()
        self.assertIsInstance(longest_wet, int)
        self.assertGreaterEqual(longest_wet, 0)

    @patch('pgpar.PrecipGenPAR.calculate_parameters')
    def test_calculate_yearly_pww_pwd(self, mock_calculate_parameters):
        mock_calculate_parameters.return_value = pd.DataFrame({
            'Month': range(1, 13),
            'Mean': np.random.rand(12),
            'SD': np.random.rand(12),
            'PWW': np.random.rand(12),
            'PWD': np.random.rand(12)
        })
        result = self.obj.calculate_yearly_pww_pwd()
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.index.nlevels, 2)  # Multi-index with Year and Month
        self.assertIn('PWW', result.columns)
        self.assertIn('PWD', result.columns)

    def test_calculate_pww_pwd_correlation(self):
        correlation = self.obj.calculate_pww_pwd_correlation()
        self.assertIsInstance(correlation, float)
        self.assertTrue(-1 <= correlation <= 1)

    def test_calculate_pww_mean_correlation(self):
        correlation = self.obj.calculate_pww_mean_correlation()
        self.assertIsInstance(correlation, float)
        self.assertTrue(-1 <= correlation <= 1)

    @patch('pgpar.PrecipGenPAR.calculate_autocorrelation_ann_precip')
    def test_calculate_autocorrelation_ann_precip(self, mock_autocorr):
        mock_autocorr.return_value = (0.5, 2)
        autocorrelation, optimal_lag = self.obj.calculate_autocorrelation_ann_precip()
        self.assertIsInstance(autocorrelation, float)
        self.assertIsInstance(optimal_lag, int)
        self.assertTrue(-1 <= autocorrelation <= 1)
        self.assertGreaterEqual(optimal_lag, 1)

if __name__ == '__main__':
    unittest.main()