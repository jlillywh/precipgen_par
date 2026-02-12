#!/usr/bin/env python3
"""
PrecipGen PAR - Web Interface Entry Point

This script launches the Streamlit web interface.
Run with: streamlit run precipgen-web.py
"""

import sys
from pathlib import Path

# Add precipgen package to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the streamlit app
import precipgen.web.streamlit_app
