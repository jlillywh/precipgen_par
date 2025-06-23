#!/bin/bash
echo "================================================================"
echo "        PrecipGen PAR - Precipitation Parameter Analysis"
echo "================================================================"
echo
echo "This tool helps you analyze precipitation data and generate"
echo "parameters for precipitation modeling."
echo
echo "Make sure you have:"
echo "1. Python 3.8 or newer installed"
echo "2. Downloaded weather data from NOAA Climate Data Online"
echo "   (https://www.ncdc.noaa.gov/cdo-web/)"
echo
echo "First time setup:"
echo "- Run: pip install -r requirements.txt"
echo
read -p "Press Enter to continue..."
echo "Starting PrecipGen PAR..."
echo
python3 easy_start.py
echo
echo "Analysis complete. Check the output files in this folder."
read -p "Press Enter to exit..."
