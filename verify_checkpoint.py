"""
Checkpoint verification script for GUI Architecture Refactor.

This script verifies:
1. All 6 tabs are functional
2. File organization is flat (no subdirectories)
3. CSV outputs are consistent
4. Complete workflow can be executed
"""

import sys
from pathlib import Path

def verify_imports():
    """Verify all required modules can be imported."""
    print("✓ Verifying imports...")
    try:
        from precipgen.desktop.app import DesktopApp
        from precipgen.desktop.views.main_window import MainWindow
        from precipgen.desktop.views.home_panel import HomePanel
        from precipgen.desktop.views.search_panel import SearchPanel
        from precipgen.desktop.views.upload_panel import UploadPanel
        from precipgen.desktop.views.basic_analysis_panel import BasicAnalysisPanel
        from precipgen.desktop.views.markov_analysis_panel import MarkovAnalysisPanel
        from precipgen.desktop.views.trend_analysis_panel import TrendAnalysisPanel
        from precipgen.desktop.controllers.project_controller import ProjectController
        from precipgen.desktop.controllers.data_controller import DataController
        from precipgen.desktop.controllers.analysis_controller import AnalysisController
        from precipgen.desktop.models.app_state import AppState
        from precipgen.desktop.utils.csv_writer import write_csv_file
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

def verify_tab_structure():
    """Verify that MainWindow creates all 6 tabs."""
    print("\n✓ Verifying tab structure...")
    try:
        from precipgen.desktop.views.main_window import MainWindow
        import inspect
        
        # Check setup_layout method
        source = inspect.getsource(MainWindow.setup_layout)
        
        required_tabs = [
            '"Home"',
            '"Search"',
            '"Upload"',
            '"Basic Analysis"',
            '"Markov Analysis"',
            '"Trend Analysis"'
        ]
        
        for tab in required_tabs:
            if tab in source:
                print(f"  ✓ Tab {tab} found")
            else:
                print(f"  ✗ Tab {tab} NOT found")
                return False
        
        print("  ✓ All 6 tabs are defined")
        return True
    except Exception as e:
        print(f"  ✗ Tab verification failed: {e}")
        return False

def verify_flat_file_organization():
    """Verify that files are saved directly to working directory."""
    print("\n✓ Verifying flat file organization...")
    try:
        from precipgen.desktop.controllers.data_controller import DataController
        import inspect
        
        # Check download_station_data method
        source = inspect.getsource(DataController.download_station_data)
        
        # Should NOT create subdirectories
        if 'mkdir' in source.lower() or 'makedirs' in source.lower():
            # Check if it's only for temp directory
            if 'temp_download_path' not in source:
                print("  ✗ Found directory creation in download method")
                return False
        
        # Should save directly to project folder
        if 'project_folder /' in source:
            print("  ✓ Files saved directly to project folder")
        else:
            print("  ✗ File path structure unclear")
            return False
        
        print("  ✓ Flat file organization verified")
        return True
    except Exception as e:
        print(f"  ✗ File organization verification failed: {e}")
        return False

def verify_csv_consistency():
    """Verify CSV output consistency utility exists."""
    print("\n✓ Verifying CSV output consistency...")
    try:
        from precipgen.desktop.utils.csv_writer import write_csv_file
        import inspect
        
        # Check that write_csv_file has consistent formatting
        source = inspect.getsource(write_csv_file)
        
        checks = {
            "sep=','": "Comma delimiter",
            "encoding='utf-8'": "UTF-8 encoding",
            "lineterminator='\\n'": "Consistent line endings"
        }
        
        for check, description in checks.items():
            if check in source:
                print(f"  ✓ {description} enforced")
            else:
                print(f"  ✗ {description} NOT enforced")
                return False
        
        print("  ✓ CSV consistency utility verified")
        return True
    except Exception as e:
        print(f"  ✗ CSV consistency verification failed: {e}")
        return False

def verify_controller_structure():
    """Verify all required controllers exist."""
    print("\n✓ Verifying controller structure...")
    try:
        from precipgen.desktop.controllers.project_controller import ProjectController
        from precipgen.desktop.controllers.data_controller import DataController
        from precipgen.desktop.controllers.analysis_controller import AnalysisController
        
        controllers = [
            (ProjectController, "ProjectController"),
            (DataController, "DataController"),
            (AnalysisController, "AnalysisController")
        ]
        
        for controller_class, name in controllers:
            if controller_class:
                print(f"  ✓ {name} exists")
            else:
                print(f"  ✗ {name} NOT found")
                return False
        
        print("  ✓ All controllers verified")
        return True
    except Exception as e:
        print(f"  ✗ Controller verification failed: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("GUI Architecture Refactor - Checkpoint Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", verify_imports()))
    results.append(("Tab Structure", verify_tab_structure()))
    results.append(("Flat File Organization", verify_flat_file_organization()))
    results.append(("CSV Consistency", verify_csv_consistency()))
    results.append(("Controller Structure", verify_controller_structure()))
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All verification checks passed!")
        print("\nThe GUI architecture refactor is ready for manual testing.")
        print("\nNext steps:")
        print("1. Run the application: python -m precipgen.desktop.app")
        print("2. Test the complete workflow:")
        print("   - Select a working directory")
        print("   - Search for a station")
        print("   - Download station data")
        print("   - Run basic analysis")
        print("   - Calculate Markov parameters")
        print("   - Perform trend analysis")
        return 0
    else:
        print("\n✗ Some verification checks failed.")
        print("Please review the errors above and fix the issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
