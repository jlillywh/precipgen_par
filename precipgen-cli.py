#!/usr/bin/env python3
"""
PrecipGen PAR - Command Line Interface Entry Point

This is a convenience wrapper for the CLI interface.
"""

import sys
from pathlib import Path

# Add precipgen package to path
sys.path.insert(0, str(Path(__file__).parent))

from precipgen.cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
