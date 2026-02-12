# Getting Started with PrecipGen PAR

This guide will help you get started with PrecipGen PAR to find weather stations, download precipitation data, and analyze it for precipitation modeling.

## 🚀 **EASIEST WAY TO START** 

**For beginners: Use the Interactive Menu Interface**

```bash
python easy_start.py
```

This opens a user-friendly menu that guides you through the entire process:
- **Find stations by city name** (just type "denver", "seattle", etc.)
- **Automatic project organization** (each location gets its own folder)
- **Guided workflow** with helpful tips and explanations
- **No command-line knowledge required**

**For advanced users:** Continue reading for command-line interface (CLI) instructions.

---

## Quick Setup

### 1. Install Python (if not already installed)

**IMPORTANT for Windows users:** Make sure to install 64-bit Python for best compatibility with scientific packages.

#### Quick Check: Do you have the right Python?
```powershell
# Check if you have 64-bit Python installed
python -c "import platform; print(f'Python {platform.python_version()} - {platform.architecture()[0]}')"
```

You should see something like: `Python 3.12.5 - 64bit`

If you see `32bit` or get an error, follow the installation steps below.

#### Fresh Installation (Recommended)
1. **Download 64-bit Python** from https://python.org
   - Choose "Windows installer (64-bit)" 
   - Python 3.9, 3.10, 3.11, or 3.12 are all supported
2. During installation:
   - ✅ Check "Add Python to PATH" 
   - ✅ Check "Install for all users" (if you have admin rights)
   - Choose "Customize installation" and ensure "pip" is selected

#### If you have multiple Python versions
If you already have Python installed but it's 32-bit, you can:

**Option A: Install 64-bit Python alongside (Recommended)**
```powershell
# After installing 64-bit Python, create venv with specific Python
C:\Users\YourUsername\AppData\Local\Programs\Python\Python312\python.exe -m venv venv
.\venv\Scripts\Activate.ps1
```

**Option B: Use py launcher to select 64-bit version**
```powershell
# List available Python versions
py -0

# Create venv with specific 64-bit version (e.g., 3.12)
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

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

# OR use the beginner-friendly interface
python easy_start.py
```

## 🎯 **RECOMMENDED FOR BEGINNERS: Interactive Menu**

The easiest way to use PrecipGen PAR is through the interactive menu:

```bash
python easy_start.py
```

### What the Interactive Menu Does:

1. **🏙️ Smart City Search** - Just type city names like "Denver", "Los Angeles", "New York"
   - Built-in database of 200+ major US cities
   - Automatically finds coordinates for you
   - No need to look up latitude/longitude

2. **📁 Project Organization** - Keeps your work organized automatically
   - Each city/location gets its own folder (e.g., `denver_precipgen/`)
   - All files for that project stay together
   - Easy to find and manage your analysis results

3. **🎯 Guided Workflow** - Step-by-step process with helpful tips
   - Find stations → Download data → Fill gaps → Analyze
   - Clear explanations of what each step does
   - Shows you exactly what files were created and where

4. **💡 Smart Recommendations** - Suggests the best options
   - Recommends filled data over raw data for analysis
   - Shows which stations have the most complete data
   - Guides you through parameter choices

### Example: Denver Analysis in 5 Minutes

1. Run `python easy_start.py`
2. Choose "1. Find weather stations near me"
3. Choose "1. Search by city name"
4. Type "denver" and select "Denver, CO"
5. Use defaults (50km radius, project name "denver")
6. Choose "2. Download data from a station" and pick the best station
7. Use the recommended filled data analysis options
8. Get your precipitation parameters!

All files will be neatly organized in the `denver_precipgen/` folder.

---

## 🔧 **ADVANCED: Command Line Interface**

## 🔧 **ADVANCED: Command Line Interface**

The command line interface gives you full control and is perfect for automation and batch processing.

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

## 📁 **Project Organization**

PrecipGen PAR automatically organizes your work:

- **Base directory**: Where you run the tool (configured during first use)
- **Project directories**: Automatically created for each location
  - Format: `{location}_precipgen/` (e.g., `denver_precipgen/`, `seattle_precipgen/`)
  - Contains all files for that location: station lists, data, analysis results
- **File naming**: Descriptive names that show what each file contains

