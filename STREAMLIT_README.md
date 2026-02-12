# 🌐 PrecipGen Streamlit Web Interface

## What is This?

A modern, user-friendly web interface for PrecipGen that runs in your browser. No command line knowledge needed!

## Quick Start (3 Steps)

### 1. Install Streamlit
```bash
pip install streamlit
```

### 2. Launch the Interface
**Windows:** Double-click `run_streamlit.bat`

**Mac/Linux:** 
```bash
chmod +x run_streamlit.sh
./run_streamlit.sh
```

**Or manually:**
```bash
streamlit run streamlit_app.py
```

### 3. Use the Interface
Your browser opens automatically. Start with "Find Stations" in the sidebar!

## What Can You Do?

### 🏠 Home
- Overview and quick start guide
- View recent projects
- One-click project opening

### 📍 Find Stations
- **Search by City:** Choose from 100+ major US cities
- **Search by Coordinates:** Enter custom lat/lon
- Adjust search radius with slider
- Filter by minimum years of data
- See results in interactive table
- Download station list as CSV
- Automatic project creation

### 📥 Download Data
- Browse available station lists
- Select station from dropdown
- One-click data download
- Preview downloaded data
- Automatic file organization

### 🔍 Data Quality Check
- Run gap analysis
- View coverage statistics
- Identify missing data periods
- Export analysis reports

### 🔧 Fill Missing Data
- Choose fill method (linear, forward, backward)
- Set maximum gap size
- Preview filled data
- Recommended before parameter calculation

### 📊 Calculate Parameters
- Compute precipitation statistics
- Works with original or filled data
- View results in table
- Download parameters as CSV

### 📈 Random Walk Analysis
- Calculate volatility and reversion rates
- Configurable window size
- Optional seasonal analysis
- Automatic plot generation
- Export in JSON and CSV formats

### 🌊 Wave Analysis
- Advanced seasonal pattern analysis
- Wave function decomposition
- JSON output format

## Why Use Streamlit?

### vs. Command Line Interface (CLI)
| Feature | Streamlit | CLI |
|---------|-----------|-----|
| Learning curve | ⭐⭐⭐⭐⭐ Easy | ⭐⭐ Hard |
| File selection | Click dropdown | Type full path |
| Data preview | Built-in tables | Separate command |
| Progress | Visual indicators | Text output |
| Results | Interactive tables | Terminal text |
| Plots | Inline display | Saved to files |
| Downloads | Browser button | Find file manually |

### vs. Easy Start Menu
| Feature | Streamlit | Easy Start |
|---------|-----------|------------|
| Interface | Web browser | Terminal |
| Visual feedback | ⭐⭐⭐⭐⭐ | ⭐ |
| Data preview | Yes | No |
| Multi-tasking | Multiple tabs | Sequential |
| File browser | Dropdown | Type path |

## Typical Workflow

1. **Find Stations** (2 minutes)
   - Select city or enter coordinates
   - Adjust search radius
   - Click "Search Stations"
   - Review results table

2. **Download Data** (1 minute)
   - Select station list
   - Choose station
   - Click "Download Station Data"
   - Preview data

3. **Fill Missing Data** (30 seconds)
   - Select data file
   - Choose fill method
   - Click "Fill Missing Data"

4. **Calculate Parameters** (30 seconds)
   - Select filled data file
   - Click "Calculate Parameters"
   - Download results

5. **Advanced Analysis** (2-5 minutes)
   - Run Random Walk or Wave Analysis
   - View results and plots
   - Export data

**Total time: ~5-10 minutes from start to results!**

## Project Organization

Streamlit automatically organizes your work in a separate data directory:

```
precipgen_par/                        ← Source code
└── precipgen_data/                   ← All output files
    └── phoenix_precipgen/
        ├── phoenix_stations.csv              # Station search results
        ├── USW00023183_data.csv              # Downloaded data
        ├── USW00023183_filled.csv            # Filled data
        ├── USW00023183_parameters.csv        # Parameters
        ├── USW00023183_random_walk.json      # Analysis results
        ├── USW00023183_random_walk.csv       # Analysis data
        └── USW00023183_random_walk_*.png     # Plots
```

**Benefits:**
- ✅ Clean separation of code and data
- ✅ Easy to backup just your analysis work
- ✅ Data excluded from version control
- ✅ Professional project organization

See [DATA_ORGANIZATION.md](DATA_ORGANIZATION.md) for details.

## Features

