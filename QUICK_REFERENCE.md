# PrecipGen CLI - Quick Reference

## Command Syntax

Use either:
- `python cli.py <command>` (cross-platform)
- `precipgen.bat <command>` (Windows shortcut)
- `./precipgen.ps1 <command>` (PowerShell)

## Two-Stage Workflow for Station Analysis

### Stage 1: Station Discovery
```bash
# Find stations within radius of coordinates (lat, lon, radius_km)
python cli.py find-stations-radius 39.7392 -104.9903 50 --download -o stations.csv

# Find stations by climate zone  
python cli.py find-stations temperate --download -o temperate_stations.csv
```

### Stage 2: Batch Quality Assessment
```bash
# Evaluate multiple stations and get wellness summary
python cli.py batch-gap-analysis stations.csv -o wellness_summary.csv

# With time period filtering
python cli.py batch-gap-analysis stations.csv \
  --start-year 2000 --end-year 2023 \
  -o wellness_summary.csv
```

## Individual Station Analysis Commands
```bash
# Dataset information
python cli.py info data.csv

# Single station gap analysis (RECOMMENDED FIRST STEP)
python cli.py gap-analysis data.csv --gap-threshold 14 -o gap_results

# Fill missing data (use before parameter calculation)
python cli.py fill-data data.csv -o filled_data.csv

# Calculate monthly parameters  
python cli.py params data.csv -o params.csv

# Window statistics (volatility & reversion)
python cli.py window data.csv --window-years 3 -o window.csv

# Extended parameter analysis  
python cli.py ext-params data.csv --window-years 3 -o ext_params

# Wave analysis of parameter evolution
python cli.py wave-analysis data.csv --window-years 10 --create-plots -o wave_results

# Run tests
python cli.py test
```

## Station Discovery & Download Commands
```bash
# List climate zones
python cli.py list-zones

# Get station information
python cli.py station-info USW00023066

# Download station data
python cli.py download-station USW00023066 -o station_data.csv
```

## Common Options
- `-o, --output`: Output file path
- `--start-year`, `--end-year`: Date range filtering  
- `--window-years`: Years per analysis window (default: 3)
- `--gap-threshold`: Threshold for short vs long gaps in days (default: 7)
- `--download`: Auto-download GHCN inventory
- `--column`: Column to analyze (default: PRCP)
- `-h, --help`: Command help

## Workflow Examples

### New Station Analysis
1. `python cli.py find-stations temperate -o stations.csv`
2. `python cli.py download-station USC00118740 -o chicago.csv`
3. `python cli.py gap-analysis chicago.csv --gap-threshold 14`
4. `python cli.py fill-data chicago.csv -o chicago_filled.csv` (if needed)
5. `python cli.py params chicago_filled.csv -o chicago_params.csv`

### Existing Data Analysis
1. `python cli.py info my_data.csv`
2. `python cli.py gap-analysis my_data.csv --start-year 1950 --end-year 2020`
3. `python cli.py fill-data my_data.csv -o my_data_filled.csv` (if needed)
4. `python cli.py params my_data_filled.csv --start-year 1950 --end-year 2020`
5. `python cli.py window my_data_filled.csv --window-years 5`

## Complete Workflow Example
```bash
# Step 1: Find stations near Denver within 50km
python cli.py find-stations-radius 39.7392 -104.9903 50 --download -o denver_stations.csv

# Step 2: Evaluate data quality for 2000-2023 period
python cli.py batch-gap-analysis denver_stations.csv \
  --start-year 2000 --end-year 2023 \
  -o denver_wellness.csv

# Step 3: Download and analyze the best station from results
python cli.py download-station USW00023062 -o denver_data.csv
python cli.py gap-analysis denver_data.csv --start-year 2000 --end-year 2023
python cli.py fill-data denver_data.csv -o denver_filled.csv
python cli.py params denver_filled.csv --start-year 2000 --end-year 2023 -o denver_params.csv
```

## Data Quality Ratings
- **EXCELLENT (≥95%)**: Ready for parameter calculation
- **GOOD (≥90%)**: Generally suitable
- **FAIR (≥80%)**: Use with caution
- **POOR (<80%)**: Gap filling recommended

## Data Filling Options
```bash
# Basic data filling
python cli.py fill-data input.csv -o filled.csv

# Advanced options
python cli.py fill-data input.csv -o filled.csv \
  --max-gap-days 30 \
  --min-similarity 0.7 \
  --seasonal-window 15 \
  --min-years-climatology 10
```

Note: Data filling uses deterministic methods that may affect precipitation statistics for stochastic modeling.
