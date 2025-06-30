#!/usr/bin/env python3
"""
Comprehensive test for main PrecipGen PAR functionality.
Tests the key features before GitHub deployment.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_imports():
    """Test that all main modules import correctly."""
    print("🔍 Testing imports...")
    
    try:
        import easy_start
        print("  ✅ easy_start.py imports successfully")
    except Exception as e:
        print(f"  ❌ easy_start.py import failed: {e}")
        return False
    
    try:
        import cli
        print("  ✅ cli.py imports successfully") 
    except Exception as e:
        print(f"  ❌ cli.py import failed: {e}")
        return False
    
    try:
        import pgpar
        print("  ✅ pgpar.py imports successfully")
    except Exception as e:
        print(f"  ❌ pgpar.py import failed: {e}")
        return False
    
    return True

def test_city_search():
    """Test city search functionality."""
    print("\n🔍 Testing city search...")
    
    try:
        from easy_start import search_cities
        
        # Test denver search
        denver_results = search_cities('denver')
        if denver_results and len(denver_results) >= 1:
            print(f"  ✅ Denver search: found {len(denver_results)} results")
            print(f"    First result: {denver_results[0][3]}")
        else:
            print("  ❌ Denver search failed")
            return False
        
        # Test los angeles search
        la_results = search_cities('los angeles')
        if la_results and len(la_results) >= 1:
            print(f"  ✅ Los Angeles search: found {len(la_results)} results")
            print(f"    First result: {la_results[0][3]}")
        else:
            print("  ❌ Los Angeles search failed")
            return False
        
        # Test partial match
        seattle_results = search_cities('seat')
        if seattle_results and any('Seattle' in r[3] for r in seattle_results):
            print(f"  ✅ Partial search: found Seattle in {len(seattle_results)} results")
        else:
            print("  ❌ Partial search failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ City search test failed: {e}")
        return False

def test_project_aware_output():
    """Test project-aware output path functionality."""
    print("\n🔍 Testing project-aware output...")
    
    try:
        from easy_start import get_project_aware_output_path
        
        # Test project directory input
        result1 = get_project_aware_output_path('denver_precipgen/data.csv', 'output.csv')
        if 'denver_precipgen' in result1 and 'output.csv' in result1:
            print(f"  ✅ Project directory test: {os.path.basename(result1)}")
        else:
            print(f"  ❌ Project directory test failed: {result1}")
            return False
        
        # Test non-project input
        result2 = get_project_aware_output_path('regular_data.csv', 'output.csv')
        if 'output.csv' in result2:
            print(f"  ✅ Non-project directory test: {os.path.basename(result2)}")
        else:
            print(f"  ❌ Non-project directory test failed: {result2}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Project-aware output test failed: {e}")
        return False

def test_config_functions():
    """Test configuration functions."""
    print("\n🔍 Testing configuration...")
    
    try:
        from easy_start import load_config, save_config
        
        # Test loading config
        config = load_config()
        print(f"  ✅ Config loaded: {type(config).__name__}")
        
        # Test that we can access output directory function
        from easy_start import get_output_directory
        output_dir = get_output_directory()
        print(f"  ✅ Output directory: {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_dependencies():
    """Test that key dependencies are available."""
    print("\n🔍 Testing dependencies...")
    
    dependencies = [
        ('pandas', 'Data manipulation'),
        ('numpy', 'Numerical computing'),
        ('requests', 'HTTP requests'),
        ('matplotlib', 'Plotting'),
        ('scipy', 'Scientific computing')
    ]
    
    all_good = True
    for dep, desc in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}: {desc}")
        except ImportError:
            print(f"  ❌ {dep}: {desc} - MISSING")
            all_good = False
    
    return all_good

def main():
    """Run all tests."""
    print("🧪 PrecipGen PAR Comprehensive Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("City Search", test_city_search), 
        ("Project-Aware Output", test_project_aware_output),
        ("Configuration", test_config_functions),
        ("Dependencies", test_dependencies)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Ready for GitHub!")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed - Review before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