✅ **No Command Line** - Point and click interface  
✅ **Visual Feedback** - See data tables and plots  
✅ **File Browser** - No path typing needed  
✅ **Progress Indicators** - Know what's happening  
✅ **Data Preview** - See before processing  
✅ **Download Buttons** - Easy result export  
✅ **Error Messages** - User-friendly explanations  
✅ **Multi-tab** - Work on multiple things  
✅ **Interactive** - Adjust parameters with sliders  
✅ **Professional** - Modern, clean interface  

## System Requirements

- **Python:** 3.8 or higher
- **RAM:** 2GB minimum (4GB recommended)
- **Browser:** Chrome, Firefox, Safari, or Edge
- **Internet:** Required for initial inventory download (~50MB)

## Installation

### Option 1: Just Streamlit
```bash
pip install streamlit
```

### Option 2: All Requirements
```bash
pip install -r requirements.txt
```

This installs:
- streamlit (web interface)
- pandas (data handling)
- numpy (numerical operations)
- scipy (statistics)
- matplotlib (plotting)
- requests (data download)
- tqdm (progress bars)

## Troubleshooting

### "Module not found: streamlit"
```bash
pip install streamlit
```

### "Port 8501 is already in use"
Close existing Streamlit instance or use different port:
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Browser doesn't open
Manually go to: `http://localhost:8501`

### Inventory download fails
- Check internet connection
- Wait a minute (it's ~50MB)
- Try again - it only downloads once

### Import errors
```bash
pip install -r requirements.txt
```

## Tips for Best Experience

💡 **Use Chrome or Firefox** for best compatibility  
💡 **Keep terminal open** - that's where the server runs  
💡 **Use filled data** for parameter calculations  
💡 **Start with smaller radius** (25-50 km) for faster searches  
💡 **Check data quality** before running analyses  
💡 **Download results** before closing browser  
💡 **Bookmark the URL** if you close the tab  

## Stopping the Server

Press `Ctrl+C` in the terminal where Streamlit is running.

## Restarting

Just run the launch command again. Your previous work is saved!

## Documentation

- **Quick Start:** [STREAMLIT_QUICKSTART.md](STREAMLIT_QUICKSTART.md) - 5-minute guide
- **Full Guide:** [STREAMLIT_GUIDE.md](STREAMLIT_GUIDE.md) - Complete instructions
- **Features:** [STREAMLIT_FEATURES.md](STREAMLIT_FEATURES.md) - Detailed feature list
- **Installation:** [INSTALL_STREAMLIT.md](INSTALL_STREAMLIT.md) - Setup help
- **Comparison:** [INTERFACE_COMPARISON.md](INTERFACE_COMPARISON.md) - Compare interfaces

## Advanced Usage

### Custom Port
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Headless Mode (Remote Server)
```bash
streamlit run streamlit_app.py --server.headless true
```

### Custom Theme
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

## Compatibility

### Works With
- All existing CLI commands
- Easy Start menu projects
- Existing data files
- All file formats

### File Compatibility
All three interfaces (Streamlit, Easy Start, CLI) work with the same files and project structure. You can switch between them freely!

## Getting Help

1. Check the **Home page** in the interface
2. Read **info boxes** on each page
3. Review error messages (they're user-friendly!)
4. Check terminal output for details
5. Read the documentation files
6. Check [GETTING_STARTED.md](GETTING_STARTED.md) for general help

## Examples

### Example 1: Phoenix Analysis
1. Launch Streamlit
2. Find Stations → Select "Phoenix, AZ"
3. Set radius to 50 km
4. Click "Search Stations"
5. Download Data → Select station
6. Fill Missing Data → Click "Fill"
7. Calculate Parameters → Click "Calculate"
8. Done! Download results

### Example 2: Custom Location
1. Launch Streamlit
2. Find Stations → "Search by Coordinates" tab
3. Enter: Lat 40.7128, Lon -74.0060 (New York)
4. Set radius to 25 km
5. Click "Search Stations"
6. Follow workflow as above

### Example 3: Random Walk Analysis
1. Launch Streamlit
2. Random Walk Analysis page
3. Select filled data file
4. Set window size to 2 years
5. Check "Seasonal analysis"
6. Check "Create plots"
7. Click "Run Random Walk Analysis"
8. View results and plots inline
9. Download JSON and CSV

## What's Next?

After getting comfortable with Streamlit:
- Try the **CLI** for automation
- Use **Easy Start** for guided workflows
- Combine all three for maximum productivity!

## Support

For issues or questions:
- Check documentation files
- Review error messages
- Check terminal output
- Read [README.md](README.md) for general info

---

**Enjoy the user-friendly experience!** 🌧️📊

Made with ❤️ using [Streamlit](https://streamlit.io)
