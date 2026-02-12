#!/usr/bin/env python3
"""
PrecipGen PAR - Interactive Menu Entry Point

This is a convenience wrapper for the interactive menu interface.
"""

import sys
from pathlib import Path

# Add precipgen package to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the interactive menu
from scripts.easy_start import main

if __name__ == "__main__":
    sys.exit(main())
