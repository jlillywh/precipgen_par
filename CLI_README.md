# PrecipGen Parameter CLI Tool

A command-line interface for precipitation parameter generation and analysis. This tool provides various functions for analyzing precipitation time series data and calculating parameters used in precipitation generation models.

## Two-Stage Workflow for Station Analysis

This CLI implements a **two-stage workflow** for finding and evaluating precipitation monitoring stations:

### Stage 1: Station Discovery
Find weather stations by geographic location or climate characteristics
- **Geographic Search**: Find stations within a radius of specified coordinates
- **Climate Zone Search**: Find stations by climate zone (arid, tropical, temperate)

### Stage 2: Data Quality Assessment  
Evaluate multiple stations with batch gap analysis to determine data "wellness"
- **Batch Gap Analysis**: Analyze data quality across multiple stations
- **Wellness Summary**: Get ranked results showing the best stations for analysis

## Installation & Setup

1. **Clone/Download the project** to your local machine
2. **Ensure Python 3.x is installed** on your system
3. **Install dependencies**:
   ```bash
   pip install pandas numpy scipy requests tqdm
   ```
   Or if using a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

## Usage

The CLI tool provides several commands for different types of analysis:

### Basic Usage

```bash
# Direct Python usage
python cli.py <command> [options]

# Windows batch script (easier)
.\precipgen.bat <command> [options]

# PowerShell script
.\precipgen.ps1 <command> [options]
```

## Two-Stage Workflow Commands

### Stage 1: Station Discovery

#### `find-stations-radius` - Find Stations by Geographic Location
Find GHCN weather stations within a specified radius of coordinates.

```bash
# Find stations within 50km of Denver, Colorado
python cli.py find-stations-radius 39.7392 -104.9903 50 --download -o denver_stations.csv

# Find stations with specific data requirements
python cli.py find-stations-radius 40.7128 -74.0060 100 \
  --data-types PRCP,TMAX,TMIN \
  --min-years 30 \
  --start-before 1990 \
  --end-after 2020 \
  -o nyc_stations.csv
```

**Parameters:**
- `latitude longitude radius`: Geographic center point and search radius (km)
- `--data-types`: Required data types (default: PRCP,TMAX,TMIN)
- `--min-years`: Minimum years of data required (default: 30)
- `--start-before`: Data must start on or before this year (default: 1990)
- `--end-after`: Data must end after this year (default: 2020)
- `--download`: Download GHCN inventory if not found locally
- `-o`: Output CSV file with station results

#### `find-stations` - Find Stations by Climate Zone
Find stations within specific climate zones.

```bash
python cli.py find-stations temperate --download -o temperate_stations.csv
python cli.py find-stations arid -o arid_stations.csv
```

### Stage 2: Data Quality Assessment

#### `batch-gap-analysis` - Evaluate Multiple Stations
Perform gap analysis on multiple stations and create a wellness summary.

```bash
# Analyze stations found in Stage 1
python cli.py batch-gap-analysis denver_stations.csv -o denver_wellness.csv

# Analyze specific time period
python cli.py batch-gap-analysis stations.csv \
  --start-year 2000 \
  --end-year 2023 \
  --column PRCP \
  --gap-threshold 7 \
  -o wellness_summary.csv
```

**Parameters:**
- `stations_file`: CSV file with station list (must have STATION column)
- `--start-year/--end-year`: Limit analysis to specific time period
- `--column`: Data column to analyze (default: PRCP)
- `--gap-threshold`: Threshold for short vs long gaps in days (default: 7)
- `-o`: Output CSV file with wellness summary

**Wellness Summary Output:**
- Station ID, name, coordinates, distance
- Data coverage percentage
- Quality rating (EXCELLENT/GOOD/FAIR/POOR)
- Gap statistics (short gaps, long gaps, longest gap)
- Quality score for ranking

## Individual Analysis Commands

### 0. `gap-analysis` - Single Station Data Quality Assessment
Analyze missing data patterns in precipitation datasets before parameter calculation.

```bash
python cli.py gap-analysis input.csv --gap-threshold 14 -o gap_results
python cli.py gap-analysis input.csv --start-year 1950 --end-year 2020 --column PRCP
```

**Analysis Output:**
- Data coverage percentage
- Count of short vs long gaps
- Detailed information about significant gaps
- Data quality assessment and recommendations
- Export options for gap analysis results

**Quality Thresholds:**
- **Excellent (≥95% coverage)**: Ready for parameter calculation
- **Good (≥90% coverage)**: Generally suitable, consider gap filling for long gaps
- **Fair (≥80% coverage)**: Use with caution, gap filling recommended
- **Poor (<80% coverage)**: Gap filling strongly recommended

