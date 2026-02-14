# PrecipGen PAR - Precipitation Parameter Analysis

A tool for analyzing historical precipitation data and generating parameters for stochastic precipitation modeling.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.3.0-green.svg)](https://github.com/jlillywh/precipgen_par/releases)

## Quick Start

### Desktop Application (Recommended)
```bash
# Run the GUI application
python -m precipgen.desktop.app
```

The desktop application provides a clean 6-tab workflow:
1. **Home** - Select working directory
2. **Search** - Find GHCN stations by location
3. **Upload** - Import custom precipitation data
4. **Basic Analysis** - View descriptive statistics
5. **Markov Analysis** - Calculate parameters for PrecipGen
6. **Trend Analysis** - Analyze seasonal trends

### Interactive Menu
```bash
python precipgen-menu.py
```

### Command Line Interface
```bash
# Find stations near Denver, CO
python precipgen-cli.py find-stations-radius 39.7392 -104.9903 50 -o denver_stations.csv

# Download data and analyze
python precipgen-cli.py download-station USW00023066 -o denver_data.csv
python precipgen-cli.py fill-data denver_data.csv -o denver_filled.csv
python precipgen-cli.py params denver_filled.csv -o denver_parameters.csv
```

## Project Structure

```
precipgen_par/
├── precipgen/              # Main package
│   ├── core/              # Core analysis modules
│   ├── data/              # Data handling
│   ├── cli/               # CLI interface
│   ├── desktop/           # Desktop GUI application
│   │   ├── views/        # UI components (6 tabs)
│   │   ├── controllers/  # Business logic
│   │   └── models/       # State management
│   └── web/               # Streamlit web app
├── scripts/                # Executable scripts
├── tests/                  # Test suite (105+ tests)
├── docs/                   # Documentation
│   ├── guides/            # User guides
│   ├── deployment/        # Deployment docs
│   └── api/               # API documentation
├── precipgen-web.py       # Web interface launcher
├── precipgen-cli.py       # CLI launcher
├── precipgen-menu.py      # Interactive menu launcher
├── build_executable.bat   # Build Windows executable
└── README.md
```

## Features

### Desktop GUI (New in v1.3.0)
- Clean 6-tab MVC architecture
- GHCN station search with year range display
- Automatic GHCN metadata parsing
- Progressive disclosure for detailed results
- Station-specific export filenames
- Real-time analysis with progress indicators

### Analysis Capabilities



## What This Tool Does

PrecipGen PAR analyzes historical precipitation data to generate parameters for stochastic precipitation simulation. It's based on the proven WGEN model (1983) and includes modern enhancements:

1. **Find Weather Stations** - Search by city name, coordinates, or climate zone
2. **Download Historical Data** - Automatic download from NOAA databases
3. **Fill Missing Data** - Professional-grade gap filling using meteorological methods
4. **Calculate Parameters** - Generate PWW, PWD, alpha, beta parameters for each month
5. **Advanced Analysis** - Volatility, reversion rates, climate trends, and future projections

The output parameters can be used with precipitation simulation models like PrecipGen to generate synthetic precipitation time series for long-term studies.

## Installation

```bash
git clone https://github.com/yourusername/precipgen_par.git
cd precipgen_par
pip install -r requirements.txt
python easy_start.py  # Test installation
```

Requirements:
- Python 3.9+ (64-bit recommended)
- Dependencies listed in requirements.txt

## Usage Examples

### Example 1: Complete Beginner Workflow
```bash
# Run the interactive menu
python easy_start.py

# Follow the prompts:
# 1. Choose "Find weather stations near me"
# 2. Choose "Search by city name" 
# 3. Type "denver"
# 4. Select "Denver, CO" from the list
# 5. Use defaults and let it find stations
# 6. Download data from the best station
# 7. Analyze with recommended settings
```

### Example 2: Advanced Command Line
```bash
# Find stations within 100km of Seattle
python cli.py find-stations-radius 47.6062 -122.3321 100 \
  --min-years 30 -o seattle_stations.csv

# Download data from the best station
python cli.py download-station USW00024233 -o seattle_data.csv

# Fill missing data (recommended)
python cli.py fill-data seattle_data.csv -o seattle_filled.csv

# Calculate basic parameters
python cli.py params seattle_filled.csv -o seattle_parameters.csv

# Advanced wave analysis
python cli.py wave-analysis seattle_filled.csv \
  --create-plots -o seattle_wave_analysis
```

### Example 3: Batch Analysis
```bash
# Find stations in multiple climate zones
python cli.py find-stations temperate -o temperate_stations.csv
python cli.py find-stations arid -o arid_stations.csv

# Analyze data quality across regions  
python cli.py batch-gap-analysis temperate_stations.csv -o quality_report.csv
```
python cli.py find-stations arid -o arid_stations.csv

# Analyze data quality across regions  
python cli.py batch-gap-analysis temperate_stations.csv -o quality_report.csv
```

## Output Files

PrecipGen PAR creates organized project folders with descriptive file names:

```
your_analysis_folder/
├── denver_precipgen/
│   ├── denver_stations.csv          # Station search results
│   ├── USW00023066_data.csv         # Downloaded raw data
│   ├── USW00023066_filled.csv       # Gap-filled data
│   ├── denver_parameters.csv        # Monthly PWW, PWD, alpha, beta
│   ├── denver_random_walk.json      # Volatility & reversion rates
│   ├── denver_gaps_analysis.csv     # Data quality assessment
│   └── denver_trend_analysis.png    # Visualization plots
└── seattle_precipgen/
    └── [similar files for Seattle]
```

## Scientific Background

This tool implements the proven WGEN precipitation model (Richardson & Wright, 1984) with modern enhancements:

- **Markov Chain Model**: Two-state (wet/dry) first-order Markov process
- **Gamma Distribution**: Models precipitation amounts on wet days
- **Monthly Parameters**: Accounts for seasonal variation
- **Random Walk Extensions**: Captures long-term variability and climate trends
- **Professional Data QA**: Meteorological-grade gap filling and quality control

Key Parameters Generated:
- **PWW**: Probability of wet day following wet day
- **PWD**: Probability of wet day following dry day  
- **alpha, beta**: Gamma distribution shape and scale parameters
- **Volatility**: Parameter variability over time
- **Reversion rates**: Mean-reverting behavior coefficients

## Documentation

- [Getting Started Guide](docs/guides/GETTING_STARTED.md) - Complete setup and usage instructions
- [Quick Reference](docs/guides/QUICK_REFERENCE.md) - Command reference and examples
- [Streamlit Guide](docs/guides/STREAMLIT_GUIDE.md) - Web interface documentation
- [Data Filling Guide](docs/guides/FILL_DATA_GUIDE.md) - Gap filling documentation
- [Deployment Guide](docs/deployment/DEPLOYMENT.md) - Deployment instructions

## Command Line Interface

### Available Commands

The CLI provides comprehensive tools for precipitation data analysis:

**Analysis Commands:**
- `params` - Calculate monthly precipitation parameters (PWW, PWD, alpha, beta)
- `window` - Calculate window-based parameter statistics (volatility, reversion rates)
- `ext-params` - Calculate extended parameters with distribution fitting
- `wave-analysis` - Analyze temporal evolution of parameters using wave functions
- `gap-analysis` - Analyze missing data gaps in precipitation dataset
- `fill-data` - Fill missing values using meteorological methods
- `info` - Display dataset information

**Station Discovery Commands:**
- `find-stations` - Find GHCN stations by climate zone
- `find-stations-radius` - Find stations within radius of coordinates
- `batch-gap-analysis` - Evaluate data quality across multiple stations
- `download-station` - Download data for a specific GHCN station
- `station-info` - Get information about a GHCN station
- `list-zones` - List available climate zones

**Utility Commands:**
- `test` - Run the test suite

### Command Syntax

```bash
# Direct Python usage (cross-platform)
python precipgen-cli.py <command> [options]

# Or use scripts (for convenience)
python scripts/precipgen.bat <command> [options]  # Windows
./scripts/precipgen.sh <command> [options]        # Linux/Mac
```

### Two-Stage Workflow for Station Analysis

#### Stage 1: Station Discovery
Find weather stations by geographic location or climate characteristics:

```bash
# Find stations within 50km of Denver, Colorado
python precipgen-cli.py find-stations-radius 39.7392 -104.9903 50 --download -o denver_stations.csv

# Find stations by climate zone
python precipgen-cli.py find-stations temperate --download -o temperate_stations.csv
```

#### Stage 2: Data Quality Assessment
Evaluate multiple stations with batch gap analysis:

```bash
# Analyze data quality for 2000-2023 period
python precipgen-cli.py batch-gap-analysis denver_stations.csv \
  --start-year 2000 --end-year 2023 \
  -o denver_wellness.csv
```

### Individual Station Analysis

```bash
# Download station data
python precipgen-cli.py download-station USW00023066 -o data.csv

# Check data quality
python precipgen-cli.py gap-analysis data.csv --gap-threshold 14

# Fill missing data if needed
python precipgen-cli.py fill-data data.csv -o filled_data.csv

# Calculate parameters
python precipgen-cli.py params filled_data.csv -o params.csv

# Advanced analysis
python precipgen-cli.py wave-analysis filled_data.csv --create-plots -o wave_results
python precipgen-cli.py window filled_data.csv --window-years 3 -o window_stats.csv
```

### Complete Workflow Example

```bash
# 1. Find stations near Denver within 50km
python precipgen-cli.py find-stations-radius 39.7392 -104.9903 50 --download -o denver_stations.csv

# 2. Evaluate data quality
python precipgen-cli.py batch-gap-analysis denver_stations.csv \
  --start-year 2000 --end-year 2023 \
  -o denver_wellness.csv

# 3. Download best station from results
python precipgen-cli.py download-station USW00023062 -o denver_data.csv

# 4. Analyze data quality
python precipgen-cli.py gap-analysis denver_data.csv --start-year 2000 --end-year 2023

# 5. Fill gaps if needed
python precipgen-cli.py fill-data denver_data.csv -o denver_filled.csv

# 6. Calculate parameters
python precipgen-cli.py params denver_filled.csv --start-year 2000 --end-year 2023 -o denver_params.csv

# 7. Advanced analysis
python precipgen-cli.py wave-analysis denver_filled.csv --create-plots -o denver_wave_analysis
```

### Common Options

- `-o, --output` - Output file path
- `--start-year`, `--end-year` - Date range filtering
- `--window-years` - Years per analysis window (default: varies by command)
- `--gap-threshold` - Threshold for short vs long gaps in days (default: 7)
- `--create-plots` - Generate visualization plots
- `--download` - Auto-download GHCN inventory
- `-h, --help` - Command help

### Data Quality Ratings

- **EXCELLENT (≥95%)** - Ready for parameter calculation
- **GOOD (≥90%)** - Generally suitable
- **FAIR (≥80%)** - Use with caution, gap filling recommended
- **POOR (<80%)** - Gap filling strongly recommended

### Input Data Format

CSV files with precipitation data:
```csv
DATE,PRCP
1900-01-01,0.0
1900-01-02,2.5
1900-01-03,0.0
```

Requirements:
- `DATE` column in YYYY-MM-DD format
- `PRCP` column with numeric precipitation values
- First 6 rows treated as metadata (skipped)

For detailed CLI documentation, see the full command reference in the codebase.

## Recent Updates

- Smart City Search: Search for weather stations by city name (200+ US cities)
- Project Organization: Automatic folder structure keeps work organized by location
- Streamlined Interface: Beginner-friendly menu system with guided workflow
- Advanced Analysis: Random walk parameters, climate trend detection, seasonal analysis
- Professional Data Filling: Meteorological-grade gap filling algorithms

## Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- Richardson, C.W. & Wright, D.A. (1984). WGEN: A model for generating daily weather variables. USDA Agricultural Research Service.
- Based on the foundational FORTRAN implementation from 1983
- Modern Python implementation with enhanced features for climate analysis

## Support

- Check the [Getting Started Guide](GETTING_STARTED.md) for detailed instructions
- Look at [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common tasks
- Create an issue on GitHub for bugs or feature requests

---

Perfect for climate researchers, hydrologists, environmental consultants, students, and anyone needing reliable precipitation parameters for stochastic modeling.
