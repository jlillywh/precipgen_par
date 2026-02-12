#!/bin/bash
echo "Starting PrecipGen Web Interface..."
echo ""
echo "The web interface will open in your browser automatically."
echo "Press Ctrl+C to stop the server."
echo ""
cd "$(dirname "$0")/.."
streamlit run precipgen-web.py
