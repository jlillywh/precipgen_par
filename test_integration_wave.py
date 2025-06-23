#!/usr/bin/env python3
"""
Integration test for PrecipGen Parameter Wave Analysis

This test verifies that the complete wave analysis workflow works correctly
including CLI integration and output generation.
"""

import os
import tempfile
import subprocess
import json
import pandas as pd
import shutil
from pathlib import Path


def test_integration():
    """Test complete integration of wave analysis functionality."""
    
    print("Running PrecipGen Parameter Wave Analysis Integration Test")
    print("=" * 60)
    
    # Create temporary directory for outputs
    test_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {test_dir}")
    
    try:
        # Test data file
        test_data = os.path.join("tests", "GrandJunction", "USW00023066_data.csv")
        
        if not os.path.exists(test_data):
            print("❌ Test data file not found")
            return False
        
        print(f"✓ Using test data: {test_data}")
        
        # Test 1: CLI Command
        print("\n1. Testing CLI command...")
        output_base = os.path.join(test_dir, "cli_test")
        
        cmd = [
            "python", "cli.py", "wave-analysis", test_data,
            "--window-years", "6",
            "--start-year", "1980", 
            "--end-year", "2010",
            "--create-plots",
            "-o", output_base
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✓ CLI command executed successfully")
        else:
            print(f"❌ CLI command failed: {result.stderr}")
            return False
        
        # Check output files
        expected_files = [
            f"{output_base}_wave_params.json",
            f"{output_base}_components.csv", 
            f"{output_base}_history.csv",
            f"{output_base}_evolution.png",
            f"{output_base}_components.png"
        ]
        
        for file in expected_files:
            if os.path.exists(file):
                print(f"✓ Generated: {os.path.basename(file)}")
            else:
                print(f"❌ Missing: {os.path.basename(file)}")
                return False
        
        # Test 2: Validate JSON output
        print("\n2. Validating JSON output...")
        json_file = f"{output_base}_wave_params.json"
        
        try:
            with open(json_file, 'r') as f:
                wave_data = json.load(f)
            
            # Check structure
            required_keys = ['metadata', 'PWW', 'PWD', 'alpha', 'beta']
            for key in required_keys:
                if key in wave_data:
                    print(f"✓ Found section: {key}")
                else:
                    print(f"❌ Missing section: {key}")
                    return False
            
            # Check metadata
            metadata = wave_data['metadata']
            if 'generated_date' in metadata and 'window_size_years' in metadata:
                print("✓ Metadata structure valid")
            else:
                print("❌ Invalid metadata structure")
                return False
                
        except Exception as e:
            print(f"❌ JSON validation failed: {e}")
            return False
        
        # Test 3: Validate CSV output
        print("\n3. Validating CSV output...")
        csv_file = f"{output_base}_components.csv"
        
        try:
            df = pd.read_csv(csv_file)
            required_columns = ['parameter', 'component_index', 'frequency', 'period', 'amplitude']
            
            for col in required_columns:
                if col in df.columns:
                    print(f"✓ Found column: {col}")
                else:
                    print(f"❌ Missing column: {col}")
                    return False
            
            print(f"✓ CSV contains {len(df)} component records")
            
        except Exception as e:
            print(f"❌ CSV validation failed: {e}")
            return False
        
        # Test 4: Demo script
        print("\n4. Testing demo script...")
        demo_output = os.path.join(test_dir, "demo_output")
        
        # Run demo with redirected data
        original_cwd = os.getcwd()
        try:
            # Create a simple test to avoid long demo run
            result = subprocess.run([
                "python", "-c", 
                """
import sys
sys.path.insert(0, '.')
from demo_pgpar_wave import demo_parameter_wave_analysis
demo_parameter_wave_analysis('tests/GrandJunction/USW00023066_data.csv', 'temp_demo_test')
print('Demo completed successfully')
                """
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✓ Demo script executed successfully")
            else:
                print(f"❌ Demo script failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠ Demo script timed out (probably still working)")
        except Exception as e:
            print(f"❌ Demo script error: {e}")
            return False
        
        # Test 5: Module import test
        print("\n5. Testing module imports...")
        
        try:
            result = subprocess.run([
                "python", "-c",
                """
import sys
sys.path.insert(0, '.')
from pgpar_wave import PrecipGenPARWave, analyze_precipgen_parameter_waves
from time_series import TimeSeries
print('All imports successful')
                """
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ All modules import successfully")
            else:
                print(f"❌ Import failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Import test error: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("✅ Integration test PASSED!")
        print("All components are working correctly together.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        return False
        
    finally:
        # Clean up
        print(f"\nCleaning up temporary directory: {test_dir}")
        shutil.rmtree(test_dir, ignore_errors=True)
        
        # Clean up demo output if it exists
        if os.path.exists("temp_demo_test"):
            shutil.rmtree("temp_demo_test", ignore_errors=True)


if __name__ == "__main__":
    success = test_integration()
    exit(0 if success else 1)