### Example Project Structure:
```
your_analysis_folder/
├── denver_precipgen/
│   ├── denver_stations.csv
│   ├── USW00023066_data.csv
│   ├── USW00023066_filled.csv
│   └── denver_parameters.csv
├── seattle_precipgen/
│   ├── seattle_stations.csv
│   ├── USW00024233_data.csv
│   └── seattle_analysis_results.json
└── precipgen_config.json
```

---

## 💡 **Tips for Your Son**

1. **Start Simple**: Use `python easy_start.py` - it's designed for beginners
2. **City Search**: Just type city names - no need to look up coordinates
3. **Follow the Numbers**: The menu options are numbered 1-11, follow them in order
4. **Use Filled Data**: When given a choice, always choose "filled" data for analysis
5. **One Project per Location**: Create separate projects for each city/location you analyze
6. **Check the Project Folder**: All your results are saved in the `{city}_precipgen/` folder

---

## 📊 **Understanding the Outputs**
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

## 🚀 **Quick Start for Your Son**

1. **Open Terminal/Command Prompt** in the PrecipGen PAR folder
2. **Run**: `python easy_start.py`
3. **Follow the menu**:
   - Choose option 1 (Find weather stations near me)
   - Choose option 1 (Search by city name)
   - Type your city name (e.g., "denver", "seattle")
   - Select your city from the list
   - Accept the defaults (50km radius is usually good)
   - Let it create your project folder
4. **Download data**: Choose option 2, pick the best station from your list
5. **Analyze**: Use options 4-7 to fill data and calculate parameters
6. **Find your results**: Look in the `{yourcity}_precipgen/` folder

**That's it!** Everything is automatic and organized for you.

---

## 🆕 **New Features**

### 🏙️ City Search Database
- **200+ Major US Cities**: Just type "denver", "new york", "los angeles"
- **Smart Matching**: Finds cities even with partial names
- **Automatic Coordinates**: No need to look up latitude/longitude
- **Multiple Matches**: Shows all matching cities if there are several

### 📁 Project-Aware Organization
- **Automatic Folders**: Each location gets its own organized folder
- **Smart File Paths**: All analysis results go to the right project folder
- **Context Display**: Shows which project each file belongs to
- **Easy Navigation**: Find all your work for a location in one place

### 🎯 Streamlined Workflow
- **Removed Unnecessary Prompts**: No more confusing "fill data?" questions
- **Smart Defaults**: Recommends the best options for beginners
- **Clear Labels**: Files are clearly marked as "ORIGINAL DATA" or "FILLED DATA"
- **Project Context**: Always shows which city/project you're working with

### 💫 Random Walk Analysis
- **Advanced Parameters**: Calculates volatility and reversion rates
- **Climate Trends**: Detects long-term climate change patterns
- **Seasonal Analysis**: Analyzes trends within each season
- **Export Options**: Results in multiple formats for different uses

---

## ⚠️ **Troubleshooting**

### Python Installation Issues

**"Python dependency not found" or "Need python for x86_64, but found x86"**:
- This means you have 32-bit Python but need 64-bit for scientific packages
- Solution: Install 64-bit Python from https://python.org
- After installing 64-bit Python, recreate your virtual environment:
  ```powershell
  # Remove old venv
  Remove-Item -Recurse -Force venv
  
  # Create new venv with 64-bit Python
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

**"pandas installation fails with meson build errors"**:
- Usually indicates 32-bit Python or missing build tools
- Use the 64-bit Python solution above
- If still failing, try: `pip install --only-binary=all pandas`

**"Multiple Python versions detected"**:
- Use py launcher to select specific version:
  ```powershell
  py -0  # List available versions
  py -3.12 -m venv venv  # Use specific 64-bit version
  ```

### Package Installation Issues

**"Module not found" errors**: Run `pip install -r requirements.txt`

**"Permission denied during pip install"**: 
- Make sure virtual environment is activated
- On Windows, run PowerShell as administrator if needed

### Data and Connection Issues

**"No stations found"**: Try increasing search radius or relaxing criteria

**"Connection errors"**: Check internet connection for data downloads

**"Empty data files"**: Station may not have data for your requested period

**Permission errors**: Make sure you have write permissions in the output directory
