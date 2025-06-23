# PrecipGen CLI - Quick Reference

## Two-Stage Workflow for Station Analysis

### Stage 1: Station Discovery
```bash
# Find stations within radius of coordinates (lat, lon, radius_km)
precipgen.bat find-stations-radius 39.7392 -104.9903 50 --download -o stations.csv

# Find stations by climate zone  
precipgen.bat find-stations temperate --download -o temperate_stations.csv
```

### Stage 2: Batch Quality Assessment
```bash
# Evaluate multiple stations and get wellness summary
precipgen.bat batch-gap-analysis stations.csv -o wellness_summary.csv

# With time period filtering
precipgen.bat batch-gap-analysis stations.csv \
  --start-year 2000 --end-year 2023 \
  -o wellness_summary.csv
```

## Individual Station Analysis Commands
```bash
# Dataset information
precipgen.bat info data.csv

# Single station gap analysis (RECOMMENDED FIRST STEP)
precipgen.bat gap-analysis data.csv --gap-threshold 14 -o gap_results

# Calculate monthly parameters  
precipgen.bat params data.csv -o params.csv

# Window statistics (volatility & reversion)
precipgen.bat window data.csv --window-years 3 -o window.csv

# Extended parameter analysis  
precipgen.bat ext-params data.csv --window-years 3 -o ext_params

# Run tests
precipgen.bat test
```

## Station Discovery & Download Commands
```bash
# List climate zones
precipgen.bat list-zones

# Get station information
precipgen.bat station-info USW00023066

# Download station data
precipgen.bat download-station USW00023066 -o station_data.csv
```

## Common Options
- `-o, --output`: Output file path (files saved to `tests/` directory if just filename given)
- `--start-year`, `--end-year`: Date range filtering  
- `--window-years`: Years per analysis window
- `--download`: Auto-download GHCN inventory
- `-h, --help`: Command help

**Note**: When specifying just a filename for `-o` (e.g., `-o results.csv`), files are automatically saved to the `tests/` directory to keep the project organized. To save elsewhere, provide a full path (e.g., `-o output/results.csv`).

## Workflow Examples

### New Station Analysis
1. `precipgen.bat find-stations temperate -o stations.csv`
2. `precipgen.bat download-station USC00118740 -o chicago.csv`
3. `precipgen.bat gap-analysis chicago.csv --gap-threshold 14`  
4. `precipgen.bat params chicago.csv -o chicago_params.csv`

### Existing Data Analysis
1. `precipgen.bat info my_data.csv`
2. `precipgen.bat gap-analysis my_data.csv --start-year 1950 --end-year 2020`
3. `precipgen.bat params my_data.csv --start-year 1950 --end-year 2020`
4. `precipgen.bat window my_data.csv --window-years 5`

## Complete Workflow Example
```bash
# Step 1: Find stations near Denver within 50km
precipgen.bat find-stations-radius 39.7392 -104.9903 50 --download -o denver_stations.csv

# Step 2: Evaluate data quality for 2000-2023 period
precipgen.bat batch-gap-analysis tests/denver_stations.csv \
  --start-year 2000 --end-year 2023 \
  -o denver_wellness.csv

# Step 3: Download and analyze the best station from results
precipgen.bat download-station USW00023062 -o denver_data.csv
precipgen.bat gap-analysis tests/denver_data.csv --start-year 2000 --end-year 2023
precipgen.bat params tests/denver_data.csv --start-year 2000 --end-year 2023 -o denver_params.csv
```

## Quality Ratings
- **EXCELLENT (≥95%)**: Ready for parameter calculation
- **GOOD (≥90%)**: Generally suitable
- **FAIR (≥80%)**: Use with caution
- **POOR (<80%)**: Gap filling recommended
