"""
Test suite for verifying export functionality.

This test verifies that parameter export works correctly with proper
file creation, metadata, and content validation.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import csv

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.calibration_controller import CalibrationController
from precipgen.desktop.controllers.data_controller import HistoricalParameters


class TestExportVerification(unittest.TestCase):
    """Test suite for export functionality verification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app_state = AppState()
        self.controller = CalibrationController(self.app_state)
        
        # Create mock historical parameters
        self.historical_params = self._create_mock_historical_params()
    
    def _create_mock_historical_params(self):
        """Create mock historical parameters for testing."""
        months = range(1, 13)
        
        alpha_df = pd.DataFrame({'ALPHA': [1.5] * 12}, index=months)
        beta_df = pd.DataFrame({'BETA': [0.8] * 12}, index=months)
        pww_df = pd.DataFrame({'PWW': [0.6] * 12}, index=months)
        pwd_df = pd.DataFrame({'PWD': [0.3] * 12}, index=months)
        pdw_df = pd.DataFrame({'PDW': [0.4] * 12}, index=months)
        pdd_df = pd.DataFrame({'PDD': [0.7] * 12}, index=months)
        
        return HistoricalParameters(
            alpha=alpha_df,
            beta=beta_df,
            p_wet_wet=pww_df,
            p_wet_dry=pwd_df,
            p_dry_wet=pdw_df,
            p_dry_dry=pdd_df,
            calculation_date=datetime.now(),
            source_station="TEST_STATION",
            date_range=(date(2000, 1, 1), date(2020, 12, 31))
        )
    
    def test_export_creates_csv_file(self):
        """Test that export creates a CSV file in the project folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            result = self.controller.export_parameters()
            
            assert result.success is True
            assert result.value is not None
            assert result.value.exists()
            assert result.value.suffix == '.csv'
            assert result.value.parent.name == 'exports'
    
    def test_export_creates_metadata_file(self):
        """Test that export creates a metadata file alongside the CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            result = self.controller.export_parameters()
            
            assert result.success is True
            
            # Check metadata file exists
            metadata_file = result.value.with_suffix('.txt')
            assert metadata_file.exists()
            
            # Verify metadata content
            with open(metadata_file, 'r') as f:
                content = f.read()
                assert 'PrecipGen Parameter Export' in content
                assert 'TEST_STATION' in content
                assert '2000-01-01' in content
                assert '2020-12-31' in content
    
    def test_export_csv_has_correct_structure(self):
        """Test that exported CSV has correct columns and rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            result = self.controller.export_parameters()
            
            assert result.success is True
            
            # Read and verify CSV structure
            with open(result.value, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # Should have 12 rows (one per month)
                assert len(rows) == 12
                
                # Check required columns exist
                required_columns = ['ALPHA', 'BETA', 'PWW', 'PWD', 'PDW', 'PDD']
                for col in required_columns:
                    assert col in rows[0], f"Missing column: {col}"
    
    def test_export_csv_has_correct_values(self):
        """Test that exported CSV contains correct parameter values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            result = self.controller.export_parameters()
            
            assert result.success is True
            
            # Read and verify values
            with open(result.value, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # Check first row values match historical parameters
                assert float(rows[0]['ALPHA']) == 1.5
                assert float(rows[0]['BETA']) == 0.8
                assert float(rows[0]['PWW']) == 0.6
                assert float(rows[0]['PWD']) == 0.3
    
    def test_export_adjusted_parameters_has_correct_values(self):
        """Test that adjusted parameters are exported with correct values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            # Adjust alpha for month 1
            self.controller.adjust_parameter('alpha', 1, 3.0)
            
            result = self.controller.export_parameters()
            
            assert result.success is True
            
            # Read and verify adjusted value
            with open(result.value, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # First row should have adjusted alpha
                assert float(rows[0]['ALPHA']) == 3.0
                
                # Other months should still have historical value
                assert float(rows[1]['ALPHA']) == 1.5
    
    def test_export_filename_includes_station_and_timestamp(self):
        """Test that export filename includes station ID and timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            result = self.controller.export_parameters()
            
            assert result.success is True
            
            # Check filename format
            filename = result.value.name
            assert 'TEST_STATION' in filename
            assert 'params' in filename
            assert filename.endswith('.csv')
    
    def test_export_to_custom_path(self):
        """Test that export can write to a custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            # Create custom output path
            custom_path = Path(tmpdir) / 'custom' / 'output.csv'
            custom_path.parent.mkdir(parents=True, exist_ok=True)
            
            result = self.controller.export_parameters(output_path=custom_path)
            
            assert result.success is True
            assert result.value == custom_path
            assert custom_path.exists()
    
    def test_multiple_exports_create_unique_files(self):
        """Test that multiple exports create unique files with timestamps."""
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            # Export twice with a small delay to ensure different timestamps
            result1 = self.controller.export_parameters()
            time.sleep(1.1)  # Wait just over 1 second to ensure different timestamp
            result2 = self.controller.export_parameters()
            
            assert result1.success is True
            assert result2.success is True
            
            # Files should be different (due to timestamp)
            assert result1.value != result2.value
            assert result1.value.exists()
            assert result2.value.exists()


if __name__ == '__main__':
    unittest.main()
