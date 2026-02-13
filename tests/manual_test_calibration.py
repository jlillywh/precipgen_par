"""
Manual test script for calibration functionality.

This script allows manual testing of the calibration panel with real data.
Run this script to verify that:
1. Sliders respond to user input
2. Parameter values update in real-time
3. Deviations are calculated correctly
4. Reset functionality works
5. Export functionality works
"""

import sys
from pathlib import Path
from datetime import datetime, date
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.calibration_controller import CalibrationController
from precipgen.desktop.controllers.data_controller import HistoricalParameters


def create_test_historical_params():
    """Create realistic test historical parameters."""
    months = range(1, 13)
    
    # Create realistic monthly variations
    alpha_values = [1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1]
    beta_values = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65]
    pww_values = [0.5, 0.52, 0.55, 0.58, 0.6, 0.62, 0.6, 0.58, 0.55, 0.52, 0.5, 0.48]
    pwd_values = [0.25, 0.27, 0.3, 0.32, 0.35, 0.37, 0.35, 0.32, 0.3, 0.27, 0.25, 0.23]
    
    alpha_df = pd.DataFrame({'ALPHA': alpha_values}, index=months)
    beta_df = pd.DataFrame({'BETA': beta_values}, index=months)
    pww_df = pd.DataFrame({'PWW': pww_values}, index=months)
    pwd_df = pd.DataFrame({'PWD': pwd_values}, index=months)
    
    # Calculate complementary probabilities
    pdw_values = [1 - pww for pww in pww_values]
    pdd_values = [1 - pwd for pwd in pwd_values]
    
    pdw_df = pd.DataFrame({'PDW': pdw_values}, index=months)
    pdd_df = pd.DataFrame({'PDD': pdd_values}, index=months)
    
    return HistoricalParameters(
        alpha=alpha_df,
        beta=beta_df,
        p_wet_wet=pww_df,
        p_wet_dry=pwd_df,
        p_dry_wet=pdw_df,
        p_dry_dry=pdd_df,
        calculation_date=datetime.now(),
        source_station="TEST_STATION_12345",
        date_range=(date(2000, 1, 1), date(2020, 12, 31))
    )


def test_calibration_controller():
    """Test the calibration controller functionality."""
    print("=" * 70)
    print("CALIBRATION CONTROLLER TEST")
    print("=" * 70)
    
    # Initialize components
    app_state = AppState()
    controller = CalibrationController(app_state)
    
    # Create and set historical parameters
    historical_params = create_test_historical_params()
    app_state.set_historical_params(historical_params)
    
    print("\n1. Historical Parameters Loaded:")
    print(f"   Alpha (Jan): {historical_params.alpha.iloc[0, 0]:.3f}")
    print(f"   Beta (Jan): {historical_params.beta.iloc[0, 0]:.3f}")
    print(f"   P(W|W) (Jan): {historical_params.p_wet_wet.iloc[0, 0]:.3f}")
    print(f"   P(W|D) (Jan): {historical_params.p_wet_dry.iloc[0, 0]:.3f}")
    
    # Test parameter adjustment
    print("\n2. Testing Parameter Adjustment:")
    result = controller.adjust_parameter('alpha', 1, 2.0)
    if result.success:
        print(f"   ✓ Adjusted alpha for January to 2.0")
        adjusted = app_state.adjusted_params
        deviation = adjusted.deviations['alpha'].iloc[0, 0]
        print(f"   ✓ Deviation calculated: {deviation:.3f}")
        print(f"   ✓ Expected deviation: {2.0 - historical_params.alpha.iloc[0, 0]:.3f}")
    else:
        print(f"   ✗ Failed to adjust parameter: {result.error}")
    
    # Test validation
    print("\n3. Testing Parameter Validation:")
    
    # Valid value
    is_valid, error = controller.validate_parameter('alpha', 1.5)
    print(f"   ✓ Valid alpha (1.5): {is_valid}")
    
    # Invalid value (negative)
    is_valid, error = controller.validate_parameter('alpha', -1.0)
    print(f"   ✓ Invalid alpha (-1.0): {not is_valid} - {error}")
    
    # Invalid probability (> 1)
    is_valid, error = controller.validate_parameter('p_wet_wet', 1.5)
    print(f"   ✓ Invalid probability (1.5): {not is_valid} - {error}")
    
    # Test reset
    print("\n4. Testing Reset to Historical:")
    result = controller.reset_to_historical()
    if result.success:
        print(f"   ✓ Reset successful")
        adjusted = app_state.adjusted_params
        print(f"   ✓ Alpha (Jan) after reset: {adjusted.alpha.iloc[0, 0]:.3f}")
        print(f"   ✓ Matches historical: {abs(adjusted.alpha.iloc[0, 0] - historical_params.alpha.iloc[0, 0]) < 1e-10}")
    else:
        print(f"   ✗ Reset failed: {result.error}")
    
    # Test export (requires project folder)
    print("\n5. Testing Export (without project folder):")
    result = controller.export_parameters()
    if not result.success:
        print(f"   ✓ Correctly rejected export without project folder")
        print(f"   ✓ Error message: {result.error}")
    else:
        print(f"   ✗ Should have failed without project folder")
    
    print("\n" + "=" * 70)
    print("CALIBRATION CONTROLLER TEST COMPLETE")
    print("=" * 70)


def test_slider_simulation():
    """Simulate slider interactions."""
    print("\n" + "=" * 70)
    print("SLIDER INTERACTION SIMULATION")
    print("=" * 70)
    
    app_state = AppState()
    controller = CalibrationController(app_state)
    historical_params = create_test_historical_params()
    app_state.set_historical_params(historical_params)
    
    print("\nSimulating user moving alpha slider for January:")
    print("Historical value: 1.2")
    
    slider_values = [1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0]
    
    for value in slider_values:
        result = controller.adjust_parameter('alpha', 1, value)
        if result.success:
            adjusted = app_state.adjusted_params
            deviation = adjusted.deviations['alpha'].iloc[0, 0]
            print(f"  Slider at {value:.1f} → Deviation: {deviation:+.1f}")
    
    print("\n" + "=" * 70)
    print("SLIDER SIMULATION COMPLETE")
    print("=" * 70)


def main():
    """Run all manual tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "CALIBRATION FUNCTIONALITY TEST" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        test_calibration_controller()
        test_slider_simulation()
        
        print("\n✓ All manual tests completed successfully!")
        print("\nTo test the UI interactively:")
        print("  1. Run: python precipgen/desktop/app.py")
        print("  2. Select a project folder")
        print("  3. Search and download GHCN data")
        print("  4. Navigate to Calibration tab")
        print("  5. Move sliders and verify real-time updates")
        print("  6. Test Reset and Export buttons")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
