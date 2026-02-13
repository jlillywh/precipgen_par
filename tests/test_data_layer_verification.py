"""
Verification script for Data Layer checkpoint.

This script verifies that GHCN search and download functionality works correctly.
It performs a real search and simulates a download to ensure the integration is working.
"""

import tempfile
from pathlib import Path

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.data_controller import DataController, SearchCriteria


def test_ghcn_search():
    """Test GHCN station search functionality."""
    print("\n=== Testing GHCN Station Search ===")
    
    # Initialize components
    app_state = AppState()
    data_controller = DataController(app_state)
    
    # Create search criteria for Grand Junction, CO area
    criteria = SearchCriteria(
        latitude=39.05,
        longitude=-108.55,
        radius_km=50.0,
        start_year=1980,
        end_year=2020
    )
    
    print(f"Searching for stations near Grand Junction, CO...")
    print(f"  Latitude: {criteria.latitude}")
    print(f"  Longitude: {criteria.longitude}")
    print(f"  Radius: {criteria.radius_km} km")
    print(f"  Date range: {criteria.start_year} - {criteria.end_year}")
    
    # Perform search
    result = data_controller.search_stations(criteria)
    
    if not result.success:
        print(f"❌ Search failed: {result.error}")
        return False
    
    stations = result.value
    print(f"✓ Search successful! Found {len(stations)} station(s)")
    
    if len(stations) > 0:
        print("\nFirst 3 stations:")
        for i, station in enumerate(stations[:3]):
            print(f"\n  Station {i+1}:")
            print(f"    ID: {station.station_id}")
            print(f"    Name: {station.name}")
            print(f"    Location: {station.latitude:.4f}°, {station.longitude:.4f}°")
            print(f"    Data: {station.start_date} - {station.end_date}")
    
    return True


def test_ghcn_download_simulation():
    """Test GHCN download functionality with a known station."""
    print("\n\n=== Testing GHCN Data Download ===")
    
    # Initialize components
    app_state = AppState()
    data_controller = DataController(app_state)
    
    # Set up a temporary project folder
    with tempfile.TemporaryDirectory() as tmpdir:
        project_folder = Path(tmpdir) / "test_project"
        project_folder.mkdir()
        
        app_state.set_project_folder(project_folder)
        print(f"Project folder: {project_folder}")
        
        # Use a known station (Grand Junction, CO)
        from precipgen.desktop.controllers.data_controller import StationMetadata
        
        test_station = StationMetadata(
            station_id="USW00023066",  # Grand Junction Regional Airport
            name="Grand Junction Regional Airport",
            latitude=39.1225,
            longitude=-108.5267,
            elevation=1475.0,
            start_date=1948,
            end_date=2024,
            data_coverage=95.0
        )
        
        print(f"\nAttempting to download data for: {test_station.station_id}")
        print(f"  Name: {test_station.name}")
        print(f"  Location: {test_station.latitude:.4f}°, {test_station.longitude:.4f}°")
        
        # Progress callback
        def progress_callback(percent, message):
            print(f"  Progress: {percent}% - {message}")
        
        # Perform download
        result = data_controller.download_station_data(test_station, progress_callback)
        
        if not result.success:
            print(f"❌ Download failed: {result.error}")
            return False
        
        print(f"✓ Download successful!")
        
        # Verify file was created in project folder
        data_dir = project_folder / 'data'
        expected_file = data_dir / f"{test_station.station_id}_data.csv"
        
        if expected_file.exists():
            print(f"✓ Data file created: {expected_file}")
            
            # Check file size
            file_size = expected_file.stat().st_size
            print(f"  File size: {file_size:,} bytes")
            
            # Verify data was loaded into app state
            if app_state.precipitation_data is not None:
                print(f"✓ Data loaded into app state")
                print(f"  Rows: {len(app_state.precipitation_data)}")
                print(f"  Columns: {list(app_state.precipitation_data.columns)}")
            else:
                print(f"❌ Data not loaded into app state")
                return False
        else:
            print(f"❌ Data file not created at expected location")
            return False
        
        # Verify no temp files remain
        temp_files = list(data_controller.temp_download_path.glob("*"))
        if len(temp_files) == 0:
            print(f"✓ No temporary files remaining")
        else:
            print(f"⚠ Warning: {len(temp_files)} temporary file(s) found")
    
    return True


