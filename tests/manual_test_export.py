"""
Manual test for parameter export functionality.

This script demonstrates the export_parameters() functionality by:
1. Creating a test project folder
2. Setting up historical parameters
3. Exporting parameters to CSV
4. Verifying the exported files
"""

import tempfile
from pathlib import Path
from datetime import datetime, date
import pandas as pd

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.calibration_controller import CalibrationController
from precipgen.desktop.controllers.data_controller import HistoricalParameters


def create_test_historical_params():
    """Create sample historical parameters for testing."""
    # Create sample monthly parameter values
    months = list(range(1, 13))
    
    alpha_df = pd.DataFrame({'value': [1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3]})
    beta_df = pd.DataFrame({'value': [0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35]})
    pww_df = pd.DataFrame({'value': [0.6, 0.62, 0.64, 0.66, 0.68, 0.7, 0.72, 0.74, 0.76, 0.78, 0.8, 0.82]})
    pwd_df = pd.DataFrame({'value': [0.3, 0.32, 0.34, 0.36, 0.38, 0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52]})
    pdw_df = pd.DataFrame({'value': [0.4, 0.38, 0.36, 0.34, 0.32, 0.3, 0.28, 0.26, 0.24, 0.22, 0.2, 0.18]})
    pdd_df = pd.DataFrame({'value': [0.7, 0.68, 0.66, 0.64, 0.62, 0.6, 0.58, 0.56, 0.54, 0.52, 0.5, 0.48]})
    
    return HistoricalParameters(
        alpha=alpha_df,
        beta=beta_df,
        p_wet_wet=pww_df,
        p_wet_dry=pwd_df,
        p_dry_wet=pdw_df,
        p_dry_dry=pdd_df,
        calculation_date=datetime.now(),
        source_station="TEST_STATION_001",
        date_range=(date(2000, 1, 1), date(2020, 12, 31))
    )


def main():
    """Run manual export test."""
    print("=" * 60)
    print("Manual Test: Parameter Export Functionality")
    print("=" * 60)
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        project_folder = Path(tmpdir)
        print(f"\n1. Created test project folder: {project_folder}")
        
        # Initialize app state and controller
        app_state = AppState()
        app_state.set_project_folder(project_folder)
        controller = CalibrationController(app_state)
        
        # Create and set historical parameters
        historical_params = create_test_historical_params()
        app_state.set_historical_params(historical_params)
        print(f"2. Set historical parameters for station: {historical_params.source_station}")
        
        # Test 1: Export historical parameters
        print("\n" + "-" * 60)
        print("Test 1: Export Historical Parameters")
        print("-" * 60)
        result = controller.export_parameters()
        
        if result.success:
            print(f"✓ Export successful!")
            print(f"  Output file: {result.value}")
            print(f"  File exists: {result.value.exists()}")
            
            # Verify metadata file
            metadata_file = result.value.with_suffix('.txt')
            print(f"  Metadata file: {metadata_file}")
            print(f"  Metadata exists: {metadata_file.exists()}")
            
            # Read and display CSV content
            print("\n  CSV Content (first 3 months):")
            df = pd.read_csv(result.value, index_col=0)
            print(df.head(3).to_string())
            
            # Read and display metadata
            print("\n  Metadata Content:")
            with open(metadata_file, 'r') as f:
                print("  " + "\n  ".join(f.read().split('\n')))
        else:
            print(f"✗ Export failed: {result.error}")
        
        # Test 2: Adjust parameters and export
        print("\n" + "-" * 60)
        print("Test 2: Export Adjusted Parameters")
        print("-" * 60)
        
        # Adjust some parameters
        controller.adjust_parameter('alpha', 1, 2.5)
        controller.adjust_parameter('beta', 6, 1.8)
        print("  Adjusted alpha (month 1) to 2.5")
        print("  Adjusted beta (month 6) to 1.8")
        
        result2 = controller.export_parameters()
        
        if result2.success:
            print(f"✓ Export successful!")
            print(f"  Output file: {result2.value}")
            
            # Read and verify adjusted values
            print("\n  CSV Content (showing adjusted values):")
            df2 = pd.read_csv(result2.value, index_col=0)
            print(f"  Month 1 - ALPHA: {df2.loc[1, 'ALPHA']} (should be 2.5)")
            print(f"  Month 6 - BETA: {df2.loc[6, 'BETA']} (should be 1.8)")
            
            # Check metadata indicates adjusted parameters
            metadata_file2 = result2.value.with_suffix('.txt')
            with open(metadata_file2, 'r') as f:
                metadata_content = f.read()
                if "User-Adjusted" in metadata_content:
                    print("  ✓ Metadata correctly indicates adjusted parameters")
                else:
                    print("  ✗ Metadata does not indicate adjusted parameters")
        else:
            print(f"✗ Export failed: {result2.error}")
        
        print("\n" + "=" * 60)
        print("Manual test complete!")
        print("=" * 60)


if __name__ == '__main__':
    main()
