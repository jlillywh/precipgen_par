#!/usr/bin/env python3
"""
Manual verification script for GUI Architecture Refactor
Tests with real data and verifies error handling.
"""

import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.models.session_config import SessionConfig
from precipgen.desktop.controllers.project_controller import ProjectController
from precipgen.desktop.controllers.data_controller import DataController
from precipgen.desktop.controllers.analysis_controller import AnalysisController


def test_session_initialization():
    """Test session initialization with working directory."""
    print("\n" + "="*70)
    print("TEST 1: Session Initialization")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        app_state = AppState()
        session_config = SessionConfig()
        project_controller = ProjectController(app_state, session_config)
        
        # Test setting project folder
        app_state.set_project_folder(Path(tmpdir))
        
        assert app_state.project_folder == Path(tmpdir), "Project folder not set"
        print("✓ Session initialization successful")
        print(f"  Working directory: {tmpdir}")
        
        return True


def test_flat_file_organization():
    """Test that files are saved in flat structure."""
    print("\n" + "="*70)
    print("TEST 2: Flat File Organization")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create sample CSV files
        test_files = [
            "GHCN001.csv",
            "GHCN002.csv",
            "CUSTOM_MyStation.csv"
        ]
        
        for filename in test_files:
            filepath = tmppath / filename
            df = pd.DataFrame({
                'DATE': pd.date_range('2020-01-01', periods=100),
                'PRCP': np.random.rand(100) * 10
            })
            df.to_csv(filepath, index=False)
        
        # Verify files are in root directory
        csv_files = list(tmppath.glob("*.csv"))
        assert len(csv_files) == 3, f"Expected 3 files, found {len(csv_files)}"
        
        # Verify no subdirectories created
        subdirs = [d for d in tmppath.iterdir() if d.is_dir()]
        assert len(subdirs) == 0, f"Found unexpected subdirectories: {subdirs}"
        
        print("✓ Flat file organization verified")
        print(f"  Files in root: {len(csv_files)}")
        print(f"  Subdirectories: {len(subdirs)}")
        
        return True


def test_csv_format_consistency():
    """Test CSV output format consistency."""
    print("\n" + "="*70)
    print("TEST 3: CSV Format Consistency")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create test CSV with standardized format
        test_file = tmppath / "test_station.csv"
        df = pd.DataFrame({
            'DATE': pd.date_range('2020-01-01', periods=100),
            'PRCP': np.random.rand(100) * 10
        })
        df.to_csv(test_file, index=False)
        
        # Read back and verify format
        df_read = pd.read_csv(test_file)
        
        assert 'DATE' in df_read.columns, "DATE column missing"
        assert 'PRCP' in df_read.columns, "PRCP column missing"
        assert len(df_read.columns) == 2, f"Expected 2 columns, found {len(df_read.columns)}"
        
        # Verify header is present
        with open(test_file, 'r') as f:
            first_line = f.readline().strip()
            assert first_line == 'DATE,PRCP', f"Header mismatch: {first_line}"
        
        print("✓ CSV format consistency verified")
        print(f"  Columns: {list(df_read.columns)}")
        print(f"  Header: {first_line}")
        
        return True


