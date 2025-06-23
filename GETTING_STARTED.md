# Getting Started with PrecipGen PAR

This guide will help you get started with PrecipGen PAR to find weather stations, download precipitation data, and analyze it for precipitation modeling.

## Quick Setup

### 1. Install Python (if not already installed)
- Download Python 3.8 or newer from https://python.org
- During installation, make sure to check "Add Python to PATH"

### 2. Download the Tool
```bash
# Clone or download this repository
git clone https://github.com/yourusername/precipgen_par.git
cd precipgen_par
```

### 3. Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt
```

### 4. Test Installation
```bash
# Test that everything works
python cli.py --help
```

## Complete Automated Workflow

The tool can automatically find stations, download data, and perform analysis - no manual website navigation needed!

### Step 1: Find Weather Stations Near You

#### Option A: Search by Climate Zone
```bash
# Find stations in temperate climate zones
python cli.py find-stations temperate --download -o my_stations.csv

# Find stations in arid or tropical zones
python cli.py find-stations arid --download -o desert_stations.csv
python cli.py find-stations tropical --download -o tropical_stations.csv
```

#### Option B: Search by Coordinates and Radius
```bash
# Find stations within 50km of Denver, CO (39.7392, -104.9903)
python cli.py find-stations-radius 39.7392 -104.9903 50 -o denver_area_stations.csv

# Find stations within 100km of your location
python cli.py find-stations-radius YOUR_LAT YOUR_LON 100 -o local_stations.csv

# Customize the search criteria
python cli.py find-stations-radius 40.0 -105.0 75 \
  --min-years 30 \
  --start-before 1990 \
  --end-after 2020 \
  -o quality_stations.csv
```

#### Option C: Get Information About a Specific Station
```bash
# If you know a station ID (like USW00023066 for Grand Junction, CO)
python cli.py station-info USW00023066
```

### Step 2: Download Station Data

Once you've found stations, download the data:

```bash
# Download data for a specific station
python cli.py download-station USW00023066 -o grand_junction_data.csv

# Download data for the best station from your search
# (Look at the CSV from step 1 and pick the best station ID)
python cli.py download-station STATION_ID -o my_station_data.csv
```

### Step 3: Fill Missing Data (RECOMMENDED)

Real-world precipitation data often has missing values. Use professional meteorological methods to fill gaps:

```bash
# Basic data filling
python cli.py fill-data my_station_data.csv -o filled_data.csv

# Advanced options
python cli.py fill-data my_station_data.csv \
  --max-gap-days 30 \
  --min-similarity 0.7 \
  --seasonal-window 15 \
  -o filled_data.csv
```

**Filling methods used:**
- **Linear interpolation**: 1-2 day gaps
- **Climatological normals**: 3-7 day gaps using seasonal averages
- **Analogous year method**: 8+ day gaps using similar years

### Step 4: Analyze Data Quality

Check the quality and completeness of your data (before or after filling):

```bash
# Basic gap analysis
python cli.py gap-analysis filled_data.csv

# Detailed gap analysis with output files
python cli.py gap-analysis filled_data.csv -o gap_analysis_results

# Gap analysis for a specific time period
python cli.py gap-analysis filled_data.csv --start-year 1990 --end-year 2020 -o modern_period_gaps
```

### Step 5: Calculate Parameters

Generate the core PrecipGen parameters (PWW, PWD, alpha, beta):

```bash
# Basic parameter calculation
python cli.py params filled_data.csv -o parameters.csv

# Parameters for a specific time period
python cli.py params filled_data.csv --start-year 1980 --end-year 2010 -o params_1980_2010.csv
```

### Step 6: Wave Function Analysis (Advanced)

Analyze how parameters change over time using wave functions:

```bash
# Basic wave analysis
python cli.py wave-analysis filled_data.csv -o wave_results

# Complete analysis with plots and future projections
python cli.py wave-analysis filled_data.csv \
  --window-years 10 \
  --create-plots \
  --project-years 20 \
  -o comprehensive_wave_analysis
```

## Complete Example Workflow

Here's a complete example starting from scratch:

```bash
# 1. Find stations near Denver, Colorado
python cli.py find-stations-radius 39.7392 -104.9903 100 \
  --min-years 40 \
  --start-before 1980 \
  --end-after 2020 \
  -o denver_stations.csv

