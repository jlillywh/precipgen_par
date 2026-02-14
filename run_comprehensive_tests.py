#!/usr/bin/env python3
"""
Comprehensive test runner for GUI Architecture Refactor - Task 16
Runs all tests and verifies correctness properties.
"""

import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def main():
    """Run comprehensive test suite."""
    print("="*70)
    print("COMPREHENSIVE TEST SUITE - GUI Architecture Refactor")
    print("Task 16: Final Checkpoint")
    print("="*70)
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    results = {}
    
    # 1. Run all unit tests
    print("\n\n" + "="*70)
    print("PHASE 1: UNIT TESTS")
    print("="*70)
    results['unit_tests'] = run_command(
        ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short', '-k', 'not manual'],
        "Running all unit tests (excluding manual tests)"
    )
    
    # 2. Run property-based tests (if they exist)
    print("\n\n" + "="*70)
    print("PHASE 2: PROPERTY-BASED TESTS")
    print("="*70)
    
    # Check if property tests exist
    property_test_files = list(Path('tests').glob('**/test_*properties*.py'))
    if property_test_files:
        results['property_tests'] = run_command(
            ['python', '-m', 'pytest'] + [str(f) for f in property_test_files] + ['-v'],
            "Running property-based tests"
        )
    else:
        print("No property-based test files found (optional tests)")
        results['property_tests'] = True
    
    # 3. Run integration tests
    print("\n\n" + "="*70)
    print("PHASE 3: INTEGRATION TESTS")
    print("="*70)
    results['integration_tests'] = run_command(
        ['python', '-m', 'pytest', 'tests/test_integration_workflow.py', '-v', '-s'],
        "Running integration workflow tests"
    )
    
    # 4. Run comprehensive final tests
    print("\n\n" + "="*70)
    print("PHASE 4: COMPREHENSIVE FINAL TESTS")
    print("="*70)
    results['comprehensive_tests'] = run_command(
        ['python', '-m', 'pytest', 'tests/test_comprehensive_final.py', '-v'],
        "Running comprehensive final tests"
    )
    
    # 5. Verify file organization
    print("\n\n" + "="*70)
    print("PHASE 5: FILE ORGANIZATION VERIFICATION")
    print("="*70)
    
    print("\nVerifying flat file structure in desktop views...")
    views_path = Path('precipgen/desktop/views')
    if views_path.exists():
        view_files = list(views_path.glob('*.py'))
        print(f"Found {len(view_files)} view files:")
        for f in sorted(view_files):
            print(f"  ✓ {f.name}")
        
        # Check for required panels
        required_panels = [
            'home_panel.py',
            'search_panel.py',
            'upload_panel.py',
            'basic_analysis_panel.py',
            'markov_analysis_panel.py',
            'trend_analysis_panel.py',
            'main_window.py'
        ]
        
        missing_panels = []
        for panel in required_panels:
            if not (views_path / panel).exists():
                missing_panels.append(panel)
        
        if missing_panels:
            print(f"\n⚠ Missing required panels: {', '.join(missing_panels)}")
            results['file_organization'] = False
        else:
            print("\n✓ All required panels present")
            results['file_organization'] = True
    else:
        print("⚠ Views directory not found")
        results['file_organization'] = False
    
    # 6. Verify controllers
    print("\nVerifying controllers...")
    controllers_path = Path('precipgen/desktop/controllers')
    if controllers_path.exists():
        controller_files = list(controllers_path.glob('*.py'))
        print(f"Found {len(controller_files)} controller files:")
        for f in sorted(controller_files):
            print(f"  ✓ {f.name}")
        
        required_controllers = [
            'project_controller.py',
            'data_controller.py',
            'analysis_controller.py'
        ]
        
        missing_controllers = []
        for controller in required_controllers:
            if not (controllers_path / controller).exists():
                missing_controllers.append(controller)
        
        if missing_controllers:
            print(f"\n⚠ Missing required controllers: {', '.join(missing_controllers)}")
        else:
            print("\n✓ All required controllers present")
    
    # Summary
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:30s}: {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED - Implementation verified!")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Review output above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