**Options:**
- `--gap-threshold`: Days threshold for short vs long gaps (default: 7)
- `--column`: Data column to analyze (default: PRCP)

### 1. `params` - Calculate Monthly Parameters
Calculate basic precipitation parameters (PWW, PWD, ALPHA, BETA) for each month.

```bash
python cli.py params input.csv -o output.csv
python cli.py params input.csv --start-year 1950 --end-year 2020
```

**Parameters:**
- `PWW`: Probability of wet day following wet day
- `PWD`: Probability of wet day following dry day  
- `ALPHA`: Gamma distribution shape parameter
- `BETA`: Gamma distribution scale parameter

### 2. `window` - Calculate Window Statistics
Calculate volatility and reversion rates using sliding windows.

```bash
python cli.py window input.csv --window-years 3 -o window_stats.csv
```

**Options:**
- `--window-years`: Number of years per sliding window (default: 2)

### 3. `ext-params` - Extended Parameter Analysis
Calculate parameters with distribution fitting across multiple time windows.

```bash
python cli.py ext-params input.csv --window-years 3 -o ext_params
```

**Output:** Creates separate CSV files for each parameter's distribution data.

### 4. `info` - Dataset Information
Display basic information about the precipitation dataset.

```bash
python cli.py info input.csv
```

**Shows:**
- Date range and total days
- Wet/dry day statistics
- Basic precipitation statistics

### 5. `random-walk` - Random Walk Parameter Analysis (RECOMMENDED)
Analyze precipitation parameters for mean-reverting random walk modeling. This is the **recommended approach** for capturing long-term variability in precipitation parameters.

```bash
python cli.py random-walk input.csv -o random_walk_results
python cli.py random-walk input.csv --window-years 2 --create-plots -o rw_analysis
```

**What it calculates:**
- **Volatility (σ)**: Annual random fluctuation magnitude for each parameter
- **Reversion Rate (r)**: Speed of return to long-term mean values
- **Parameter Correlations**: For Gaussian copula dependency modeling
- **Long-term Means**: Target values for the random walk process

**Methodology:**
- Uses overlapping 2-year windows (based on published research)
- Estimates volatility from first-order differences: σ = std(Δx)
- Estimates reversion rate via regression: Δx = r(μ - x₋₁) + ε
- Calculates PWW-PWD, PWW-alpha correlations for realistic simulations

**Options:**
- `--window-years`: Window size for parameter extraction (default: 2)
- `--create-plots`: Generate diagnostic and correlation plots
- `--start-year`, `--end-year`: Limit analysis to specific time period

**Output Files:**
- `*_random_walk_params.json`: Complete analysis results with metadata
- `*_random_walk_summary.csv`: Summary table of volatilities and reversion rates
- `*_parameter_sequence.csv`: Historical parameter values from sliding windows
- `*_random_walk_evolution.png`: Parameter evolution plots (if --create-plots)
- `*_correlation_matrix.png`: Parameter correlation heatmap (if --create-plots)

**Use Case:** These parameters enable realistic long-term precipitation simulation by allowing parameters to fluctuate around historical means while maintaining proper correlations.

### 6. `test` - Run Test Suite
Run the project's test suite to verify functionality.

```bash
python cli.py test
```

### Station Discovery & Data Download

The CLI also includes powerful utilities for discovering and downloading precipitation data from the Global Historical Climatology Network (GHCN) database.

### 7. `list-zones` - List Climate Zones
Display available climate zones and their geographic coverage.

```bash
python cli.py list-zones
```

**Shows:**
- Available climate zones (arid, tropical, temperate)
- Geographic coordinate ranges for each zone
- Description of each climate type

### 8. `find-stations` - Find Stations by Climate Zone
Search for GHCN stations in specific climate zones that meet quality criteria.

```bash
python cli.py find-stations temperate --download -o temperate_stations.csv
python cli.py find-stations arid --inventory-file my_inventory.txt
```

**Quality Criteria:**
- Located in specified climate zone
- Has precipitation (PRCP), max temp (TMAX), min temp (TMIN) data
- At least 90 years of historical data
- Data coverage >95%
- Records start on or before 1900
- Records end after 2023

**Options:**
- `--download`: Automatically download GHCN inventory if not found
- `--inventory-file`: Specify custom inventory file path

### 9. `download-station` - Download Station Data
Download complete dataset for a specific GHCN station.

```bash
python cli.py download-station USW00023066 -o grand_junction_data.csv
python cli.py download-station USC00050848  # Uses default filename
```

**Downloads:**
- Complete historical dataset in CSV format
- Includes metadata (station name, location, coverage, etc.)
- Ready for analysis with other CLI commands

