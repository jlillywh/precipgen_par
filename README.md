# PrecipGen PAR - Precipitation Parameter Analysis

**An easy-to-use tool for analyzing historical precipitation data and generating parameters for stochastic precipitation modeling.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

**For beginners - Use the Interactive Menu:**
```bash
python easy_start.py
```

**For advanced users - Use the Command Line:**
```bash
# Find stations near Denver, CO
python cli.py find-stations-radius 39.7392 -104.9903 50 -o denver_stations.csv

# Download data and analyze
python cli.py download-station USW00023066 -o denver_data.csv
python cli.py fill-data denver_data.csv -o denver_filled.csv
python cli.py params denver_filled.csv -o denver_parameters.csv
```

## ✨ Features

- **🏙️ Smart City Search** - Just type "Denver", "Seattle", "New York" - no coordinates needed
- **📁 Project Organization** - Automatic folder structure keeps your work organized
- **🔧 Professional Data Filling** - Meteorological-grade gap filling using multiple methods
- **📊 Advanced Analysis** - Random walk parameters, climate trends, wave analysis
- **🎯 Beginner-Friendly** - Interactive menu guides you through the entire process
- **⚡ Automated Workflow** - Download data directly from NOAA, no manual website navigation

## 📋 What This Tool Does

PrecipGen PAR analyzes historical precipitation data to generate parameters for stochastic precipitation simulation. It's based on the proven WGEN model (1983) and includes modern enhancements:

1. **Find Weather Stations** - Search by city name, coordinates, or climate zone
2. **Download Historical Data** - Automatic download from NOAA databases
3. **Fill Missing Data** - Professional-grade gap filling using meteorological methods
4. **Calculate Parameters** - Generate PWW, PWD, alpha, beta parameters for each month
5. **Advanced Analysis** - Volatility, reversion rates, climate trends, and future projections

The output parameters can be used with precipitation simulation models like PrecipGen to generate synthetic precipitation time series for long-term studies.

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/precipgen_par.git
   cd precipgen_par
   ```

2. **Install Python 3.9+ (64-bit recommended):**
   - Download from [python.org](https://python.org)
   - Make sure to check "Add Python to PATH" during installation

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Test the installation:**
   ```bash
   python easy_start.py
   ```

## 🎯 Usage Examples

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

# Advanced random walk analysis
python cli.py random-walk seattle_filled.csv \
  --seasonal-analysis --create-plots -o seattle_random_walk
```

### Example 3: Batch Analysis
```bash
# Find stations in multiple climate zones
python cli.py find-stations temperate -o temperate_stations.csv
python cli.py find-stations arid -o arid_stations.csv

# Analyze data quality across regions  
python cli.py batch-gap-analysis temperate_stations.csv -o quality_report.csv
```

## 📊 Output Files

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

## 🔬 Scientific Background

This tool implements the proven WGEN precipitation model (Richardson & Wright, 1984) with modern enhancements:

- **Markov Chain Model**: Two-state (wet/dry) first-order Markov process
- **Gamma Distribution**: Models precipitation amounts on wet days
- **Monthly Parameters**: Accounts for seasonal variation
- **Random Walk Extensions**: Captures long-term variability and climate trends
- **Professional Data QA**: Meteorological-grade gap filling and quality control

**Key Parameters Generated:**
- **PWW**: Probability of wet day following wet day
- **PWD**: Probability of wet day following dry day  
- **alpha, beta**: Gamma distribution shape and scale parameters
- **Volatility**: Parameter variability over time
- **Reversion rates**: Mean-reverting behavior coefficients

## 📚 Documentation

- **[Getting Started Guide](GETTING_STARTED.md)** - Complete setup and usage instructions
- **[Quick Reference](QUICK_REFERENCE.md)** - Command reference and examples
- **[CLI README](CLI_README.md)** - Command-line interface documentation

## 🆕 Recent Updates

- **Smart City Search**: Search for weather stations by city name (200+ US cities)
- **Project Organization**: Automatic folder structure keeps work organized by location
- **Streamlined Interface**: Beginner-friendly menu system with guided workflow
- **Advanced Analysis**: Random walk parameters, climate trend detection, seasonal analysis
- **Professional Data Filling**: Meteorological-grade gap filling algorithms

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 References

- Richardson, C.W. & Wright, D.A. (1984). WGEN: A model for generating daily weather variables. USDA Agricultural Research Service.
- Based on the foundational FORTRAN implementation from 1983
- Modern Python implementation with enhanced features for climate analysis

## 🆘 Support

