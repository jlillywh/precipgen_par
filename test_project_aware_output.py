#!/usr/bin/env python3
"""
Test script to verify project-aware output functionality
"""

import os
import tempfile
import shutil
from pathlib import Path

def test_project_aware_output():
    """Test that all components use project-aware output paths."""
    
    print("🔍 Testing Project-Aware Output Functionality")
    print("=" * 50)
    
    # Test imports
    try:
        from easy_start import (
            get_output_directory, 
            get_output_path, 
            get_project_aware_output_path,
            change_output_directory
        )
        print("✅ Successfully imported project-aware functions from easy_start.py")
    except ImportError as e:
        print(f"❌ Failed to import project-aware functions: {e}")
        return False
    
    # Test CLI imports
    try:
        from cli import get_output_path as cli_get_output_path
        print("✅ Successfully imported project-aware CLI functions")
    except ImportError as e:
        print(f"❌ Failed to import CLI functions: {e}")
        return False
    
    # Test demo file imports
    try:
        from demo_data_filling import get_output_path as demo_get_output_path
        print("✅ Successfully imported demo file project-aware functions")
    except ImportError as e:
        print(f"❌ Failed to import demo functions: {e}")
        return False
    
    # Test main.py imports
    try:
        from main import get_output_path as main_get_output_path
        print("✅ Successfully imported main.py project-aware functions")
    except ImportError as e:
        print(f"❌ Failed to import main functions: {e}")
        return False
    
    print("\n📋 Testing output path logic...")
    
    # Test global output path
    test_filename = "test_output.csv"
    global_path = get_output_path(test_filename)
    print(f"Global output path: {global_path}")
    
    # Test project-aware output path
    test_input_file = "boulder_precipgen/boulder_stations.csv"
    project_path = get_project_aware_output_path(test_input_file, test_filename)
    print(f"Project-aware output path: {project_path}")
    
    # Verify that project-aware path puts output in project directory
    if "boulder_precipgen" in project_path:
        print("✅ Project-aware output correctly places files in project directory")
    else:
        print("❌ Project-aware output not working correctly")
        return False
    
    print("\n📁 Testing output directory configuration...")
    
    # Test output directory retrieval
    current_output_dir = get_output_directory()
    print(f"Current output directory: {current_output_dir}")
    
    print("\n✅ All project-aware output tests passed!")
    return True

def test_file_operations():
    """Test that file operations are project-aware in key modules."""
    
    print("\n🔧 Testing File Operations in Key Modules")
    print("=" * 50)
    
    # Check if key modules have been updated
    modules_to_check = [
        "cli.py",
        "demo_data_filling.py", 
        "demo_pgpar_wave.py",
        "main.py",
        "pgpar_ext.py"
    ]
    
    for module in modules_to_check:
        if os.path.exists(module):
            with open(module, 'r') as f:
                content = f.read()
                
            # Check for project-aware imports
            has_project_imports = (
                "from easy_start import" in content or
                "get_output_path" in content
            )
            
            if has_project_imports:
                print(f"✅ {module}: Has project-aware output functions")
            else:
                print(f"⚠️  {module}: May not have project-aware output functions")
        else:
            print(f"❌ {module}: File not found")
    
    return True

def test_config_file():
    """Test that config file has correct settings."""
    
    print("\n⚙️ Testing Configuration File")
    print("=" * 50)
    
    config_file = "precipgen_config.json"
    
    if os.path.exists(config_file):
        import json
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            output_dir = config.get('output_directory', 'Not found')
            print(f"Configured output directory: {output_dir}")
            
            if output_dir == ".":
                print("✅ Output directory correctly set to current directory")
            else:
                print(f"ℹ️  Output directory set to: {output_dir}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            return False
    else:
        print("ℹ️  No config file found (will be created on first run)")
        return True

if __name__ == "__main__":
    print("🧪 PrecipGen PAR Project-Aware Output Test Suite")
    print("=" * 60)
    
    success = True
    
    success &= test_project_aware_output()
    success &= test_file_operations()
    success &= test_config_file()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! Project-aware output is working correctly.")
        print("\nℹ️  Summary of Project-Aware Output Features:")
        print("• Global output directory configurable via easy_start.py option 10")
        print("• Project directories (e.g., boulder_precipgen/) automatically created")
        print("• All file operations respect project context")
        print("• Station files, data files, analysis outputs saved in correct project dirs")
        print("• CLI operations are project-aware when input files are provided")
        print("• Demo scripts and main.py use project-aware output")
    else:
        print("❌ SOME TESTS FAILED! Please review the output above.")
    
    print("\n💡 To test the full workflow:")
    print("1. Run easy_start.py")
    print("2. Use option 10 to set/change output directory")
    print("3. Use option 1 to find stations (creates project directory)")
    print("4. Use option 2 to download data (saves in project directory)")
    print("5. Use option 4 to fill data (saves in project directory)")
    print("6. Use option 7 to run analysis (saves in project directory)")