### 10. `station-info` - Get Station Information
Get basic information about a GHCN station without downloading the full dataset.

```bash
python cli.py station-info USW00023066
```

**Shows:**
- Station name and ID
- Geographic location (latitude/longitude) 
- Date range of available data
- Data coverage percentage
- Available data types (PRCP, TMAX, TMIN, etc.)

## Input Data Format

The tool expects CSV files with precipitation data in the following format:

```
# Header rows (6 lines of metadata - will be skipped)
DATE,PRCP
1900-01-01,0.0
1900-01-02,2.5
1900-01-03,0.0
...
```

**Requirements:**
- `DATE` column: Date in YYYY-MM-DD format
- `PRCP` column: Precipitation amount (numeric)
- First 6 rows are treated as metadata and skipped

## Examples

### Complete Workflow Example

```bash
# 1. Check dataset information
python cli.py info "data/precipitation.csv"

# 2. PERFORM GAP ANALYSIS FIRST (RECOMMENDED)
python cli.py gap-analysis "data/precipitation.csv" \
    --start-year 1950 --end-year 2020 \
    --gap-threshold 14 \
    -o "results/gap_analysis"

# 3. Calculate basic monthly parameters (if gap analysis shows good quality)
python cli.py params "data/precipitation.csv" \
    --start-year 1950 --end-year 2020 \
    -o "results/monthly_params.csv"

# 4. Calculate random walk parameters (RECOMMENDED for long-term variability)
python cli.py random-walk "data/precipitation.csv" \
    --start-year 1950 --end-year 2020 \
    --create-plots \
    -o "results/random_walk_analysis"

# 5. Calculate window statistics (alternative approach)
python cli.py window "data/precipitation.csv" \
    --start-year 1950 --end-year 2020 \
    --window-years 5 \
    -o "results/window_stats.csv"

# 6. Run extended analysis
python cli.py ext-params "data/precipitation.csv" \
    --start-year 1950 --end-year 2020 \
    --window-years 3 \
    -o "results/ext_params"

# 7. Run tests to verify everything works
python cli.py test
```

### Using the Sample Data

```bash
# The project includes sample data for testing
python cli.py info "tests/GrandJunction/USW00023066_data.csv"
python cli.py params "tests/GrandJunction/USW00023066_data.csv" -o sample_params.csv

# RECOMMENDED: Run random walk analysis on sample data
python cli.py random-walk "tests/GrandJunction/USW00023066_data.csv" \
    --create-plots -o sample_random_walk
```

### Discover and Analyze New Stations

```bash
# 1. List available climate zones
python cli.py list-zones

# 2. Find stations in temperate zones
python cli.py find-stations temperate --download -o temperate_stations.csv

# 3. Get info about a specific station from results
python cli.py station-info USC00050848

# 4. Download the station data
python cli.py download-station USC00050848 -o chicago_data.csv

# 5. Analyze the downloaded data
python cli.py info chicago_data.csv
python cli.py params chicago_data.csv --start-year 1950 --end-year 2020 -o chicago_params.csv

# 6. RECOMMENDED: Run random walk analysis for long-term variability modeling
python cli.py random-walk chicago_data.csv --start-year 1950 --end-year 2020 \
    --create-plots -o chicago_random_walk
```

### Compare Multiple Stations

```bash
# Download data for comparison
python cli.py download-station USW00023066 -o grand_junction.csv  # Arid
python cli.py download-station USC00111577 -o miami.csv           # Tropical  
python cli.py download-station USC00118740 -o chicago.csv         # Temperate

# Analyze each station
python cli.py params grand_junction.csv -o gj_params.csv
python cli.py params miami.csv -o miami_params.csv  
python cli.py params chicago.csv -o chicago_params.csv

# Compare window statistics
python cli.py window grand_junction.csv --window-years 5 -o gj_window.csv
python cli.py window miami.csv --window-years 5 -o miami_window.csv
python cli.py window chicago.csv --window-years 5 -o chicago_window.csv
```

## Common Options

- `-o, --output`: Specify output file path
- `--start-year`: Start year for data trimming
- `--end-year`: End year for data trimming
- `--window-years`: Number of years per analysis window
- `-h, --help`: Show help for any command

## Output Files

### Monthly Parameters (`params` command)
```csv
,PWW,PWD,ALPHA,BETA
1,0.435,0.155,0.998,2.280
2,0.415,0.172,0.998,2.242
...
```

### Window Statistics (`window` command)
```csv
Parameter,Volatility,Reversion_Rate
PWW,0.036,0.317
PWD,0.015,0.293
ALPHA,0.052,0.351
BETA,0.395,0.387
```

## Complete Workflow Example

Here's a complete example of using the two-stage workflow to find and evaluate weather stations for precipitation analysis:

