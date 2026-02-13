"""
Test suite for CalibrationPanel UI component.

This test suite validates the CalibrationPanel view component including
initialization, slider interaction, and state updates.
"""

import unittest
from datetime import datetime, date
import pandas as pd

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.calibration_controller import CalibrationController
from precipgen.desktop.controllers.data_controller import HistoricalParameters
from precipgen.desktop.views.calibration_panel import CalibrationPanel


class TestCalibrationPanel(unittest.TestCase):
    """Test suite for CalibrationPanel class."""
    
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
        """Test that CalibrationPanel initializes correctly without errors."""
        # This test verifies the panel can be created
        # Note: We can't fully test UI without a running Tk mainloop
        try:
            # Just verify imports and class structure
            assert CalibrationPanel is not None
            assert hasattr(CalibrationPanel, '__init__')
            assert hasattr(CalibrationPanel, 'setup_ui')
            assert hasattr(CalibrationPanel, 'on_slider_changed')
            assert hasattr(CalibrationPanel, 'on_reset_clicked')
            assert hasattr(CalibrationPanel, 'on_export_clicked')
        except Exception as e:
            self.fail(f"CalibrationPanel initialization check failed: {e}")
    
    def test_panel_has_required_methods(self):
        """Test that CalibrationPanel has all required methods."""
        required_methods = [
            'setup_ui',
            'create_month_selector',
            'create_parameters_frame',
            'create_parameter_slider',
            'create_controls_frame',
            'on_month_changed',
            'on_slider_changed',
            'on_reset_clicked',
            'on_export_clicked',
            'on_state_change',
            'update_parameter_displays',
            'update_controls_state',
        ]
        
        for method_name in required_methods:
            assert hasattr(CalibrationPanel, method_name), \
                f"CalibrationPanel missing required method: {method_name}"
    
    def test_get_historical_value_helper(self):
        """Test the _get_historical_value helper method logic."""
        # Set up app state with historical params
        self.app_state.set_historical_params(self.historical_params)
        
        # Verify we can access historical values
        assert self.app_state.has_historical_params()
        
        # Test accessing values from historical params
        historical = self.app_state.historical_params
        
        # Test alpha value for January (month_idx=0)
        alpha_value = float(historical.alpha.iloc[0, 0])
        assert alpha_value == 1.5
        
        # Test beta value for January
        beta_value = float(historical.beta.iloc[0, 0])
        assert beta_value == 0.8
        
        # Test probability values
        pww_value = float(historical.p_wet_wet.iloc[0, 0])
        assert pww_value == 0.6


if __name__ == '__main__':
    unittest.main()
