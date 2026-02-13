"""
Test suite for CalibrationController.

This test suite validates the CalibrationController functionality including
parameter adjustment, validation, reset operations, and export.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime, date
import pandas as pd

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.calibration_controller import CalibrationController, AdjustedParameters
from precipgen.desktop.controllers.data_controller import HistoricalParameters


class TestCalibrationController(unittest.TestCase):
    """Test suite for CalibrationController class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app_state = AppState()
        self.controller = CalibrationController(self.app_state)
        
        # Create mock historical parameters
        self.historical_params = self._create_mock_historical_params()
    
    def _create_mock_historical_params(self):
        """Create mock historical parameters for testing."""
        # Create monthly parameter values (12 months)
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
    
    def test_initialization(self):
        """Test that CalibrationController initializes correctly."""
        assert self.controller.app_state is self.app_state
    
    def test_adjust_parameter_no_historical(self):
        """Test that adjusting parameter without historical params fails."""
        result = self.controller.adjust_parameter('alpha', 1, 2.0)
        
        assert result.success is False
        assert "No historical parameters" in result.error
    
    def test_adjust_parameter_invalid_month(self):
        """Test that invalid month values are rejected."""
        self.app_state.set_historical_params(self.historical_params)
        
        # Test month < 1
        result = self.controller.adjust_parameter('alpha', 0, 2.0)
        assert result.success is False
        assert "Invalid month" in result.error
        
        # Test month > 12
        result = self.controller.adjust_parameter('alpha', 13, 2.0)
        assert result.success is False
        assert "Invalid month" in result.error
    
    def test_adjust_parameter_invalid_name(self):
        """Test that invalid parameter names are rejected."""
        self.app_state.set_historical_params(self.historical_params)
        
        result = self.controller.adjust_parameter('invalid_param', 1, 2.0)
        assert result.success is False
        assert "Invalid parameter name" in result.error
    
    def test_adjust_parameter_success(self):
        """Test successful parameter adjustment."""
        self.app_state.set_historical_params(self.historical_params)
        
        result = self.controller.adjust_parameter('alpha', 1, 2.5)
        
        assert result.success is True
        assert result.value is not None
        assert isinstance(result.value, AdjustedParameters)
        
        # Verify the parameter was adjusted
        adjusted_params = self.app_state.adjusted_params
        assert adjusted_params is not None
        assert adjusted_params.alpha.iloc[0, 0] == 2.5
    
    def test_validate_parameter_alpha_beta(self):
        """Test validation of alpha and beta parameters."""
        # Valid values
        is_valid, error = self.controller.validate_parameter('alpha', 1.5)
        assert is_valid is True
        assert error is None
        
        is_valid, error = self.controller.validate_parameter('beta', 0.5)
        assert is_valid is True
        assert error is None
        
        # Invalid: <= 0
        is_valid, error = self.controller.validate_parameter('alpha', 0.0)
        assert is_valid is False
        assert "must be greater than 0" in error
        
        is_valid, error = self.controller.validate_parameter('beta', -1.0)
        assert is_valid is False
        assert "must be greater than 0" in error
        
        # Invalid: too large
        is_valid, error = self.controller.validate_parameter('alpha', 15.0)
        assert is_valid is False
        assert "unreasonably large" in error
    
    def test_validate_parameter_probabilities(self):
        """Test validation of probability parameters."""
        # Valid values
        is_valid, error = self.controller.validate_parameter('p_wet_wet', 0.5)
        assert is_valid is True
        assert error is None
        
        is_valid, error = self.controller.validate_parameter('p_wet_dry', 0.0)
        assert is_valid is True
        assert error is None
        
        is_valid, error = self.controller.validate_parameter('p_dry_wet', 1.0)
        assert is_valid is True
        assert error is None
        
        # Invalid: < 0
        is_valid, error = self.controller.validate_parameter('p_wet_wet', -0.1)
        assert is_valid is False
        assert "must be between 0.0 and 1.0" in error
        
        # Invalid: > 1
        is_valid, error = self.controller.validate_parameter('p_dry_dry', 1.5)
        assert is_valid is False
        assert "must be between 0.0 and 1.0" in error
    
    def test_reset_to_historical_no_params(self):
        """Test that reset without historical params fails."""
        result = self.controller.reset_to_historical()
        
        assert result.success is False
        assert "No historical parameters" in result.error
    
    def test_reset_to_historical_success(self):
        """Test successful reset to historical values."""
        self.app_state.set_historical_params(self.historical_params)
        
        # First adjust a parameter
        self.controller.adjust_parameter('alpha', 1, 3.0)
        
        # Verify it was adjusted
        assert self.app_state.adjusted_params.alpha.iloc[0, 0] == 3.0
        
        # Reset to historical
        result = self.controller.reset_to_historical()
        
        assert result.success is True
        assert result.value is not None
        
        # Verify parameters were reset
        adjusted_params = self.app_state.adjusted_params
        assert adjusted_params.alpha.iloc[0, 0] == 1.5  # Original historical value
    
    def test_deviation_calculation(self):
        """Test that deviations are calculated correctly."""
        self.app_state.set_historical_params(self.historical_params)
        
        # Adjust alpha for month 1 from 1.5 to 2.5
        result = self.controller.adjust_parameter('alpha', 1, 2.5)
        
        assert result.success is True
        
        # Check deviation
        adjusted_params = self.app_state.adjusted_params
        deviation = adjusted_params.deviations['alpha'].iloc[0, 0]
        
        # Deviation should be 2.5 - 1.5 = 1.0
        assert abs(deviation - 1.0) < 1e-10
    
    def test_export_parameters_no_project_folder(self):
        """Test that export without project folder fails."""
        self.app_state.set_historical_params(self.historical_params)
        
        result = self.controller.export_parameters()
        
        assert result.success is False
        assert "No project folder" in result.error
    
    def test_export_parameters_no_params(self):
        """Test that export without parameters fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            
            result = self.controller.export_parameters()
            
            assert result.success is False
            assert "No parameters available" in result.error
    
    def test_export_parameters_success(self):
        """Test successful parameter export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            result = self.controller.export_parameters()
            
            assert result.success is True
            assert result.value is not None
            assert isinstance(result.value, Path)
            assert result.value.exists()
            
            # Verify metadata file was created
            metadata_file = result.value.with_suffix('.txt')
            assert metadata_file.exists()
            
            # Verify CSV content
            import csv
            with open(result.value, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 12  # 12 months
                
                # Check that all required columns exist
                assert 'ALPHA' in rows[0]
                assert 'BETA' in rows[0]
                assert 'PWW' in rows[0]
                assert 'PWD' in rows[0]
    
    def test_export_adjusted_parameters(self):
        """Test that adjusted parameters are exported when available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app_state.set_project_folder(Path(tmpdir))
            self.app_state.set_historical_params(self.historical_params)
            
            # Adjust a parameter
            self.controller.adjust_parameter('alpha', 1, 3.0)
            
            # Export
            result = self.controller.export_parameters()
            
            assert result.success is True
            
            # Read the exported file and verify adjusted value
            import csv
            with open(result.value, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # First row should have adjusted alpha value
                assert float(rows[0]['ALPHA']) == 3.0


if __name__ == '__main__':
    unittest.main()
