#!/usr/bin/env python3
"""
Streamlit Cloud entry point for PrecipGen PAR
"""

import sys
from pathlib import Path

# Add precipgen package to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the streamlit app
import precipgen.web.streamlit_app