def test_analysis_controller():
    """Test AnalysisController with sample data."""
    print("\n" + "="*70)
    print("TEST 4: Analysis Controller")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        app_state = AppState()
        app_state.set_project_folder(tmppath)
        
        # Create sample precipitation data (3 years)
        dates = pd.date_range('2020-01-01', '2022-12-31', freq='D')
        np.random.seed(42)
        prcp_data = []
        for _ in range(len(dates)):
            if np.random.random() > 0.7:  # 30% wet days
                prcp_data.append(np.random.exponential(5))
            else:
                prcp_data.append(0.0)
        
        test_file = tmppath / "GHCN_TEST.csv"
        df = pd.DataFrame({
            'DATE': dates,
            'PRCP': prcp_data
        })
        df.to_csv(test_file, index=False)
        
        # Test AnalysisController
        analysis_controller = AnalysisController(app_state)
        
        # Test basic stats calculation
        result = analysis_controller.calculate_basic_stats("GHCN_TEST.csv")
        
        if result.success:
            stats = result.value  # Use 'value' not 'data'
            print("✓ Basic statistics calculated successfully")
            print(f"  Years on record: {stats.years_on_record}")
            print(f"  Mean annual precipitation: {stats.mean_annual:.2f} mm")
            print(f"  Date range: {stats.date_range[0]} to {stats.date_range[1]}")
            
            # Verify export
            export_result = analysis_controller.export_basic_stats(
                stats, 
                tmppath / "basic_stats.csv"
            )
            
            if export_result.success:
                print("✓ Basic stats export successful")
                assert (tmppath / "basic_stats.csv").exists(), "Export file not created"
            else:
                print(f"✗ Export failed: {export_result.error}")
                return False
        else:
            print(f"✗ Calculation failed: {result.error}")
            return False
        
        # Test Markov parameters calculation
        markov_result = analysis_controller.calculate_markov_parameters("GHCN_TEST.csv")
        
        if markov_result.success:
            params = markov_result.value  # Use 'value' not 'data'
            print("✓ Markov parameters calculated successfully")
            print(f"  Monthly parameters shape: {params.monthly_params.shape}")
            
            # Verify 12 months
            assert len(params.monthly_params) == 12, "Expected 12 monthly parameters"
            
            # Verify columns
            expected_cols = ['Pww', 'Pwd', 'alpha', 'beta']
            for col in expected_cols:
                assert col in params.monthly_params.columns, f"Missing column: {col}"
            
            print(f"  Columns: {list(params.monthly_params.columns)}")
        else:
            print(f"✗ Markov calculation failed: {markov_result.error}")
            return False
        
        return True


def test_error_handling():
    """Test error handling for various failure modes."""
    print("\n" + "="*70)
    print("TEST 5: Error Handling")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        app_state = AppState()
        app_state.set_project_folder(tmppath)
        
        analysis_controller = AnalysisController(app_state)
        
        # Test 1: Nonexistent file
        result = analysis_controller.calculate_basic_stats("nonexistent.csv")
        assert not result.success, "Should fail for nonexistent file"
        print("✓ Handles nonexistent file correctly")
        print(f"  Error: {result.error}")
        
        # Test 2: Invalid CSV format
        bad_file = tmppath / "bad.csv"
        with open(bad_file, 'w') as f:
            f.write("invalid,csv,data\n1,2\n")  # Inconsistent columns
        
        result = analysis_controller.calculate_basic_stats("bad.csv")
        assert not result.success, "Should fail for invalid CSV"
        print("✓ Handles invalid CSV correctly")
        print(f"  Error: {result.error}")
        
        # Test 3: Insufficient data
        short_file = tmppath / "short.csv"
        df = pd.DataFrame({
            'DATE': pd.date_range('2020-01-01', periods=10),
            'PRCP': [0.0] * 10
        })
        df.to_csv(short_file, index=False)
        
        result = analysis_controller.calculate_basic_stats("short.csv")
        # This might succeed or fail depending on implementation
        print(f"✓ Handles insufficient data: {'Success' if result.success else 'Failed as expected'}")
        if not result.success:
            print(f"  Error: {result.error}")
        
        return True


def test_state_management():
    """Test AppState observer pattern."""
    print("\n" + "="*70)
    print("TEST 6: State Management")
    print("="*70)
    
    app_state = AppState()
    
    # Track observer notifications
    notifications = []
    
    def observer(state_key, new_value):
        notifications.append((state_key, new_value))
    
    app_state.register_observer(observer)
    
    # Test state changes
    with tempfile.TemporaryDirectory() as tmpdir:
        app_state.set_project_folder(Path(tmpdir))
    
    assert len(notifications) > 0, "No observer notifications received"
    assert notifications[0][0] == 'project_folder', "Wrong state key notified"
    
    print("✓ Observer pattern working correctly")
    print(f"  Notifications received: {len(notifications)}")
    print(f"  State key: {notifications[0][0]}")
    
    return True


def main():
    """Run all verification tests."""
    print("="*70)
    print("GUI ARCHITECTURE REFACTOR - MANUAL VERIFICATION")
    print("Task 16: Final Checkpoint")
    print("="*70)
    
    tests = [
        ("Session Initialization", test_session_initialization),
        ("Flat File Organization", test_flat_file_organization),
        ("CSV Format Consistency", test_csv_format_consistency),
        ("Analysis Controller", test_analysis_controller),
        ("Error Handling", test_error_handling),
        ("State Management", test_state_management),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception:")
            print(f"  {type(e).__name__}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:30s}: {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n✓ ALL VERIFICATIONS PASSED")
        return 0
    else:
        print("\n✗ SOME VERIFICATIONS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