- Check the [Getting Started Guide](GETTING_STARTED.md) for detailed instructions
- Look at [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common tasks
- Create an issue on GitHub for bugs or feature requests

---

**Perfect for:** Climate researchers, hydrologists, environmental consultants, students, and anyone needing reliable precipitation parameters for stochastic modeling.

2. **Create a virtual environment:**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

## Quick Start for New Users

### For Beginners - Easy Menu Interface

If you're new to command line tools, use the easy menu interface:

**Windows:**
```cmd
# Double-click start_precipgen.bat
# OR run in command prompt:
python easy_start.py
```

**Mac/Linux:**
```bash
# Make executable and run:
chmod +x start_precipgen.sh
./start_precipgen.sh
# OR run directly:
python3 easy_start.py
```

This will give you a simple menu to:
1. Check data quality
2. Calculate parameters  
3. Run wave analysis
4. Get help finding weather data

### For Command Line Users

See the [Getting Started Guide](GETTING_STARTED.md) for detailed command line instructions.

### First Time Setup

1. **Install Python 3.8+** from https://python.org
2. **Download this tool** from GitHub
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Get weather data** from https://www.ncdc.noaa.gov/cdo-web/
5. **Run analysis**: Use `python easy_start.py` or command line tools

### Example Workflow

```bash
# Easy way - menu interface
python easy_start.py

# Command line way
python cli.py download-station USW00023066 -o data.csv
python cli.py fill-data data.csv -o filled_data.csv  # NEW: Fill missing values
python cli.py gap-analysis filled_data.csv -o gaps.csv
python cli.py params filled_data.csv -o parameters.csv  
python cli.py wave-analysis filled_data.csv --create-plots --project-years 20
```

### 4.2 Running the PrecipGenPAR Script

1. **Run the script:**

    ```sh
    python pgpar_cmd.py
    ```

2. **Follow the prompts:**

    - Enter the GHCN station ID when prompted.

3. **View the results:**

    - The script will fetch and process the data, then save the results to a CSV file named `<station_id>_precipitation_parameters.csv`.

### 4.3 Example

```sh
$ python pgpar_cmd.py
Enter the GHCN station ID: USW00094728
Fetching data for station USW00094728...
Dataset Summary:
Station Name: NEW YORK CENTRAL PARK, NY US
Station ID: USW00094728
Location: NY
Coordinates: 40.779, -73.969
Elevation: 42.1 meters
Precipitation units: inches
Date Range: 01/01/2020 to 12/31/2020
Total Records: 366
Precipitation Stats:
  Average Annual Precipitation: 49.92 inches
  Mean Daily Precipitation: 0.14 inches
  Standard Deviation: 0.34 inches

Annual Precipitation Autocorrelation:
  Autocorrelation: 0.1234
  Optimal Lag: 1 year(s)

Results saved to USW00094728_precipitation_parameters.csv
```

### 4.4 Wave Analysis of Parameter Evolution

The system includes advanced wave function analysis to characterize the temporal evolution of PrecipGen parameters. This analysis identifies cyclic patterns and trends in PWW, PWD, alpha, and beta over time.

#### Usage:

```sh
# Basic wave analysis
python cli.py wave-analysis input_data.csv -o wave_results

# Advanced wave analysis with custom parameters
python cli.py wave-analysis input_data.csv \
  --window-years 10 \
  --overlap 0.5 \
  --num-components 5 \
  --create-plots \
  --project-years 20 \
  -o wave_analysis_output

# Demo script for comprehensive analysis
python demo_pgpar_wave.py
```

#### Parameters:
- `--window-years`: Size of sliding window in years (default: 10)
- `--overlap`: Window overlap fraction (default: 0.5)
- `--num-components`: Number of wave components to extract (default: 5)
- `--min-data-threshold`: Minimum data coverage per window (default: 0.8)
- `--project-years`: Years to project into future (default: 0)
- `--create-plots`: Generate visualization plots

#### Output Files:
- `*_wave_params.json`: Complete wave function parameters
- `*_components.csv`: Summary of wave components
- `*_history.csv`: Parameter values over time
- `*_projections.csv`: Future parameter projections (if requested)
- `*_evolution.png`: Parameter evolution plots (if requested)
- `*_components.png`: Wave component analysis plots (if requested)

#### Example Output:
```
Analysis Summary:
--------------------------------------------------

PWW:
  Trend: -0.000326 per year
  Dominant period: 8.0 years
  Total wave amplitude: 0.1821
  Components: 0 short-term, 1 medium-term, 0 long-term

PWD:
  Trend: -0.000028 per year
  Dominant period: 8.0 years
  Total wave amplitude: 0.0637
  Components: 1 short-term, 1 medium-term, 0 long-term
```

### 4.5 Data Filling for Missing Values

Real-world precipitation data often contains missing values due to equipment failures, maintenance periods, or data transmission issues. The PrecipGen PAR tool includes professional-grade data filling capabilities that follow meteorological best practices.

#### Usage:

```sh
# Basic data filling
python cli.py fill-data input_data.csv -o filled_data.csv

# Advanced options
python cli.py fill-data input_data.csv \
  --max-gap-days 30 \
  --min-similarity 0.7 \
  --seasonal-window 15 \
  --min-years-climatology 10 \
  -o filled_data.csv
```

#### Filling Methods:

1. **Linear Interpolation (1-2 day gaps)**
   - Simple linear interpolation between adjacent values
   - Most appropriate for very short gaps
   - Ensures smooth transitions

2. **Climatological Normal (3-7 day gaps)**
   - Uses seasonal averages from other years
   - Considers ±15 day window around target date
   - Preserves seasonal patterns

3. **Analogous Year Method (8+ day gaps)**
   - Finds meteorologically similar years
   - Based on seasonal precipitation patterns
   - Uses correlation analysis for year selection

#### Quality Control:

- Statistical validation of filled values
- Preservation of seasonal patterns
- No negative precipitation values
- Extreme value detection
- Comprehensive quality report generation

#### Output Files:

- `*_filled.csv`: Data with missing values filled
- `*_filling_report.json`: Detailed filling statistics and validation

#### Example Output:
```
Data Filling Summary:
Original missing values: 45
Final missing values: 3
Values filled: 42
Success rate: 93.3%

Methods used:
  Linear Interpolation: 8
  Climatological Normal: 6  
  Analogous Year: 4
```

## 5. Testing
The `PrecipGen` project includes a suite of tests to verify its functionality. Here are the testing requirements:

To run the tests, use the following command: `python -m unittest discover`

## 6. Contributing
Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (git checkout -b feature-branch).
3. Make your changes.
4. Commit your changes (git commit -am 'Add new feature').
5. Push to the branch (git push origin feature-branch).
6. Create a new Pull Request.

## 7. License
This project is licensed under the MIT License. See the LICENSE file for details.

## 8. Contact
For any questions or suggestions, please open an issue or contact the repository owner.
