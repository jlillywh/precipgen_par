"""
Manual test script for verifying folder selection functionality.

This script launches the desktop application to allow manual testing
of the folder selection feature. Run this script and test:
1. Click "Change..." button
2. Select a folder
3. Verify the folder path is displayed
4. Close and reopen the app to verify persistence
"""

import sys
from pathlib import Path

# Add parent directory to path to import precipgen
sys.path.insert(0, str(Path(__file__).parent.parent))

from precipgen.desktop.app import DesktopApp


def main():
    """
    Launch the desktop application for manual testing.
    
    Instructions:
    1. Click the "Change..." button in the project panel
    2. Select a folder from the dialog
    3. Verify the folder path is displayed correctly
    4. Close the application
    5. Run this script again to verify the folder path persists
    """
    print("=" * 60)
    print("Manual Test: Folder Selection")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Click 'Change...' button")
    print("2. Select a folder")
    print("3. Verify folder path displays correctly")
    print("4. Close the app")
    print("5. Run again to test persistence")
    print("\n" + "=" * 60 + "\n")
    
    app = DesktopApp()
    app.run()


if __name__ == '__main__':
    main()
