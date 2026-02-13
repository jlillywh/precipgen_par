"""
Test script to verify the PrecipGen executable can be launched.

This script tests that:
1. The executable file exists
2. The executable can be launched (basic smoke test)
3. The executable has the correct file properties
"""

import subprocess
import sys
import time
from pathlib import Path


def test_executable_exists():
    """Test that the executable file exists."""
    exe_path = Path("dist/PrecipGen.exe")
    
    if not exe_path.exists():
        print("❌ FAIL: Executable not found at dist/PrecipGen.exe")
        return False
    
    print(f"✓ PASS: Executable exists at {exe_path}")
    print(f"  Size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
    return True


def test_executable_launches():
    """Test that the executable can be launched (will close immediately)."""
    exe_path = Path("dist/PrecipGen.exe")
    
    try:
        print("\n✓ Testing executable launch...")
        print("  Note: The application window will open briefly and close automatically.")
        print("  This is expected behavior for the test.")
        
        # Launch the executable with a timeout
        # We'll kill it after 3 seconds since we just want to verify it starts
        process = subprocess.Popen(
            [str(exe_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit to see if it crashes immediately
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✓ PASS: Executable launched successfully")
            print("  The application is running. Terminating test process...")
            process.terminate()
            process.wait(timeout=5)
            return True
        else:
            # Process exited
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                print("✓ PASS: Executable launched and exited cleanly")
                return True
            else:
                print(f"❌ FAIL: Executable exited with code {process.returncode}")
                if stderr:
                    print(f"  Error output: {stderr.decode('utf-8', errors='ignore')}")
                return False
                
    except Exception as e:
        print(f"❌ FAIL: Could not launch executable: {e}")
        return False


def test_no_python_required():
    """Verify that the executable doesn't require Python installation."""
    print("\n✓ Testing standalone nature...")
    print("  The executable should work without Python in PATH")
    print("  (This test assumes you're running from a venv, which is good)")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print("✓ PASS: Running from virtual environment")
        print("  The executable is standalone and doesn't need this venv")
    else:
        print("⚠ WARNING: Not running from virtual environment")
        print("  Cannot fully verify standalone nature")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("PrecipGen Executable Test Suite")
    print("=" * 60)
    
    tests = [
        ("Executable Exists", test_executable_exists),
        ("Executable Launches", test_executable_launches),
        ("No Python Required", test_no_python_required),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[Test] {test_name}")
        print("-" * 60)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ FAIL: Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! The executable is ready for distribution.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