# 2. Look at the results and pick the best station
# Open denver_stations.csv and find a station with good coverage

# 3. Download data for the chosen station (example: USW00023066)
python cli.py download-station USW00023066 -o denver_weather_data.csv

# 4. Fill missing data (RECOMMENDED)
python cli.py fill-data denver_weather_data.csv -o denver_weather_filled.csv

# 5. Check data quality
python cli.py gap-analysis denver_weather_filled.csv -o denver_gaps

# 6. Calculate parameters
python cli.py params denver_weather_filled.csv -o denver_parameters.csv

# 7. Analyze temporal patterns
python cli.py wave-analysis denver_weather_filled.csv \
  --create-plots \
  --project-years 25 \
  -o denver_wave_analysis
```

## Batch Analysis of Multiple Stations

You can also analyze multiple stations at once:

```bash
# 1. Find multiple stations
python cli.py find-stations-radius 40.0 -105.0 200 -o region_stations.csv

# 2. Run batch gap analysis on all found stations
python cli.py batch-gap-analysis region_stations.csv -o batch_wellness_summary.csv

# 3. Choose the best stations from the wellness summary
# 4. Download and analyze each one individually
```

## Understanding the Outputs

### Station Search Results
- `*_stations.csv`: List of stations with metadata (location, data range, coverage)
- Columns include: STATION, LAT, LON, ELEVATION, START_YEAR, END_YEAR, TOTAL_YEARS

### Downloaded Data
- Station data in CSV format with DATE and PRCP columns
- Ready for analysis with the other tools

### Gap Analysis Results
- `*_gaps_summary.csv`: Summary of data completeness
- `*_gaps_long_gaps.csv`: Details of major data gaps
- Shows data quality and suitability for analysis

### Parameter Results
- `parameters.csv`: Monthly PWW, PWD, ALPHA, BETA values
- These are the core parameters used for precipitation simulation

### Wave Analysis Results
- `*_wave_params.json`: Wave function parameters for long-term modeling
- `*_history.csv`: How parameters change over time
- `*_projections.csv`: Future parameter projections
- `*_evolution.png` and `*_components.png`: Visualization plots

## Advanced Options

### Station Search Criteria
```bash
# Customize search parameters
python cli.py find-stations-radius LAT LON RADIUS \
  --data-types PRCP,TMAX,TMIN \
  --min-years 30 \
  --start-before 1990 \
  --end-after 2020
```

### Analysis Time Periods
```bash
# Analyze specific periods
python cli.py params data.csv --start-year 1950 --end-year 2000
python cli.py wave-analysis data.csv --start-year 1980 --end-year 2020
```

### Wave Analysis Options
```bash
python cli.py wave-analysis data.csv \
  --window-years 15 \
  --overlap 0.6 \
  --num-components 7 \
  --min-data-threshold 0.85 \
  --project-years 30 \
  --create-plots
```

## Tips for Success

1. **Start with Station Search**: Use the automated tools to find high-quality stations
2. **Check Multiple Stations**: Different stations may have different data quality
3. **Longer Records Better**: 30+ years of data gives more reliable results
4. **Quality Over Quantity**: Choose stations with >90% data completeness
5. **Regional Analysis**: Compare multiple stations in your area of interest

## Getting Help

- Use `python cli.py --help` for command overview
- Use `python cli.py [command] --help` for specific command help
- Check existing station info: `python cli.py station-info STATION_ID`

## Available Climate Zones

The tool includes predefined climate zones:
- **temperate**: Eastern USA, Western Europe, Eastern China
- **arid**: Southwest USA, Western Australia, Southern Africa  
- **tropical**: Amazon Basin, Southeast Asia, Central Africa

You can also search by specific coordinates for any location worldwide.

## Troubleshooting

**"Module not found" errors**: Run `pip install -r requirements.txt`

**"No stations found"**: Try increasing search radius or relaxing criteria

**"Connection errors"**: Check internet connection for data downloads

**"Empty data files"**: Station may not have data for your requested period

**Permission errors**: Make sure you have write permissions in the output directory