def test_parameter_calculation():
    """Test historical parameter calculation functionality."""
    print("\n\n=== Testing Historical Parameter Calculation ===")
    
    # Initialize components
    app_state = AppState()
    data_controller = DataController(app_state)
    
    # Set up a temporary project folder
    with tempfile.TemporaryDirectory() as tmpdir:
        project_folder = Path(tmpdir) / "test_project"
        project_folder.mkdir()
        
        app_state.set_project_folder(project_folder)
        print(f"Project folder: {project_folder}")
        
        # Use a known station (Grand Junction, CO)
        from precipgen.desktop.controllers.data_controller import StationMetadata
        
        test_station = StationMetadata(
            station_id="USW00023066",  # Grand Junction Regional Airport
            name="Grand Junction Regional Airport",
            latitude=39.1225,
            longitude=-108.5267,
            elevation=1475.0,
            start_date=1948,
            end_date=2024,
            data_coverage=95.0
        )
        
        print(f"\nDownloading data for: {test_station.station_id}")
        
        # Download data first
        result = data_controller.download_station_data(test_station)
        
        if not result.success:
            print(f"❌ Download failed: {result.error}")
            return False
        
        print(f"✓ Data downloaded successfully")
        
        # Calculate historical parameters
        print(f"\nCalculating historical parameters...")
        
        calc_result = data_controller.calculate_historical_parameters(result.value)
        
        if not calc_result.success:
            print(f"❌ Parameter calculation failed: {calc_result.error}")
            return False
        
        print(f"✓ Parameters calculated successfully!")
        
        # Verify parameters were stored in app state
        if app_state.historical_params is None:
            print(f"❌ Parameters not stored in app state")
            return False
        
        print(f"✓ Parameters stored in app state")
        
        # Verify parameter structure
        params = app_state.historical_params
        
        print(f"\nParameter details:")
        print(f"  Source station: {params.source_station}")
        print(f"  Calculation date: {params.calculation_date}")
        print(f"  Data range: {params.date_range[0]} to {params.date_range[1]}")
        
        # Check that all parameters have 12 monthly values
        param_names = ['alpha', 'beta', 'p_wet_wet', 'p_wet_dry', 'p_dry_wet', 'p_dry_dry']
        all_valid = True
        
        for param_name in param_names:
            param_df = getattr(params, param_name)
            if len(param_df) != 12:
                print(f"❌ {param_name} has {len(param_df)} values, expected 12")
                all_valid = False
            else:
                # Get the column name (first column)
                col_name = param_df.columns[0]
                values = param_df[col_name].values
                print(f"  {param_name}: min={values.min():.4f}, max={values.max():.4f}, mean={values.mean():.4f}")
        
        if not all_valid:
            return False
        
        print(f"✓ All parameters have 12 monthly values")
        
        # Verify parameters were saved to project folder
        params_dir = project_folder / 'parameters'
        expected_file = params_dir / f"{test_station.station_id}_historical_params.csv"
        metadata_file = params_dir / f"{test_station.station_id}_metadata.txt"
        
        if expected_file.exists():
            print(f"✓ Parameters saved to: {expected_file}")
        else:
            print(f"❌ Parameters file not created")
            return False
        
        if metadata_file.exists():
            print(f"✓ Metadata saved to: {metadata_file}")
        else:
            print(f"❌ Metadata file not created")
            return False
        
        # Verify parameter ranges (Requirements 4.3)
        print(f"\nValidating parameter ranges...")
        
        alpha_values = params.alpha[params.alpha.columns[0]].values
        beta_values = params.beta[params.beta.columns[0]].values
        pww_values = params.p_wet_wet[params.p_wet_wet.columns[0]].values
        pwd_values = params.p_wet_dry[params.p_wet_dry.columns[0]].values
        
        range_valid = True
        
        if (alpha_values <= 0).any():
            print(f"❌ Some alpha values are <= 0")
            range_valid = False
        
        if (beta_values <= 0).any():
            print(f"❌ Some beta values are <= 0")
            range_valid = False
        
        if (pww_values < 0).any() or (pww_values > 1).any():
            print(f"❌ Some P(W|W) values are outside [0,1]")
            range_valid = False
        
        if (pwd_values < 0).any() or (pwd_values > 1).any():
            print(f"❌ Some P(W|D) values are outside [0,1]")
            range_valid = False
        
        if range_valid:
            print(f"✓ All parameters within valid ranges")
        else:
            return False
    
    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Data Layer Verification")
    print("=" * 60)
    
    results = []
    
    # Test 1: GHCN Search
    try:
        results.append(("GHCN Search", test_ghcn_search()))
    except Exception as e:
        print(f"❌ GHCN Search test failed with exception: {e}")
        results.append(("GHCN Search", False))
    
    # Test 2: GHCN Download
    try:
        results.append(("GHCN Download", test_ghcn_download_simulation()))
    except Exception as e:
        print(f"❌ GHCN Download test failed with exception: {e}")
        results.append(("GHCN Download", False))
    
    # Test 3: Parameter Calculation
    try:
        results.append(("Parameter Calculation", test_parameter_calculation()))
    except Exception as e:
        print(f"❌ Parameter Calculation test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Parameter Calculation", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ All verification tests passed!")
        print("\nData Layer is complete and ready for use.")
    else:
        print("\n❌ Some verification tests failed.")
        print("\nPlease review the errors above.")
    
    return all_passed


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