### Example: Finding the Best Stations Near Denver, Colorado

#### Step 1: Find Stations by Geographic Location
```bash
# Find stations within 50km of Denver, requiring good data quality
python cli.py find-stations-radius 39.7392 -104.9903 50 \
  --data-types PRCP,TMAX,TMIN \
  --min-years 30 \
  --start-before 1990 \
  --end-after 2020 \
  --download \
  -o denver_area_stations.csv
```

**Output:** List of 13 qualifying stations with their coordinates, distance from target, data coverage periods, and available data types.

#### Step 2: Evaluate Data Quality with Batch Gap Analysis
```bash
# Analyze data quality for all found stations over 2000-2023 period
python cli.py batch-gap-analysis denver_area_stations.csv \
  --start-year 2000 \
  --end-year 2023 \
  --column PRCP \
  --gap-threshold 7 \
  -o denver_wellness_summary.csv
```

**Output:** Wellness summary with quality ratings:
```
🏆 TOP STATIONS BY QUALITY:
STATION_ID          STATION_NAME      DISTANCE_KM  COVERAGE_PCT  QUALITY_RATING  LONG_GAPS
USW00023062    DENVER-STAPLETON          10.68        99.63      EXCELLENT         1
USC00058022  STRONTIA SPRINGS DAM        35.72        99.28      EXCELLENT         2
USC00050848           BOULDER            36.78        99.27      EXCELLENT         2
USC00052790         EVERGREEN            29.97        99.21      EXCELLENT         1
USC00056816      RALSTON RSVR            23.14        98.94      EXCELLENT         2
```

#### Step 3: Analyze Individual High-Quality Stations
Now use the best stations for detailed precipitation parameter analysis:

```bash
# Download data for the best station (Denver-Stapleton)
python cli.py download-station USW00023062 -o denver_stapleton_data.csv

# Perform gap analysis to confirm data quality
python cli.py gap-analysis denver_stapleton_data.csv \
  --start-year 2000 \
  --end-year 2023 \
  --gap-threshold 7 \
  -o denver_stapleton_gaps.csv

# Calculate precipitation parameters
python cli.py params denver_stapleton_data.csv \
  --start-year 2000 \
  --end-year 2023 \
  -o denver_stapleton_params.csv

# Calculate extended parameters
python cli.py ext-params denver_stapleton_data.csv \
  --start-year 2000 \
  --end-year 2023 \
  -o denver_stapleton_ext_params.csv
```

### Alternative Example: Finding Stations by Climate Zone

#### Step 1: Find Stations in Temperate Climate Zone
```bash
# Find high-quality stations in temperate climate regions
python cli.py find-stations temperate --download -o temperate_stations.csv
```

#### Step 2: Batch Analysis of Climate Zone Stations
```bash
# Evaluate data quality across all temperate zone stations
python cli.py batch-gap-analysis temperate_stations.csv \
  --start-year 1990 \
  --end-year 2023 \
  --column PRCP \
  -o temperate_wellness_summary.csv
```

### Workflow Benefits

1. **Systematic Station Discovery**: Find stations meeting specific geographic and data quality criteria
2. **Batch Quality Assessment**: Evaluate multiple stations simultaneously
3. **Data-Driven Selection**: Choose the best stations based on objective quality metrics
4. **Time Efficient**: Avoid manual downloading and evaluation of poor-quality stations
5. **Reproducible Results**: Documented criteria and parameters for station selection

### Quality Ratings Explained

- **EXCELLENT (≥95% coverage)**: Suitable for high-precision parameter estimation
- **GOOD (≥90% coverage)**: Suitable for most precipitation analyses  
- **FAIR (≥80% coverage)**: May require gap-filling before analysis
- **POOR (<80% coverage)**: Not recommended for parameter estimation

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError"**: Install required packages
   ```bash
   pip install pandas numpy scipy
   ```

2. **"File not found"**: Check file path and make sure file exists
   ```bash
   python cli.py info "path/to/your/file.csv"
   ```

3. **"Virtual environment not found"**: When using batch/PowerShell scripts
   - Make sure you're in the project directory
   - Ensure `.venv` directory exists with Python executable

### Getting Help

```bash
# General help
python cli.py --help

# Command-specific help
python cli.py params --help
python cli.py window --help
python cli.py ext-params --help
```

## Development

### Adding New Commands

To add a new command to the CLI:

1. Create a new function `cmd_your_command(args)` in `cli.py`
2. Add a new subparser in the `main()` function
3. Set the function as the default handler with `set_defaults(func=cmd_your_command)`

### Running Tests

```bash
python cli.py test
# or directly
python -m pytest tests/
```

## License

See LICENSE.txt for license information.
