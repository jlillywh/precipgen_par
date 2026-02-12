# PrecipGen Streamlit Web Interface

## Quick Start

### Installation

1. Install Streamlit (if not already installed):
```bash
pip install streamlit
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### Running the Web Interface

**Windows:**
```cmd
run_streamlit.bat
```

Or manually:
```cmd
streamlit run streamlit_app.py
```

**Mac/Linux:**
```bash
chmod +x run_streamlit.sh
./run_streamlit.sh
```

Or manually:
```bash
streamlit run streamlit_app.py
```

The web interface will automatically open in your default browser at `http://localhost:8501`

## Features

### 🏠 Home
- Overview of the tool
- Quick start guide
- View recent projects

### 📍 Find Stations
- **Search by City**: Select from 100+ major US cities
- **Search by Coordinates**: Enter custom latitude/longitude
- Adjustable search radius (10-200 km)
- Filter by minimum years of data
- Automatic project creation
- Download station lists as CSV

### 📥 Download Data
- Browse available station lists
- Select and download station data
- Preview downloaded data
- Automatic file organization by project

### 🔍 Data Quality Check
- Run gap analysis on downloaded data
- View coverage statistics
- Identify missing data periods
- Export analysis reports

### 🔧 Fill Missing Data
- Multiple interpolation methods (linear, forward, backward)
- Configurable maximum gap size
- Preview filled data
- Recommended before parameter calculation

### 📊 Calculate Parameters
- Compute precipitation statistics
- Works with original or filled data
- Export parameters as CSV
- Download results directly from browser

### 📈 Random Walk Analysis
- Calculate volatility and reversion rates
- Configurable window size
- Optional seasonal analysis
- Automatic plot generation
- Export results in JSON and CSV formats

### 🌊 Wave Analysis
- Advanced seasonal pattern analysis
- Wave function decomposition
- JSON output format

## Workflow

1. **Find Stations** → Search for weather stations near your location
2. **Download Data** → Get historical data for selected stations
3. **Data Quality Check** → Analyze gaps and coverage
4. **Fill Missing Data** → Interpolate missing values (recommended)
5. **Calculate Parameters** → Compute precipitation statistics
6. **Random Walk Analysis** → Analyze long-term variability
7. **Wave Analysis** → Advanced seasonal patterns

## Project Organization

The web interface automatically organizes your work into project directories:

```
your_location_precipgen/
├── your_location_stations.csv          # Station search results
├── STATION_ID_data.csv                 # Downloaded data
├── STATION_ID_filled.csv               # Filled data
├── STATION_ID_parameters.csv           # Calculated parameters
├── STATION_ID_random_walk.json         # Random walk analysis
├── STATION_ID_random_walk.csv          # Random walk results
└── STATION_ID_wave_analysis.json       # Wave analysis
```

## Tips

- **Use filled data** for parameter calculations to get better results
- **Start with a smaller radius** (25-50 km) to find nearby stations faster
- **Check data quality** before running analyses
- **Save your work** - all results are automatically saved to project directories
- **Download results** using the download buttons in the interface

## Advantages Over CLI

✅ **Visual Interface** - No need to remember commands  
✅ **Interactive** - See results immediately  
✅ **File Browser** - Easy file selection  
✅ **Progress Indicators** - Know what's happening  
✅ **Data Preview** - View data before processing  
✅ **Download Buttons** - Export results easily  
✅ **Project Management** - Organized workspace  
✅ **Error Messages** - Clear feedback when things go wrong  

## Troubleshooting

### Port Already in Use
If you see "Address already in use", either:
- Close the existing Streamlit instance
- Or run on a different port:
  ```bash
  streamlit run streamlit_app.py --server.port 8502
  ```

### Module Not Found
Install missing dependencies:
```bash
pip install -r requirements.txt
```

### Inventory Download Fails
- Check your internet connection
- The inventory file is ~50MB and may take a minute to download
- Once downloaded, it's cached for future use

## Configuration

Streamlit can be configured via `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"

[server]
port = 8501
headless = false
```

## Support

For issues or questions:
- Check the main README.md
- Review GETTING_STARTED.md
- Check QUICK_REFERENCE.md for CLI equivalents
