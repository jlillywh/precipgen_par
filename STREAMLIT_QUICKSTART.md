# Streamlit Quick Start - 5 Minutes to Your First Analysis

## Step 1: Install (30 seconds)

```bash
pip install streamlit
```

## Step 2: Launch (10 seconds)

**Windows:**
```cmd
run_streamlit.bat
```

**Mac/Linux:**
```bash
./run_streamlit.sh
```

**Or manually:**
```bash
streamlit run streamlit_app.py
```

Your browser opens automatically to `http://localhost:8501`

## Step 3: Find Stations (2 minutes)

1. Click **"📍 Find Stations"** in the sidebar
2. Select **"Search by City"** tab
3. Choose a city from the dropdown (e.g., "Phoenix, AZ")
4. Adjust the search radius slider (try 50 km)
5. Click **"🔍 Search Stations"** button
6. Wait for results (first time downloads inventory ~50MB)
7. See the table of nearby stations
8. Results automatically saved to project folder

## Step 4: Download Data (1 minute)

1. Click **"📥 Download Data"** in the sidebar
2. Select your station list from dropdown
3. Choose a station from the table
4. Click **"📥 Download Station Data"** button
5. See data preview appear below

## Step 5: Analyze (1 minute)

1. Click **"🔧 Fill Missing Data"** in the sidebar
2. Select your data file
3. Click **"🔧 Fill Missing Data"** button
4. Click **"📊 Calculate Parameters"** in the sidebar
5. Select the filled data file
6. Click **"📊 Calculate Parameters"** button
7. Download results with the download button

## Done! 🎉

You've just:
- ✅ Found weather stations near a location
- ✅ Downloaded historical precipitation data
- ✅ Filled missing values
- ✅ Calculated precipitation parameters

All in about 5 minutes with just a few clicks!

## What You Get

Your project folder now contains:
```
phoenix_precipgen/
├── phoenix_stations.csv          # Station search results
├── USW00023183_data.csv          # Downloaded data
├── USW00023183_filled.csv        # Filled data
└── USW00023183_parameters.csv    # Calculated parameters
```

## Next Steps

### Run Advanced Analyses

**Random Walk Analysis:**
1. Click **"📈 Random Walk Analysis"**
2. Select filled data file
3. Adjust window size (default: 2 years)
4. Check "Create plots"
5. Click **"📈 Run Random Walk Analysis"**
6. View results and plots inline

**Wave Analysis:**
1. Click **"🌊 Wave Analysis"**
2. Select filled data file
3. Click **"🌊 Run Wave Analysis"**
4. View JSON results

### Try Different Locations

1. Go back to **"📍 Find Stations"**
2. Try the **"Search by Coordinates"** tab
3. Enter custom latitude/longitude
4. Repeat the workflow

### Check Data Quality

1. Click **"🔍 Data Quality Check"**
2. Select any data file
3. Click **"🔍 Run Gap Analysis"**
4. Review coverage statistics

## Tips for Success

💡 **Use filled data** for parameter calculations  
💡 **Start with smaller radius** (25-50 km) for faster searches  
💡 **Check data quality** before running analyses  
💡 **Download results** using the download buttons  
💡 **Keep terminal open** - that's where the server runs  

## Troubleshooting

### "Module not found: streamlit"
```bash
pip install streamlit
```

### "Port already in use"
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Browser doesn't open
Manually go to: `http://localhost:8501`

### Inventory download fails
- Check internet connection
- Wait a minute (it's a large file)
- Try again - it only downloads once

## Stopping the Server

Press `Ctrl+C` in the terminal where Streamlit is running.

## Restarting

Just run the launch command again:
```bash
streamlit run streamlit_app.py
```

Your previous work is saved in project folders!

## Learn More

- **Full Guide:** [STREAMLIT_GUIDE.md](STREAMLIT_GUIDE.md)
- **Features:** [STREAMLIT_FEATURES.md](STREAMLIT_FEATURES.md)
- **Comparison:** [INTERFACE_COMPARISON.md](INTERFACE_COMPARISON.md)
- **Installation:** [INSTALL_STREAMLIT.md](INSTALL_STREAMLIT.md)

## Need Help?

- Check the **Home page** in the interface for quick start guide
- Read the **info boxes** on each page for tips
- Review error messages - they're user-friendly!
- Check the terminal output for detailed logs

---

**Enjoy the user-friendly experience!** 🌧️📊
