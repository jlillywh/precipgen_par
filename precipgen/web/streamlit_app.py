#!/usr/bin/env python3
"""
PrecipGen PAR - Streamlit Web Interface
A user-friendly web interface for precipitation parameter analysis
"""

import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
import json
import math
import subprocess

# Import PrecipGen modules
from precipgen.data.find_stations import fetch_ghcn_inventory, parse_ghcn_inventory
from precipgen.data.find_ghcn_stations import read_inventory

# Page configuration
st.set_page_config(
    page_title="PrecipGen PAR",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Output directory configuration
OUTPUT_BASE_DIR = "precipgen_data"  # All output files go here

# Initialize session state
if 'project_dir' not in st.session_state:
    st.session_state.project_dir = None
if 'inventory_loaded' not in st.session_state:
    st.session_state.inventory_loaded = False
if 'inventory_df' not in st.session_state:
    st.session_state.inventory_df = None

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

def find_files_in_output(pattern):
    """Find files matching pattern in the output directory."""
    files = []
    search_dir = OUTPUT_BASE_DIR if os.path.exists(OUTPUT_BASE_DIR) else '.'
    for root, dirs, filenames in os.walk(search_dir):
        for file in filenames:
            if pattern(file):
                files.append(os.path.join(root, file))
    return files

def read_data_csv_with_metadata(file_path, nrows=None):
    """
    Read a PrecipGen data CSV file that may have metadata headers.
    
    PrecipGen data files have this format:
    - Lines 1-6: Metadata (station info)
    - Line 7: Column headers (DATE,PRCP,TMAX,TMIN)
    - Line 8+: Actual data
    
    This function skips the metadata and reads the data correctly.
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            # Find where the actual data starts (line with "DATE,")
            data_start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('DATE,'):
                    data_start = i
                    break
        
        # Read from the data start line
        if nrows:
            df = pd.read_csv(file_path, skiprows=data_start, nrows=nrows)
        else:
            df = pd.read_csv(file_path, skiprows=data_start)
        return df
    except Exception as e:
        # Fallback: try reading without skipping rows
        return pd.read_csv(file_path, nrows=nrows)

# Major cities database
MAJOR_CITIES = {
    "Phoenix, AZ": (33.4484, -112.0740),
    "Los Angeles, CA": (34.0522, -118.2437),
    "New York, NY": (40.7128, -74.0060),
    "Chicago, IL": (41.8781, -87.6298),
    "Houston, TX": (29.7604, -95.3698),
    "Denver, CO": (39.7392, -104.9903),
    "Seattle, WA": (47.6062, -122.3321),
    "Miami, FL": (25.7617, -80.1918),
    "Boston, MA": (42.3601, -71.0589),
    "San Francisco, CA": (37.7749, -122.4194),
    "Atlanta, GA": (33.7490, -84.3880),
    "Dallas, TX": (32.7767, -96.7970),
}

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def load_inventory():
    """Load or download GHCN inventory."""
    inventory_file = "ghcnd-inventory.txt"
    
    if not os.path.exists(inventory_file):
        with st.spinner("Downloading GHCN inventory (one-time download, ~50MB)..."):
            raw_data = fetch_ghcn_inventory()
            if raw_data:
                with open(inventory_file, 'w') as f:
                    f.write(raw_data)
                st.success("Inventory downloaded successfully!")
            else:
                st.error("Failed to download inventory")
                return None
    
    try:
        df = read_inventory(inventory_file)
        return df
    except Exception as e:
        st.error(f"Error loading inventory: {e}")
        return None

def find_stations_near_location(lat, lon, radius_km, min_years=20):
    """Find stations within radius of coordinates."""
    if st.session_state.inventory_df is None:
        st.session_state.inventory_df = load_inventory()
    
    if st.session_state.inventory_df is None:
        return None
    
    df = st.session_state.inventory_df.copy()
    
    # Calculate distances
    df['distance'] = df.apply(
        lambda row: calculate_distance(lat, lon, row['LAT'], row['LONG']), 
        axis=1
    )
    
    # Filter by radius
    nearby_df = df[df['distance'] <= radius_km]
    
    if nearby_df.empty:
        return None
    
    # Group by station and check requirements
    grouped = nearby_df.groupby("STATION")
    valid_stations = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(grouped)
    for idx, (station, group) in enumerate(grouped):
        progress_bar.progress((idx + 1) / total)
        status_text.text(f"Processing station {idx + 1} of {total}...")
        
        types = set(group["TYPE"])
        required_types = {"PRCP", "TMAX", "TMIN"}
        
        if not required_types.issubset(types):
            continue
        
        min_begin = group["BEGIN"].min()
        max_end = group["END"].max()
        duration = max_end - min_begin
        
        if duration >= min_years and max_end >= 2023 and min_begin <= 1900:
            station_info = {
                "STATION": station,
                "LAT": group["LAT"].iloc[0],
                "LONG": group["LONG"].iloc[0],
                "DISTANCE_KM": round(group["distance"].iloc[0], 2),
                "BEGIN": min_begin,
                "END": max_end,
                "DURATION_YEARS": duration,
                "DATA_TYPES": ",".join(sorted(types))
            }
            valid_stations.append(station_info)
    
    progress_bar.empty()
    status_text.empty()
    
    if not valid_stations:
        return None
    
    results_df = pd.DataFrame(valid_stations)
    results_df = results_df.sort_values('DISTANCE_KM')
    
    return results_df

def run_cli_command(cmd, timeout=300):
    """Run a CLI command and return the result.
    
    Args:
        cmd: Command to run
        timeout: Timeout in seconds (default 300 = 5 minutes)
    """
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds. The station may have too much data. Try a different station or increase timeout."
    except Exception as e:
        return False, "", str(e)

# Main app
def main():
    st.title("🌧️ PrecipGen PAR")
    st.markdown("### Precipitation Parameter Analysis - Web Interface")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a workflow:",
        [
            "🏠 Home",
            "📍 Find Stations",
            "📥 Download Data",
            "🔍 Data Quality Check",
            "🔧 Fill Missing Data",
            "📊 Calculate Parameters",
            "📈 Random Walk Analysis",
            "🌊 Wave Analysis"
        ]
    )
    
    # Home page
    if page == "🏠 Home":
        # Check if running on Streamlit Cloud
        is_cloud = os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_CLOUD')
        
        if is_cloud:
            st.warning("""
            ⚠️ **Running on Streamlit Cloud**
            
            - 📁 Data storage is **temporary** - files deleted on app restart
            - 💾 **Download your results** before leaving
            - 🏠 For persistent storage, [install locally](https://github.com/yourusername/precipgen_par)
            - 📊 Best for demos and quick analyses
            """)
        
        st.markdown("""
        ## Welcome to PrecipGen PAR!
        
        This tool helps you analyze precipitation data from weather stations worldwide.
        """)
        
        # Show output directory
        output_path = os.path.abspath(OUTPUT_BASE_DIR)
        st.info(f"""
        📁 **Output Directory**  
        All project files are saved to: `{output_path}`
        
        This keeps your source code separate from data files!
        """)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("📂 Open Data Folder"):
                import platform
                if platform.system() == "Windows":
                    os.startfile(output_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", output_path])
                else:  # Linux
                    subprocess.run(["xdg-open", output_path])
                st.success("Opening folder...")
        
        st.markdown("""
        ### Quick Start Guide:
        
        1. **Find Stations** - Search for weather stations near your location
        2. **Download Data** - Get historical precipitation data
        3. **Data Quality Check** - Analyze gaps and coverage
        4. **Fill Missing Data** - Interpolate missing values (recommended)
        5. **Calculate Parameters** - Compute precipitation statistics
        6. **Random Walk Analysis** - Analyze long-term variability
        7. **Wave Analysis** - Advanced seasonal pattern analysis
        
        ### Features:
        - 🌍 Search stations by city or coordinates
        - 📊 Interactive data visualization
        - 🔧 Automated data filling
        - 📈 Comprehensive statistical analysis
        - 💾 Export results in multiple formats
        
        **Get started by selecting a workflow from the sidebar!**
        """)
        
        # Show recent projects
        st.markdown("---")
        st.subheader("Recent Projects")
        
        # Look for projects in the output directory
        if os.path.exists(OUTPUT_BASE_DIR):
            project_dirs = [d for d in os.listdir(OUTPUT_BASE_DIR) if d.endswith('_precipgen') and os.path.isdir(os.path.join(OUTPUT_BASE_DIR, d))]
        else:
            project_dirs = []
        
        if project_dirs:
            cols = st.columns(3)
            for idx, proj_dir in enumerate(sorted(project_dirs)[:6]):
                with cols[idx % 3]:
                    project_name = proj_dir.replace('_precipgen', '')
                    st.info(f"📂 **{project_name}**")
                    if st.button(f"Open {project_name}", key=f"open_{proj_dir}"):
                        st.session_state.project_dir = os.path.join(OUTPUT_BASE_DIR, proj_dir)
                        st.success(f"Opened project: {project_name}")
        else:
            st.info(f"No projects yet. Create one by finding stations!\n\nAll project files will be saved to: `{os.path.abspath(OUTPUT_BASE_DIR)}`")
    
    # Find Stations page
    elif page == "📍 Find Stations":
        st.header("Find Weather Stations")
        
        tab1, tab2 = st.tabs(["Search by City", "Search by Coordinates"])
        
        with tab1:
            st.subheader("Select a Major City")
            
            city = st.selectbox("Choose a city:", list(MAJOR_CITIES.keys()))
            lat, lon = MAJOR_CITIES[city]
            
            st.info(f"📍 Coordinates: {lat}, {lon}")
            
            col1, col2 = st.columns(2)
            with col1:
                radius = st.slider("Search radius (km)", 10, 200, 50)
            with col2:
                min_years = st.slider("Minimum years of data", 10, 50, 20)
            
            project_name = st.text_input(
                "Project name:", 
                value=city.split(',')[0].lower().replace(' ', '_')
            )
            
            if st.button("🔍 Search Stations", type="primary"):
                with st.spinner(f"Searching for stations within {radius}km of {city}..."):
                    results = find_stations_near_location(lat, lon, radius, min_years)
                
                if results is not None and not results.empty:
                    st.success(f"Found {len(results)} stations!")
                    
                    # Display results
                    st.dataframe(
                        results,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Save option
                    project_dir = os.path.join(OUTPUT_BASE_DIR, f"{project_name}_precipgen")
                    os.makedirs(project_dir, exist_ok=True)
                    
                    output_file = os.path.join(project_dir, f"{project_name}_stations.csv")
                    results.to_csv(output_file, index=False)
                    
                    st.success(f"✅ Results saved to: {output_file}")
                    st.session_state.project_dir = project_dir
                    
                    # Download button
                    csv = results.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Station List",
                        data=csv,
                        file_name=f"{project_name}_stations.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No stations found matching your criteria. Try increasing the radius or reducing minimum years.")
        
        with tab2:
            st.subheader("Search by Custom Coordinates")
            
            col1, col2 = st.columns(2)
            with col1:
                custom_lat = st.number_input("Latitude", -90.0, 90.0, 40.0, format="%.4f")
            with col2:
                custom_lon = st.number_input("Longitude", -180.0, 180.0, -105.0, format="%.4f")
            
            col1, col2 = st.columns(2)
            with col1:
                radius = st.slider("Search radius (km)", 10, 200, 50, key="radius_custom")
            with col2:
                min_years = st.slider("Minimum years of data", 10, 50, 20, key="years_custom")
            
            project_name = st.text_input("Project name:", value="custom_location")
            
            if st.button("🔍 Search Stations", type="primary", key="search_custom"):
                with st.spinner(f"Searching for stations within {radius}km..."):
                    results = find_stations_near_location(custom_lat, custom_lon, radius, min_years)
                
                if results is not None and not results.empty:
                    st.success(f"Found {len(results)} stations!")
                    st.dataframe(results, use_container_width=True, hide_index=True)
                    
                    project_dir = os.path.join(OUTPUT_BASE_DIR, f"{project_name}_precipgen")
                    os.makedirs(project_dir, exist_ok=True)
                    output_file = os.path.join(project_dir, f"{project_name}_stations.csv")
                    results.to_csv(output_file, index=False)
                    
                    st.success(f"✅ Results saved to: {output_file}")
                    st.session_state.project_dir = project_dir
                else:
                    st.warning("No stations found matching your criteria.")
    
    # Download Data page
    elif page == "📥 Download Data":
        st.header("Download Station Data")
        
        # Find available station files
        station_files = find_files_in_output(lambda f: f.endswith('_stations.csv'))
        
        if not station_files:
            st.warning("No station lists found. Please find stations first!")
            if st.button("Go to Find Stations"):
                st.rerun()
        else:
            station_file = st.selectbox("Select station list:", station_files)
            
            try:
                stations_df = pd.read_csv(station_file)
                st.dataframe(stations_df, use_container_width=True, hide_index=True)
                
                station_id = st.selectbox(
                    "Select station to download:",
                    stations_df['STATION'].tolist()
                )
                
                # Show station info
                station_info = stations_df[stations_df['STATION'] == station_id].iloc[0]
                st.info(f"""
                **Station Details:**
                - **ID:** {station_id}
                - **Location:** {station_info['LAT']:.4f}, {station_info['LONG']:.4f}
                - **Distance:** {station_info['DISTANCE_KM']:.2f} km
                - **Data Range:** {station_info['BEGIN']} to {station_info['END']}
                - **Duration:** {station_info['DURATION_YEARS']} years
                
                ⏱️ Download time depends on data size. Stations with 100+ years may take 2-5 minutes.
                """)
                
                if st.button("📥 Download Station Data", type="primary"):
                    project_dir = os.path.dirname(station_file)
                    output_file = os.path.join(project_dir, f"{station_id}_data.csv")
                    
                    # Check if file already exists
                    if os.path.exists(output_file):
                        st.warning(f"⚠️ File already exists: {output_file}")
                        if not st.checkbox("Overwrite existing file?"):
                            st.info("💡 File already downloaded! You can proceed to the next step.")
                            st.stop()
                    
                    cmd = f'"{sys.executable}" cli.py download-station {station_id} -o "{output_file}"'
                    
                    # For large downloads, don't capture output to avoid hanging
                    with st.spinner(f"Downloading {station_info['DURATION_YEARS']} years of data for {station_id}... This may take 2-5 minutes."):
                        try:
                            # Run without capturing output for large datasets
                            result = subprocess.run(
                                cmd,
                                shell=True,
                                timeout=600,  # 10 minute timeout
                                stdout=subprocess.DEVNULL,  # Don't capture stdout
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            success = result.returncode == 0
                            stderr = result.stderr
                        except subprocess.TimeoutExpired:
                            success = False
                            stderr = "Download timed out after 10 minutes. The station may have too much data."
                        except Exception as e:
                            success = False
                            stderr = str(e)
                    
                    if success:
                        # Verify file was created and has data
                        if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                            file_size_kb = os.path.getsize(output_file) / 1024
                            st.success(f"✅ Data downloaded successfully!")
                            st.info(f"📁 File: `{output_file}`\n\n📊 Size: {file_size_kb:.1f} KB")
                            
                            # Show preview
                            try:
                                df = read_data_csv_with_metadata(output_file, nrows=100)
                                st.subheader("Data Preview (first 100 rows)")
                                st.dataframe(df, use_container_width=True)
                                
                                # Show data info
                                st.info(f"✅ Total rows: {len(df):,} (showing first 100)")
                            except Exception as e:
                                st.warning(f"Could not preview data: {e}")
                                st.info("Data was downloaded successfully, but preview failed. The file is ready to use!")
                        else:
                            st.error("Download may have failed - file is missing or empty")
                            if stderr:
                                st.code(stderr)
                    else:
                        st.error("Download failed!")
                        st.code(stderr)
            
            except Exception as e:
                st.error(f"Error loading station file: {e}")
    
    # Data Quality Check page
    elif page == "🔍 Data Quality Check":
        st.header("Data Quality Analysis")
        
        data_files = find_files_in_output(lambda f: f.endswith('_data.csv') or f.endswith('_filled.csv'))
        
        if not data_files:
            st.warning("No data files found. Please download station data first!")
        else:
            data_file = st.selectbox("Select data file:", data_files)
            
            if st.button("🔍 Run Gap Analysis", type="primary"):
                project_dir = os.path.dirname(data_file)
                base_name = os.path.basename(data_file).replace('.csv', '')
                output_file = os.path.join(project_dir, f"{base_name}_gap_analysis.txt")
                
                cmd = f'"{sys.executable}" cli.py gap-analysis "{data_file}" -o "{output_file}"'
                
                with st.spinner("Analyzing data quality..."):
                    success, stdout, stderr = run_cli_command(cmd)
                
                if success:
                    st.success("✅ Analysis complete!")
                    
                    # Display results
                    if os.path.exists(output_file):
                        with open(output_file, 'r') as f:
                            results = f.read()
                        st.text_area("Analysis Results:", results, height=400)
                    
                    st.code(stdout)
                else:
                    st.error("Analysis failed!")
                    st.code(stderr)
    
    # Fill Missing Data page
    elif page == "🔧 Fill Missing Data":
        st.header("Fill Missing Data")
        
        st.info("📌 Filling missing data is recommended before parameter calculation!")
        
        st.markdown("""
        **How it works:**
        - Uses smart automatic method selection
        - Tries multiple interpolation methods
        - Validates filled values for quality
        - Generates detailed report
        """)
        
        data_files = find_files_in_output(lambda f: f.endswith('_data.csv') and not f.endswith('_filled.csv'))
        
        if not data_files:
            st.warning("No data files found. Please download station data first!")
        else:
            data_file = st.selectbox("Select data file:", data_files)
            
            max_gap_days = st.number_input(
                "Maximum gap size to fill (days):", 
                min_value=1, 
                max_value=365, 
                value=365,
                help="Gaps larger than this will not be filled. Default: 365 days (1 year)"
            )
            
            if st.button("🔧 Fill Missing Data", type="primary"):
                project_dir = os.path.dirname(data_file)
                base_name = os.path.basename(data_file).replace('_data.csv', '')
                output_file = os.path.join(project_dir, f"{base_name}_filled.csv")
                
                cmd = f'"{sys.executable}" cli.py fill-data "{data_file}" -o "{output_file}" --max-gap-days {max_gap_days}'
                
                with st.spinner("Filling missing data using smart interpolation..."):
                    success, stdout, stderr = run_cli_command(cmd, timeout=300)
                
                if success:
                    st.success(f"✅ Data filled and saved to: {output_file}")
                    
                    # Show the CLI output which includes the summary
                    with st.expander("📊 Filling Summary", expanded=True):
                        st.code(stdout)
                    
                    # Check for the detailed report
                    report_file = output_file.replace('.csv', '_filling_report.json')
                    if os.path.exists(report_file):
                        st.info(f"📄 Detailed report saved to: `{report_file}`")
                    
                    # Show preview
                    if os.path.exists(output_file):
                        try:
                            df = read_data_csv_with_metadata(output_file, nrows=100)
                            st.subheader("Filled Data Preview (first 100 rows)")
                            st.dataframe(df, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Could not preview data: {e}")
                            st.info("Data was filled successfully!")
                else:
                    st.error("Fill operation failed!")
                    st.code(stderr)
    
    # Calculate Parameters page
    elif page == "📊 Calculate Parameters":
        st.header("Calculate Precipitation Parameters")
        
        data_files = find_files_in_output(lambda f: f.endswith('.csv') and ('_data.csv' in f or '_filled.csv' in f))
        
        if not data_files:
            st.warning("No data files found!")
        else:
            data_file = st.selectbox("Select data file:", data_files)
            
            st.info("💡 Use filled data for best results!")
            
            if st.button("📊 Calculate Parameters", type="primary"):
                project_dir = os.path.dirname(data_file)
                base_name = os.path.basename(data_file).replace('.csv', '')
                output_file = os.path.join(project_dir, f"{base_name}_parameters.csv")
                
                cmd = f'"{sys.executable}" cli.py params "{data_file}" -o "{output_file}"'
                
                with st.spinner("Calculating parameters..."):
                    success, stdout, stderr = run_cli_command(cmd)
                
                if success:
                    st.success(f"✅ Parameters calculated!")
                    st.code(stdout)
                    
                    if os.path.exists(output_file):
                        df = pd.read_csv(output_file)
                        st.subheader("Calculated Parameters")
                        st.dataframe(df, use_container_width=True)
                        
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Parameters",
                            csv,
                            f"{base_name}_parameters.csv",
                            "text/csv"
                        )
                else:
                    st.error("Calculation failed!")
                    st.code(stderr)
    
    # Random Walk Analysis page
    elif page == "📈 Random Walk Analysis":
        st.header("Random Walk Parameter Analysis")
        
        st.markdown("""
        This analysis calculates volatility and reversion rates for mean-reverting 
        random walk processes - the recommended approach for modeling long-term 
        precipitation parameter variability.
        """)
        
        data_files = find_files_in_output(lambda f: f.endswith('.csv') and ('_data.csv' in f or '_filled.csv' in f))
        
        if not data_files:
            st.warning("No data files found!")
        else:
            data_file = st.selectbox("Select data file:", data_files)
            
            col1, col2 = st.columns(2)
            with col1:
                window_years = st.number_input("Window size (years):", 1, 10, 2)
            with col2:
                seasonal = st.checkbox("Seasonal analysis", value=True)
            
            create_plots = st.checkbox("Create plots", value=True)
            
            if st.button("📈 Run Random Walk Analysis", type="primary"):
                st.info("This may take a few minutes...")
                
                project_dir = os.path.dirname(data_file)
                base_name = os.path.basename(data_file).replace('.csv', '')
                
                # Run analysis using Python directly
                try:
                    from random_walk_params import analyze_random_walk_parameters
                    from time_series import TimeSeries
                    
                    with st.spinner("Loading data..."):
                        ts = TimeSeries()
                        ts.load_and_preprocess(data_file)
                    
                    with st.spinner("Running analysis..."):
                        analyzer = analyze_random_walk_parameters(
                            ts, 
                            window_size=window_years,
                            seasonal_analysis=seasonal
                        )
                    
                    # Save results
                    json_file = os.path.join(project_dir, f"{base_name}_random_walk.json")
                    csv_file = os.path.join(project_dir, f"{base_name}_random_walk.csv")
                    
                    analyzer.export_results(json_file, format='json')
                    analyzer.export_results(csv_file, format='csv')
                    
                    st.success("✅ Analysis complete!")
                    
                    # Display results
                    df = pd.read_csv(csv_file)
                    st.dataframe(df, use_container_width=True)
                    
                    # Show plots if created
                    if create_plots:
                        plot_files = [
                            f"{base_name}_random_walk_evolution.png",
                            f"{base_name}_random_walk_correlations.png"
                        ]
                        
                        for plot_file in plot_files:
                            plot_path = os.path.join(project_dir, plot_file)
                            if os.path.exists(plot_path):
                                st.image(plot_path)
                
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Wave Analysis page
    elif page == "🌊 Wave Analysis":
        st.header("Advanced Wave Analysis")
        
        st.markdown("Advanced seasonal pattern analysis using wave functions.")
        
        data_files = find_files_in_output(lambda f: f.endswith('.csv') and ('_data.csv' in f or '_filled.csv' in f))
        
        if not data_files:
            st.warning("No data files found!")
        else:
            data_file = st.selectbox("Select data file:", data_files)
            
            if st.button("🌊 Run Wave Analysis", type="primary"):
                project_dir = os.path.dirname(data_file)
                base_name = os.path.basename(data_file).replace('.csv', '')
                output_file = os.path.join(project_dir, f"{base_name}_wave_analysis.json")
                
                cmd = f'"{sys.executable}" cli.py wave-analysis "{data_file}" -o "{output_file}"'
                
                with st.spinner("Running wave analysis..."):
                    success, stdout, stderr = run_cli_command(cmd)
                
                if success:
                    st.success("✅ Wave analysis complete!")
                    st.code(stdout)
                    
                    if os.path.exists(output_file):
                        with open(output_file, 'r') as f:
                            results = json.load(f)
                        
                        st.json(results)
                else:
                    st.error("Analysis failed!")
                    st.code(stderr)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info("""
    **PrecipGen PAR**  
    Precipitation Parameter Analysis  
    Version 1.0
    
    A tool for analyzing historical precipitation data 
    and calculating parameters for stochastic weather generation.
    """)

if __name__ == "__main__":
    main()
