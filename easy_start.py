#!/usr/bin/env python3
"""
Easy launcher for PrecipGen PAR - Perfect for beginners!

This script provides a simple menu-driven interface to run precipitation analysis.
"""

import os
import sys
import subprocess
from pathlib import Path
import json
from datetime import datetime

# Configuration file for user preferences
CONFIG_FILE = "precipgen_config.json"

def load_config():
    """Load user configuration from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(config):
    """Save user configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save configuration: {e}")

def setup_output_directory():
    """Set up output directory based on user preference."""
    print("\n" + "="*60)
    print("📁 OUTPUT DIRECTORY SETUP")
    print("="*60)
    print()
    print("Where would you like to save your analysis files?")
    print()
    print("1. Current directory (same folder as easy_start.py)")
    print("2. Create a new 'precipgen_outputs' folder")
    print("3. Create a new 'analysis_results' folder") 
    print("4. Specify a custom folder path")
    print("5. Create session folders (precipgen_outputs/session_YYYYMMDD_HHMMSS)")
    print()
    
    while True:
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            output_dir = "."
            break
        elif choice == '2':
            output_dir = "precipgen_outputs"
            break
        elif choice == '3':
            output_dir = "analysis_results"
            break
        elif choice == '4':
            output_dir = input("Enter custom folder path: ").strip()
            if not output_dir:
                print("❌ Please enter a valid path.")
                continue
            break
        elif choice == '5':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"precipgen_outputs/session_{timestamp}"
            break
        else:
            print("❌ Please enter 1-5.")
            continue
    
    # Create directory if it doesn't exist
    if output_dir != ".":
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"✅ Created output directory: {output_dir}")
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")
            output_dir = "."
            print("Falling back to current directory.")
    
    return output_dir

def get_output_directory():
    """Get the configured output directory, setting up if needed."""
    config = load_config()
    
    # Check if user has configured output directory
    if 'output_directory' not in config:
        print("🔧 First time setup - let's configure where to save your analysis files!")
        output_dir = setup_output_directory()
        
        config['output_directory'] = output_dir
        config['setup_date'] = datetime.now().isoformat()
        save_config(config)
        
        print(f"\n✅ Configuration saved! All files will be saved to: {output_dir}")
        print("💡 You can change this anytime by selecting 'Change output directory' from the menu")
        input("\nPress Enter to continue...")
        
        return output_dir
    else:
        output_dir = config['output_directory']
        # Ensure directory still exists
        if output_dir != "." and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception:
                print(f"⚠️  Warning: Configured directory '{output_dir}' is not accessible.")
                print("Using current directory instead.")
                return "."
        return output_dir

def get_output_path(filename):
    """Get full output path for a filename."""
    output_dir = get_output_directory()
    if output_dir == ".":
        return filename
    else:
        return os.path.join(output_dir, filename)

def change_output_directory():
    """Allow user to change the output directory."""
    config = load_config()
    current_dir = config.get('output_directory', 'current directory')
    
    print(f"\n📁 Current output directory: {current_dir}")
    print("\nWould you like to change it?")
    
    if input("Change output directory? (y/n): ").lower() in ['y', 'yes']:
        new_dir = setup_output_directory()
        config['output_directory'] = new_dir
        config['last_changed'] = datetime.now().isoformat()
        save_config(config)
        
        print(f"\n✅ Output directory changed to: {new_dir}")
    
    input("Press Enter to continue...")

def show_current_config():
    """Show current configuration to user."""
    config = load_config()
    
    print("\n" + "="*50)
    print("📋 CURRENT CONFIGURATION")
    print("="*50)
    print()
    
    if config:
        output_dir = config.get('output_directory', 'Not configured')
        setup_date = config.get('setup_date', 'Unknown')
        
        print(f"Output Directory: {output_dir}")
        print(f"Setup Date: {setup_date[:10] if setup_date != 'Unknown' else 'Unknown'}")
        
        if 'last_changed' in config:
            print(f"Last Changed: {config['last_changed'][:10]}")
        
        # Show if directory exists and is writable
        if output_dir != "." and output_dir != "Not configured":
            if os.path.exists(output_dir):
                try:
                    test_file = os.path.join(output_dir, ".test_write")
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    print("Directory Status: ✅ Accessible and writable")
                except:
                    print("Directory Status: ⚠️  Exists but not writable")
            else:
                print("Directory Status: ❌ Does not exist")
    else:
        print("No configuration found. Setup will run on next operation.")
    
    print()
    input("Press Enter to continue...")

def print_header():
    print("=" * 60)
    print("       PrecipGen PAR - Precipitation Parameter Analysis")
    print("=" * 60)
    print()

def print_menu():
    print("What would you like to do?")
    print()
    print("1. Find weather stations near me")
    print("2. Download data from a station")
    print("3. About station data (view downloaded data info)")
    print("4. Fill missing data (RECOMMENDED)")
    print("5. Check data quality (Enhanced Gap Analysis)")
    print("6. Calculate basic parameters")
    print("7. Advanced wave analysis")
    print("8. Complete workflow (find → download → fill → analyze)")
    print("9. Help - Understanding the process")
    print("10. ⚙️  Change output directory")
    print("11. 📋 Show current configuration")
    print("12. Exit")
    print()
    print("💡 NEW: Option 5 includes yearly gap analysis!")
    print("   See which years have significant missing data that could")
    print("   impact statistical modeling and PrecipGen parameters.")
    print()

def select_time_series_file(operation_name):
    """Select a time series file for analysis operations with fallback to manual entry."""
    # Find available data files and let user choose
    data_files = find_station_data_files()
    
    if not data_files:
        print(f"\n❌ No station data files found in your configured directories.")
        print("Download some station data first using option 2, or use the manual file selection below.")
        print()
        return get_data_file()
    else:
        print(f"\n📁 Found station data files for {operation_name}:")
        for i, file in enumerate(data_files, 1):
            basename = os.path.basename(file)
            if '_filled.csv' in basename:
                label = f"{basename} (✅ FILLED DATA - RECOMMENDED)"
            elif '_data.csv' in basename:
                label = f"{basename} (📥 ORIGINAL DATA)"
            else:
                label = basename
            print(f"   {i}. {label}")
        print()
        
        choice = input("Select a file to analyze (enter number) or press Enter for manual file selection: ").strip()
        
        if choice and choice.isdigit():
            file_idx = int(choice) - 1
            if 0 <= file_idx < len(data_files):
                data_file = data_files[file_idx]
                basename = os.path.basename(data_file)
                if '_filled.csv' in basename:
                    print(f"✅ Selected: {basename} (filled data)")
                else:
                    print(f"✅ Selected: {basename} (original data)")
                return data_file
            else:
                print("❌ Invalid selection. Using manual file selection.")
                return get_data_file()
        else:
            return get_data_file()

def run_cli_command(cmd_args, shell=True):
    """Run a CLI command using the current Python interpreter."""
    if isinstance(cmd_args, str):
        # If it's a string command, we need to replace 'python cli.py' with the full path
        cmd = cmd_args.replace('python cli.py', f'"{sys.executable}" cli.py')
        return subprocess.run(cmd, shell=shell)
    else:
        # If it's a list, prepend the Python executable
        if cmd_args[0] == 'python':
            cmd_args[0] = sys.executable
        return subprocess.run(cmd_args, shell=shell)

def get_data_file():
    """Get data file from user with validation."""
    while True:
        print("Enter the path to your weather data CSV file:")
        print("(You can drag and drop the file here, or type the path)")
        file_path = input("> ").strip().strip('"').strip("'")
        
        if os.path.exists(file_path):
            return file_path
        else:
            print(f"Error: File '{file_path}' not found.")
            print("Please check the path and try again.")
            print()

def run_gap_analysis(data_file):
    """Run gap analysis with user-friendly options."""
    print(f"\nRunning gap analysis on: {os.path.basename(data_file)}")
    
    output_file = input("Save results to file? (Enter filename or press Enter to skip): ").strip()
    
    if output_file:
        output_path = get_output_path(output_file)
        cmd = f'"{sys.executable}" cli.py gap-analysis "{data_file}" -o "{output_path}"'
    else:
        cmd = f'"{sys.executable}" cli.py gap-analysis "{data_file}"'
    
    print(f"Running: {cmd}")
    result = run_cli_command(cmd)
    
    if result.returncode == 0:
        print("\n✅ Gap analysis completed successfully!")
        if output_file:
            print(f"Results saved to: {output_path}")
    else:
        print("\n❌ Gap analysis failed. Check the error messages above.")
    
    input("\nPress Enter to continue...")

def run_param_calculation(data_file):
    """Run parameter calculation."""
    print(f"\nCalculating parameters for: {os.path.basename(data_file)}")
    
    output_file = input("Output file name (default=parameters.csv): ").strip()
    if not output_file:
        output_file = "parameters.csv"
    
    output_path = get_output_path(output_file)
    cmd = f'"{sys.executable}" cli.py params "{data_file}" -o "{output_path}"'
    
    print(f"Running: {cmd}")
    result = run_cli_command(cmd)
    
    if result.returncode == 0:
        print(f"\n✅ Parameters calculated successfully!")
        print(f"Results saved to: {output_path}")
    else:
        print("\n❌ Parameter calculation failed. Check the error messages above.")
    
    input("\nPress Enter to continue...")

def run_wave_analysis(data_file):
    """Run wave function analysis."""
    print(f"\nRunning wave analysis on: {os.path.basename(data_file)}")
    
    window_years = input("Window size in years (default=10): ").strip()
    if not window_years:
        window_years = "10"
    
    project_years = input("Years to project into future (default=20): ").strip()
    if not project_years:
        project_years = "20"
    
    create_plots = input("Create plots? (y/n, default=y): ").lower()
    
    output_base = input("Output file base name (default=wave_analysis): ").strip()
    if not output_base:
        output_base = "wave_analysis"
    
    cmd_parts = [
        f'python cli.py wave-analysis "{data_file}"',
        f'--window-years {window_years}',
        f'--project-years {project_years}',
        f'-o "{output_base}"'
    ]
    
    if create_plots in ['', 'y', 'yes']:
        cmd_parts.append('--create-plots')
    
    cmd = ' '.join(cmd_parts)
    
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"\n✅ Wave analysis completed successfully!")
        print(f"Check for output files starting with '{output_base}'")
    else:
        print("\n❌ Wave analysis failed. Check the error messages above.")
    
    input("\nPress Enter to continue...")

def run_complete_workflow(data_file):
    """Run the complete analysis workflow."""
    print(f"\nRunning complete workflow on: {os.path.basename(data_file)}")
    print("This will run data filling, gap analysis, parameter calculation, and wave analysis.")
    
    confirm = input("Continue? (y/n): ").lower()
    if confirm not in ['y', 'yes']:
        return
    
    base_name = os.path.splitext(os.path.basename(data_file))[0]
    
    # Step 1: Data filling
    print("\n" + "="*40)
    print("Step 1: Data Filling")
    print("="*40)
    filled_file = f"{base_name}_filled.csv"
    cmd1 = f'python cli.py fill-data "{data_file}" -o "{filled_file}"'
    print(f"Running: {cmd1}")
    result1 = subprocess.run(cmd1, shell=True)
    
    # Use filled data for subsequent steps if filling was successful
    analysis_file = filled_file if result1.returncode == 0 else data_file
    
    # Step 2: Gap analysis
    print("\n" + "="*40)
    print("Step 2: Gap Analysis")
    print("="*40)
    cmd2 = f'python cli.py gap-analysis "{analysis_file}" -o "{base_name}_gaps.csv"'
    print(f"Running: {cmd2}")
    subprocess.run(cmd2, shell=True)
    
    # Step 3: Parameter calculation
    print("\n" + "="*40)
    print("Step 3: Parameter Calculation")
    print("="*40)
    cmd3 = f'python cli.py params "{analysis_file}" -o "{base_name}_parameters.csv"'
    print(f"Running: {cmd3}")
    subprocess.run(cmd3, shell=True)
    
    # Step 4: Wave analysis
    print("\n" + "="*40)
    print("Step 4: Wave Analysis")
    print("="*40)
    cmd4 = f'python cli.py wave-analysis "{analysis_file}" --create-plots --project-years 20 -o "{base_name}_wave"'
    print(f"Running: {cmd4}")
    subprocess.run(cmd4, shell=True)
    
    print("\n✅ Complete workflow finished!")
    print(f"Check for files starting with '{base_name}_' for all results.")
    if result1.returncode == 0:
        print(f"Used filled data: {filled_file}")
    input("\nPress Enter to continue...")

def find_stations():
    """Help user find weather stations."""
    print("\n" + "="*50)
    print("FIND WEATHER STATIONS")
    print("="*50)
    print()
    print("Choose how to search for stations:")
    print("1. Search by coordinates (latitude/longitude)")
    print("2. Search by climate zone")
    print("3. Get info about a specific station")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == '1':
        # Search by coordinates
        print("\nSearching by coordinates...")
        print("(You can find your coordinates from Google Maps or GPS)")
        
        try:
            lat = float(input("Enter latitude (e.g., 39.7392 for Denver): "))
            lon = float(input("Enter longitude (e.g., -104.9903 for Denver): "))
            radius = input("Search radius in km (default=50): ").strip()
            if not radius:
                radius = "50"
            
            # Suggest a location-based filename
            location_hint = input("Location name for filename (e.g., 'boulder', 'denver'): ").strip().lower()
            if location_hint:
                default_output = f"{location_hint}_stations.csv"
            else:
                default_output = "found_stations.csv"
            
            output_file = input(f"Save results to file (default={default_output}): ").strip()
            if not output_file:
                output_file = default_output
            
            output_path = get_output_path(output_file)
            cmd = f'python cli.py find-stations-radius {lat} {lon} {radius} --min-years 20 -o "{output_path}"'
            print(f"\nRunning: {cmd}")
            result = subprocess.run(cmd, shell=True)
            
            if result.returncode == 0:
                print(f"\n✅ Station search completed!")
                print(f"Results saved to: {output_path}")
                print(f"Open {output_path} to see the available stations.")
                print(f"\n💡 TIP: Use option 2 (Download data) next to select from this list!")
            else:
                print("\n❌ Station search failed.")
                
        except ValueError:
            print("❌ Invalid coordinates. Please enter numbers only.")
    
    elif choice == '2':
        # Search by climate zone
        print("\nAvailable climate zones:")
        print("- temperate: Eastern USA, Western Europe, Eastern China")
        print("- arid: Southwest USA, Western Australia, Southern Africa")
        print("- tropical: Amazon Basin, Southeast Asia, Central Africa")
        
        zone = input("\nEnter climate zone (temperate/arid/tropical): ").strip().lower()
        if zone not in ['temperate', 'arid', 'tropical']:
            print("❌ Invalid climate zone.")
            return
        
        output_file = input("Save results to file (default=climate_stations.csv): ").strip()
        if not output_file:
            output_file = "climate_stations.csv"
        
        cmd = f'python cli.py find-stations {zone} --download -o "{output_file}"'
        print(f"\nRunning: {cmd}")
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode == 0:
            print(f"\n✅ Climate zone search completed!")
            print(f"Results saved to: {output_file}")
        else:
            print("\n❌ Climate zone search failed.")
    
    elif choice == '3':
        # Get station info
        station_id = input("\nEnter station ID (e.g., USW00023066): ").strip()
        
        cmd = f'python cli.py station-info {station_id}'
        print(f"\nRunning: {cmd}")
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode != 0:
            print("\n❌ Failed to get station info.")
    
    else:
        print("❌ Invalid choice.")
    
    input("\nPress Enter to continue...")

def find_station_files():
    """Find CSV files that might contain station lists."""
    station_files = []
    common_names = [
        "found_stations.csv", "stations.csv", "climate_stations.csv", 
        "workflow_stations.csv", "boulder_stations.csv", "denver_stations.csv"
    ]
    
    # Get the user's configured output directory
    output_dir = get_output_directory()
    
    # Check for common station file names in configured output directory
    for name in common_names:
        if output_dir == ".":
            # Current directory
            if os.path.exists(name):
                station_files.append(name)
        else:
            # User's configured directory
            output_path = os.path.join(output_dir, name)
            if os.path.exists(output_path):
                station_files.append(output_path)
    
    # Check for any CSV files with "station" in the name in configured output directory
    search_dir = "." if output_dir == "." else output_dir
    if os.path.exists(search_dir):
        try:
            for file in os.listdir(search_dir):
                if file.lower().endswith('.csv') and 'station' in file.lower():
                    if output_dir == ".":
                        file_path = file
                    else:
                        file_path = os.path.join(output_dir, file)
                    
                    if file_path not in station_files:
                        station_files.append(file_path)
        except PermissionError:
            # If we can't read the directory, skip it
            pass
    
    # Also check current directory for any station files (fallback)
    try:
        for file in os.listdir('.'):
            if file.lower().endswith('.csv') and 'station' in file.lower() and file not in station_files:
                station_files.append(file)
    except PermissionError:
        pass
    
    # Legacy: Check tests directory for backwards compatibility
    tests_dir = "tests"
    if os.path.exists(tests_dir):
        try:
            for file in os.listdir(tests_dir):
                if file.lower().endswith('.csv') and 'station' in file.lower():
                    test_path = os.path.join(tests_dir, file)
                    if test_path not in station_files:
                        station_files.append(test_path)
        except PermissionError:
            pass
    
    return station_files

def parse_station_file(file_path):
    """Parse a station CSV file and return station info."""
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        
        # Common column names for station data
        id_cols = ['ID', 'STATION', 'STATION_ID', 'id', 'station', 'station_id']
        name_cols = ['NAME', 'STATION_NAME', 'name', 'station_name', 'DESCRIPTION', 'description']
        
        id_col = None
        name_col = None
        
        # Find the station ID column
        for col in id_cols:
            if col in df.columns:
                id_col = col
                break
        
        # Find the station name column
        for col in name_cols:
            if col in df.columns:
                name_col = col
                break
        
        if not id_col:
            return None
        
        stations = []
        for _, row in df.iterrows():
            station_id = str(row[id_col]).strip()
            if name_col and pd.notna(row[name_col]) and str(row[name_col]).strip() != station_id:
                station_name = str(row[name_col]).strip()
                stations.append((station_id, station_name))
            else:
                # If no name column or name is same as ID, just use the ID
                stations.append((station_id, None))
        
        return stations
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def download_station_data():
    """Help user download data from a station."""
    print("\n" + "="*50)
    print("DOWNLOAD STATION DATA")
    print("="*50)
    print()
    
    # Look for station files from step 1
    station_files = find_station_files()
    station_id = None
    
    if station_files:
        print("📋 Found station list files from previous searches:")
        for i, file in enumerate(station_files, 1):
            print(f"   {i}. {file}")
        print()
        
        choice = input("Select a station from a file (enter number) or press Enter to enter station ID manually: ").strip()
        
        if choice and choice.isdigit():
            file_idx = int(choice) - 1
            if 0 <= file_idx < len(station_files):
                selected_file = station_files[file_idx]
                print(f"\nLoading stations from: {selected_file}")
                
                stations = parse_station_file(selected_file)
                if stations:
                    print("\n📍 Available stations:")
                    print("-" * 80)
                    for i, (sid, name) in enumerate(stations[:20], 1):  # Show first 20
                        if name:
                            display_text = f"{sid} - {name[:50]}"
                        else:
                            display_text = f"{sid}"
                        print(f"{i:2d}. {display_text}")
                    
                    if len(stations) > 20:
                        print(f"    ... and {len(stations) - 20} more stations")
                    print("-" * 80)
                    
                    station_choice = input(f"\nSelect station (1-{min(20, len(stations))}) or enter station ID: ").strip()
                    
                    if station_choice.isdigit():
                        station_idx = int(station_choice) - 1
                        if 0 <= station_idx < min(20, len(stations)):
                            station_id = stations[station_idx][0]
                            station_name = stations[station_idx][1]
                            if station_name:
                                print(f"✅ Selected: {station_id} - {station_name}")
                            else:
                                print(f"✅ Selected: {station_id}")
                    else:
                        station_id = station_choice
                else:
                    print("❌ Could not parse station file.")
    
    # If no station selected from file, ask for manual entry
    if not station_id:
        station_id = input("Enter station ID (e.g., USW00023066): ").strip()
        if not station_id:
            print("❌ Station ID required.")
            input("Press Enter to continue...")
            return
    
    # Get output filename
    default_name = f"{station_id}_data.csv" if station_id else "station_data.csv"
    output_file = input(f"Output file name (default={default_name}): ").strip()
    if not output_file:
        output_file = default_name
    
    # Use configured output directory
    output_path = get_output_path(output_file)
    
    # Download the data
    cmd = f'python cli.py download-station {station_id} -o "{output_path}" --force'
    print(f"\nRunning: {cmd}")
    print(f"Saving to: {output_path}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"\n✅ Data downloaded successfully!")
        print(f"Data saved to: {output_path}")
        print(f"You can now analyze this data with the other tools.")
        
        # Ask if user wants to run gap filling next
        next_step = input("\n🔄 Would you like to fill missing data in this file? (y/n): ").lower()
        if next_step in ['y', 'yes']:
            run_data_filling(output_path)
    else:
        print("\n❌ Data download failed.")
    
    input("\nPress Enter to continue...")

def run_complete_workflow():
    """Run the complete analysis workflow from finding stations to analysis."""
    print("\n" + "="*60)
    print("COMPLETE WORKFLOW - FIND → DOWNLOAD → ANALYZE")
    print("="*60)
    print()
    print("This will help you:")
    print("1. Find weather stations near you")
    print("2. Download data from the best station")
    print("3. Analyze data quality")
    print("4. Calculate parameters")
    print("5. Run wave analysis")
    print()
    
    confirm = input("Continue with complete workflow? (y/n): ").lower()
    if confirm not in ['y', 'yes']:
        return
    
    # Step 1: Find stations
    print("\n" + "="*40)
    print("Step 1: Finding Stations")
    print("="*40)
    
    try:
        lat = float(input("Enter your latitude: "))
        lon = float(input("Enter your longitude: "))
        radius = input("Search radius in km (default=75): ").strip()
        if not radius:
            radius = "75"
        
        location_hint = input("Location name (e.g., 'denver', 'seattle'): ").strip().lower()
        station_file = f"{location_hint}_workflow_stations.csv" if location_hint else "workflow_stations.csv"
        
        print(f"\nSearching for stations within {radius}km of ({lat}, {lon})...")
        cmd1 = f'python cli.py find-stations-radius {lat} {lon} {radius} --min-years 25 -o "{station_file}"'
        print(f"Running: {cmd1}")
        result1 = subprocess.run(cmd1, shell=True)
        
        if result1.returncode != 0:
            print("❌ Station search failed.")
            input("Press Enter to continue...")
            return
        
        print(f"✅ Stations found! Check {station_file}")
        
        # Parse stations and let user choose
        stations = parse_station_file(station_file)
        if stations and len(stations) > 0:
            print(f"\n📍 Top stations found (showing first 10):")
            print("-" * 80)
            for i, (sid, name) in enumerate(stations[:10], 1):
                print(f"{i:2d}. {sid} - {name[:50]}")
            print("-" * 80)
            
            station_choice = input(f"Select station (1-{min(10, len(stations))}) or enter station ID: ").strip()
            
            if station_choice.isdigit():
                station_idx = int(station_choice) - 1
                if 0 <= station_idx < min(10, len(stations)):
                    station_id = stations[station_idx][0]
                    print(f"✅ Selected: {station_id} - {stations[station_idx][1]}")
                else:
                    station_id = "USW00023066"  # fallback
            else:
                station_id = station_choice if station_choice else "USW00023066"
        else:
            station_id = input("Enter station ID from the results (or press Enter for USW00023066): ").strip()
            if not station_id:
                station_id = "USW00023066"
        
        # Step 3: Download data
        print(f"\n" + "="*40)
        print("Step 2: Downloading Data")
        print("="*40)
        cmd2 = f'python cli.py download-station {station_id} -o workflow_data.csv'
        print(f"Running: {cmd2}")
        result2 = subprocess.run(cmd2, shell=True)
        
        if result2.returncode != 0:
            print("❌ Data download failed.")
            input("Press Enter to continue...")
            return
        
        # Step 4: Gap analysis
        print(f"\n" + "="*40)
        print("Step 3: Data Quality Check")
        print("="*40)
        cmd3 = f'python cli.py gap-analysis workflow_data.csv -o workflow_gaps'
        print(f"Running: {cmd3}")
        subprocess.run(cmd3, shell=True)
        
        # Step 5: Parameter calculation
        print(f"\n" + "="*40)
        print("Step 4: Parameter Calculation")
        print("="*40)
        cmd4 = f'python cli.py params workflow_data.csv -o workflow_parameters.csv'
        print(f"Running: {cmd4}")
        subprocess.run(cmd4, shell=True)
        
        # Step 6: Wave analysis
        print(f"\n" + "="*40)
        print("Step 5: Wave Analysis")
        print("="*40)
        cmd5 = f'python cli.py wave-analysis workflow_data.csv --create-plots --project-years 20 -o workflow_wave'
        print(f"Running: {cmd5}")
        subprocess.run(cmd5, shell=True)
        
        print("\n✅ Complete workflow finished!")
        print("Check these files for results:")
        print("- workflow_stations.csv (station search results)")
        print("- workflow_data.csv (downloaded precipitation data)")
        print("- workflow_gaps.csv (data quality analysis)")
        print("- workflow_parameters.csv (calculated parameters)")
        print("- workflow_wave_*.* (wave analysis results)")
        
    except ValueError:
        print("❌ Invalid coordinates.")
    
    input("\nPress Enter to continue...")

def show_help():
    """Show help for understanding the analysis process."""
    print("\n" + "="*60)
    print("UNDERSTANDING THE PRECIPITATION ANALYSIS PROCESS")
    print("="*60)
    print()
    print("This tool helps you analyze historical precipitation patterns")
    print("and generate parameters for long-term precipitation modeling.")
    print()
    print("THE PROCESS:")
    print()
    print("1. FIND STATIONS")
    print("   - Search for weather stations with good precipitation data")
    print("   - Look for stations with 20+ years of data and high completeness")
    print("   - Choose stations near your area of interest")
    print()
    print("2. DOWNLOAD DATA")
    print("   - Automatically download daily precipitation data from NOAA")
    print("   - Data includes dates and precipitation amounts")
    print()
    print("3. CHECK DATA QUALITY")
    print("   - Analyze gaps and missing data")
    print("   - Assess data completeness and reliability")
    print("   - Identify any problematic periods")
    print()
    print("4. CALCULATE PARAMETERS")
    print("   - Extract core precipitation parameters (PWW, PWD, alpha, beta)")
    print("   - PWW = Probability of wet day following wet day")
    print("   - PWD = Probability of wet day following dry day")
    print("   - alpha, beta = Shape parameters for precipitation amounts")
    print()
    print("5. WAVE ANALYSIS (ADVANCED)")
    print("   - Analyze how parameters change over time")
    print("   - Identify cyclic patterns and long-term trends")
    print("   - Generate projections for future parameter values")
    print()
    print("WHAT YOU GET:")
    print("- Parameter files for precipitation simulation models")
    print("- Data quality assessments")
    print("- Trend analysis and future projections")
    print("- Visualization plots showing patterns over time")
    print()
    print("COORDINATES HELP:")
    print("You can find latitude/longitude coordinates from:")
    print("- Google Maps (right-click → coordinates)")
    print("- GPS devices or smartphone apps")
    print("- Online coordinate lookup tools")
    print()
    print("EXAMPLES:")
    print("- Denver, CO: 39.7392, -104.9903")
    print("- New York, NY: 40.7128, -74.0060") 
    print("- Los Angeles, CA: 34.0522, -118.2437")
    print()
    input("Press Enter to continue...")

def check_installation():
    """Check if the tool is properly installed."""
    try:
        # Check if cli.py exists
        if not os.path.exists('cli.py'):
            print("❌ Error: cli.py not found in current directory")
            print("Make sure you're running this from the precipgen_par folder")
            return False
        
        # Check if requirements are installed
        result = subprocess.run([sys.executable, '-c', 'import pandas, numpy, scipy, matplotlib'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Error: Missing required packages")
            print("Please run: pip install -r requirements.txt")
            return False
        
        print("✅ Installation check passed!")
        return True
        
    except Exception as e:
        print(f"❌ Installation check failed: {e}")
        return False

def run_data_filling(data_file):
    """Run data filling with user-friendly options."""
    print(f"\nFilling missing data in: {os.path.basename(data_file)}")
    print("This will use smart precipitation interpolation:")
    print("• Single day gaps: Simple averaging")
    print("• Short gaps (2-3 days): Reduced linear interpolation")
    print("• Longer gaps (4+ days): Mostly zeros with occasional wet days")
    print("• Reflects reality that most days have no precipitation")
    print()
    
    # Pre-filter data to remove years with too many missing days
    print("\n📋 Data Quality Pre-Check")
    print("Before filling gaps, we'll remove years with excessive missing data.")
    
    max_missing = input("Maximum missing days per year to allow (default=90): ").strip()
    if max_missing and max_missing.isdigit():
        max_missing_days = int(max_missing)
    else:
        max_missing_days = 90
    
    prefiltered_file = pre_filter_data(data_file, max_missing_days)
    if not prefiltered_file:
        print("❌ Data pre-filtering failed.")
        input("\nPress Enter to continue...")
        return
    
    # Generate default output filename based on input file
    base_name = os.path.splitext(os.path.basename(data_file))[0]
    
    # Handle different file naming patterns
    if "_filled" in base_name:
        # Already a filled file - remove _filled suffix and add it back once
        station_id = base_name.replace("_filled", "").replace("_data", "")
        default_output = f"{station_id}_filled.csv"
    elif "_data" in base_name:
        # Original data file
        station_id = base_name.replace("_data", "")
        default_output = f"{station_id}_filled.csv"
    else:
        # Other file pattern
        default_output = f"{base_name}_filled.csv"
    
    output_file = input(f"Output file name (default={default_output}): ").strip()
    if not output_file:
        output_file = default_output
    
    # Use configured output directory
    output_path = get_output_path(output_file)
    
    # Advanced options
    print("\nAdvanced options (press Enter for defaults):")
    max_gap = input("Maximum gap size to fill in days (default=365): ").strip()
    if not max_gap:
        max_gap = "365"
    
    cmd_parts = [
        f'"{sys.executable}" cli.py fill-data "{prefiltered_file}"',
        f'-o "{output_path}"',
        f'--max-gap-days {max_gap}'
    ]
    
    cmd = ' '.join(cmd_parts)
    
    print(f"\nRunning: {cmd}")
    result = run_cli_command(cmd)
    
    # Clean up temporary pre-filtered file if it's different from original
    if prefiltered_file != data_file and os.path.exists(prefiltered_file):
        try:
            os.remove(prefiltered_file)
        except:
            pass
    
    if result.returncode == 0:
        print(f"\n✅ Data filling completed successfully!")
        print(f"Filled data saved to: {output_path}")
        report_file = output_path.replace('.csv', '_filling_report.json')
        print(f"Detailed report saved to: {report_file}")
        
        print("\n⚠️  Note for PrecipGen users:")
        print("This deterministic gap-filling method may affect precipitation statistics")
        print("needed for PrecipGen stochastic modeling (gamma parameters, wet day frequency).")
        print("Consider this when using filled data for model training.")
        
        print("\nRECOMMENDATION: Always run gap analysis on filled data")
        print("to verify the quality of the filling process.")
    else:
        print("\n❌ Data filling failed. Check the error messages above.")
    
    input("\nPress Enter to continue...")

def pre_filter_data(data_file, max_missing_days=90):
    """
    Pre-filter data to remove years with too many missing precipitation values.
    
    Args:
        data_file (str): Path to the input data file
        max_missing_days (int): Maximum missing days allowed per year (default: 90)
    
    Returns:
        str: Path to filtered file, or original file if no filtering needed
    """
    try:
        import pandas as pd
        
        print(f"🔍 Pre-filtering data to remove years with >{max_missing_days} missing days...")
        
        # Try to read the data with error handling for malformed CSV
        try:
            # First, detect if this is a GHCN file by checking the first few lines
            with open(data_file, 'r') as f:
                first_lines = [f.readline().strip() for _ in range(15)]  # Check more lines
            
            # Look for DATE column header to determine skip rows
            skip_rows = 0
            for i, line in enumerate(first_lines):
                # More specific detection - look for DATE with comma or tab separation
                if ('DATE' in line and ('PRCP' in line or 'TMAX' in line)) and (',' in line or '\t' in line):
                    skip_rows = i
                    print(f"✅ Found data header at line {i+1}: {line[:50]}...")
                    break
            
            if skip_rows > 0:
                print(f"✅ Detected GHCN format, skipping {skip_rows} metadata lines...")
                df = pd.read_csv(data_file, skiprows=skip_rows)
            else:
                # Try normal CSV reading
                df = pd.read_csv(data_file)
                
        except pd.errors.ParserError as e:
            print(f"⚠️  CSV parsing error, trying alternative methods...")
            print(f"    Error details: {str(e)[:100]}...")
            try:
                # Fallback methods for problematic files
                try:
                    # Try reading with more flexible options (pandas >= 1.3.0)
                    df = pd.read_csv(data_file, on_bad_lines='skip')
                except (TypeError, ValueError):
                    try:
                        # Fallback for older pandas versions
                        df = pd.read_csv(data_file, error_bad_lines=False, warn_bad_lines=True)
                    except:
                        try:
                            # Last resort: use python engine
                            df = pd.read_csv(data_file, engine='python', error_bad_lines=False)
                        except:
                            print("❌ Could not parse CSV file. Skipping pre-filtering.")
                            return data_file
            except Exception as parse_error:
                print(f"❌ Could not parse CSV file: {parse_error}")
                print("Skipping pre-filtering.")
                return data_file
        
        # Convert DATE to datetime with error handling
        try:
            df['DATE'] = pd.to_datetime(df['DATE'])
        except Exception as e:
            print(f"⚠️  Error parsing dates: {e}")
            print("Skipping pre-filtering due to date parsing issues.")
            return data_file
        
        # Check if PRCP column exists
        if 'PRCP' not in df.columns:
            print("⚠️  No PRCP column found. Skipping pre-filtering.")
            return data_file
        
        # Validate data has reasonable content
        if len(df) < 365:
            print("⚠️  Data file has less than 1 year of data. Skipping pre-filtering.")
            return data_file
        
        original_count = len(df)
        df['YEAR'] = df['DATE'].dt.year
        
        # Count missing days per year
        try:
            yearly_stats = df.groupby('YEAR').agg({
                'PRCP': ['count', lambda x: x.isna().sum()],
                'DATE': 'count'
            }).round(0)
            
            yearly_stats.columns = ['valid_days', 'missing_days', 'total_days']
        except Exception as e:
            print(f"⚠️  Error calculating yearly statistics: {e}")
            print("Skipping pre-filtering.")
            return data_file
        
        # Find years with too many missing days
        bad_years = yearly_stats[yearly_stats['missing_days'] > max_missing_days].index.tolist()
        
        if bad_years:
            print(f"⚠️  Found {len(bad_years)} years with >{max_missing_days} missing days:")
            for year in bad_years[:10]:  # Show first 10
                missing = yearly_stats.loc[year, 'missing_days']
                total = yearly_stats.loc[year, 'total_days']
                print(f"   {year}: {missing:.0f}/{total:.0f} days missing ({missing/total*100:.1f}%)")
            
            if len(bad_years) > 10:
                print(f"   ... and {len(bad_years) - 10} more years")
            
            # Remove bad years
            df_filtered = df[~df['YEAR'].isin(bad_years)].copy()
            df_filtered = df_filtered.drop('YEAR', axis=1)
            
            filtered_count = len(df_filtered)
            removed_count = original_count - filtered_count
            
            print(f"📊 Removed {removed_count:,} records ({removed_count/original_count*100:.1f}%)")
            print(f"📊 Kept {filtered_count:,} records from {len(df_filtered['DATE'].dt.year.unique())} years")
            
            # Save filtered data to temporary file
            base_name = os.path.splitext(data_file)[0]
            temp_file = f"{base_name}_prefiltered.csv"
            
            try:
                df_filtered.to_csv(temp_file, index=False)
                print(f"✅ Pre-filtered data saved to temporary file")
                return temp_file
            except Exception as e:
                print(f"⚠️  Could not save pre-filtered file: {e}")
                print("Proceeding with original file...")
                return data_file
        
        else:
            print(f"✅ No years found with >{max_missing_days} missing days. Data looks good!")
            return data_file
            
    except Exception as e:
        print(f"❌ Error during pre-filtering: {e}")
        print("Proceeding with original file...")
        return data_file

def find_station_data_files():
    """Find CSV files that contain downloaded station data (both original and filled)."""
    data_files = []
    output_dir = get_output_directory()
    
    # Check configured output directory
    search_dir = "." if output_dir == "." else output_dir
    if os.path.exists(search_dir):
        try:
            for file in os.listdir(search_dir):
                if file.lower().endswith('.csv') and ('_data.csv' in file.lower() or '_filled.csv' in file.lower()):
                    if output_dir == ".":
                        file_path = file
                    else:
                        file_path = os.path.join(output_dir, file)
                    data_files.append(file_path)
        except PermissionError:
            pass
    
    # Also check current directory as fallback
    try:
        for file in os.listdir('.'):
            if file.lower().endswith('.csv') and ('_data.csv' in file.lower() or '_filled.csv' in file.lower()) and file not in data_files:
                data_files.append(file)
    except PermissionError:
        pass
    
    # Check test_sean directory for files
    test_sean_dir = "test_sean"
    if os.path.exists(test_sean_dir):
        try:
            for file in os.listdir(test_sean_dir):
                if file.lower().endswith('.csv') and ('_data.csv' in file.lower() or '_filled.csv' in file.lower()):
                    test_path = os.path.join(test_sean_dir, file)
                    if test_path not in data_files:
                        data_files.append(test_path)
        except PermissionError:
            pass
    
    # Check tests directory for legacy files
    tests_dir = "tests"
    if os.path.exists(tests_dir):
        try:
            for file in os.listdir(tests_dir):
                if file.lower().endswith('.csv') and ('_data.csv' in file.lower() or '_filled.csv' in file.lower()):
                    test_path = os.path.join(tests_dir, file)
                    if test_path not in data_files:
                        data_files.append(test_path)
        except PermissionError:
            pass
    
    # Sort files with filled files appearing after their original data files
    def sort_key(file_path):
        basename = os.path.basename(file_path)
        if '_filled.csv' in basename:
            # Put filled files after original data files
            return (basename.replace('_filled.csv', '_data.csv'), 1)
        else:
            return (basename, 0)
    
    return sorted(data_files, key=sort_key)

def analyze_years_with_filled_data(file_path):
    """Analyze which years contain filled/interpolated data based on the filling report."""
    try:
        import pandas as pd
        
        # Determine the filling report path
        report_path = None
        if '_filled.csv' in file_path:
            # For filled files, look for matching filling report 
            report_path = file_path.replace('_filled.csv', '_filled_filling_report.json')
        elif '_data.csv' in file_path:
            # For original data files, look for a filled version's report
            report_path = file_path.replace('_data.csv', '_filled_filling_report.json')
        
        if not report_path or not os.path.exists(report_path):
            return None
        
        # Load the filling report
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Extract years that have filled data
        years_with_fills = set()
        if 'gap_details' in report:
            for gap in report['gap_details']:
                start_date = datetime.strptime(gap['start_date'], '%Y-%m-%d')
                end_date = datetime.strptime(gap['end_date'], '%Y-%m-%d')
                
                # Add all years that this gap spans
                current_year = start_date.year
                while current_year <= end_date.year:
                    years_with_fills.add(current_year)
                    current_year += 1
        
        # Create summary by year
        year_summary = {}
        if 'gap_details' in report:
            for gap in report['gap_details']:
                start_date = datetime.strptime(gap['start_date'], '%Y-%m-%d')
                end_date = datetime.strptime(gap['end_date'], '%Y-%m-%d')
                gap_days = gap['length_days']
                
                # Count days filled per year for this gap
                current_date = start_date
                while current_date <= end_date:
                    year = current_date.year
                    if year not in year_summary:
                        year_summary[year] = 0
                    year_summary[year] += 1
                    current_date += pd.Timedelta(days=1)
        
        return {
            'years_with_fills': sorted(list(years_with_fills)),
            'year_summary': year_summary,
            'report_exists': True
        }
        
    except Exception as e:
        return None

def analyze_station_data(file_path):
    """Analyze a station data file and return summary information."""
    try:
        import pandas as pd
        
        # Read the data file with error handling for GHCN format
        try:
            # First, detect if this is a GHCN file by checking the first few lines
            with open(file_path, 'r') as f:
                first_lines = [f.readline().strip() for _ in range(15)]  # Check more lines
            
            # Look for DATE column header to determine skip rows
            skip_rows = 0
            for i, line in enumerate(first_lines):
                # More specific detection - look for DATE with comma or tab separation
                if ('DATE' in line and ('PRCP' in line or 'TMAX' in line)) and (',' in line or '\t' in line):
                    skip_rows = i
                    break
            
            if skip_rows > 0:
                df = pd.read_csv(file_path, skiprows=skip_rows)
            else:
                # Try normal CSV reading
                df = pd.read_csv(file_path)
                
        except pd.errors.ParserError as e:
            print(f"⚠️  CSV parsing error, trying alternative methods...")
            print(f"    Error details: {str(e)[:100]}...")
            try:
                # Fallback methods for problematic files
                try:
                    df = pd.read_csv(file_path, on_bad_lines='skip')
                except (TypeError, ValueError):
                    try:
                        df = pd.read_csv(file_path, error_bad_lines=False, warn_bad_lines=True)
                    except:
                        df = pd.read_csv(file_path, engine='python', error_bad_lines=False)
            except Exception as parse_error:
                return {
                    'station_id': os.path.basename(file_path).split('_data.csv')[0] if '_data.csv' in file_path else 'Unknown',
                    'file_path': file_path,
                    'error': f'Could not parse CSV file: {parse_error}'
                }
        
        # Convert DATE column to datetime
        df['DATE'] = pd.to_datetime(df['DATE'])
        
        # Get station info from filename or data
        station_id = os.path.basename(file_path).split('_data.csv')[0]
        
        # Basic information
        start_date = df['DATE'].min()
        end_date = df['DATE'].max()
        total_days = len(df)
        
        # Analyze years with filled data
        filled_data_info = analyze_years_with_filled_data(file_path)
        
        # Precipitation analysis (assuming PRCP column exists)
        if 'PRCP' in df.columns:
            # Remove missing values for calculations
            precip_data = df['PRCP'].dropna()
            total_valid_days = len(precip_data)
            coverage = (total_valid_days / total_days * 100) if total_days > 0 else 0
            
            # Annual calculations
            years_span = (end_date - start_date).days / 365.25
            
            # Precipitation statistics
            total_precip = precip_data.sum()
            avg_annual_precip = total_precip / years_span if years_span > 0 else 0
            
            # Wet/dry day analysis
            wet_days = (precip_data > 0).sum()
            dry_days = (precip_data == 0).sum()
            avg_annual_wet_days = wet_days / years_span if years_span > 0 else 0
            avg_annual_dry_days = dry_days / years_span if years_span > 0 else 0
            
            # Maximum values
            max_daily_precip = precip_data.max()
            
            # Maximum consecutive dry days
            def max_consecutive_dry_days(series):
                dry_streaks = []
                current_streak = 0
                for value in series:
                    if value == 0:
                        current_streak += 1
                    else:
                        if current_streak > 0:
                            dry_streaks.append(current_streak)
                        current_streak = 0
                if current_streak > 0:
                    dry_streaks.append(current_streak)
                return max(dry_streaks) if dry_streaks else 0
            
            max_consecutive_dry = max_consecutive_dry_days(precip_data)
            
            result = {
                'station_id': station_id,
                'file_path': file_path,
                'start_date': start_date.strftime('%Y'),
                'end_date': end_date.strftime('%Y'),
                'coverage': round(coverage, 1),
                'avg_annual_precip': round(avg_annual_precip, 1),
                'avg_annual_wet_days': round(avg_annual_wet_days),
                'avg_annual_dry_days': round(avg_annual_dry_days),
                'max_daily_precip': round(max_daily_precip, 1),
                'max_consecutive_dry': max_consecutive_dry,
                'total_days': total_days,
                'valid_days': total_valid_days,
                'filled_data_info': filled_data_info
            }
            
            return result
        else:
            return {
                'station_id': station_id,
                'file_path': file_path,
                'start_date': start_date.strftime('%Y'),
                'end_date': end_date.strftime('%Y'),
                'coverage': 0,
                'error': 'No PRCP column found',
                'filled_data_info': filled_data_info
            }
            
    except Exception as e:
        return {
            'station_id': os.path.basename(file_path).split('_data.csv')[0] if '_data.csv' in file_path else 'Unknown',
            'file_path': file_path,
            'error': str(e)
        }

def show_station_data_info():
    """Show comprehensive information about downloaded station data files."""
    print("\n" + "="*50)
    print("ABOUT STATION DATA")
    print("="*50)
    print()
    
    # Find data files
    data_files = find_station_data_files()
    
    if not data_files:
        print("❌ No station data files found.")
        print("Download some station data first using option 2.")
        input("\nPress Enter to continue...")
        return
    
    print("📁 Found downloaded station data files:")
    for i, file in enumerate(data_files, 1):
        basename = os.path.basename(file)
        if '_filled.csv' in basename:
            label = f"{basename} (✅ FILLED DATA)"
        elif '_data.csv' in basename:
            label = f"{basename} (� ORIGINAL DATA)"
        else:
            label = basename
        print(f"   {i}. {label}")
    print()
    
    choice = input("Select a file to analyze (enter number): ").strip()
    
    if choice.isdigit():
        file_idx = int(choice) - 1
        if 0 <= file_idx < len(data_files):
            selected_file = data_files[file_idx]
            print(f"\n🔍 Analyzing: {os.path.basename(selected_file)}")
            print("Please wait...")
            
            # Use the comprehensive about_station function
            about_station(selected_file)
            
        else:
            print("❌ Invalid selection.")
    else:
        print("❌ Invalid selection.")
    
    input("\nPress Enter to continue...")

def about_station(data_file, station_id=None, station_name=None, lat=None, lon=None):
    """
    Print a comprehensive summary about a weather station's data.
    """
    try:
        import pandas as pd
        
        # Load data with error handling for different CSV formats
        df = None
        try:
            # Try to detect GHCN format first
            with open(data_file, 'r') as f:
                first_lines = [f.readline().strip() for _ in range(15)]
            
            skip_rows = 0
            for i, line in enumerate(first_lines):
                if ('DATE' in line and ('PRCP' in line or 'TMAX' in line)) and (',' in line or '\t' in line):
                    skip_rows = i
                    break
            
            if skip_rows > 0:
                df = pd.read_csv(data_file, skiprows=skip_rows)
            else:
                df = pd.read_csv(data_file)
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            return

        # Parse dates and prepare data
        df['DATE'] = pd.to_datetime(df['DATE'])
        precip_col = 'PRCP' if 'PRCP' in df.columns else df.columns[-1]
        df = df.sort_values('DATE')
        df['year'] = df['DATE'].dt.year
        df['month'] = df['DATE'].dt.month

        # Station metadata (try to infer if not provided)
        if not station_id:
            station_id = os.path.basename(data_file).split('_')[0]
        if not station_name:
            station_name = station_id
        lat = lat if lat is not None else "Unknown"
        lon = lon if lon is not None else "Unknown"

        # Date range and coverage
        start_date = df['DATE'].min().strftime('%Y-%m-%d')
        end_date = df['DATE'].max().strftime('%Y-%m-%d')
        total_days = len(df)
        missing_records = df[precip_col].isna().sum()
        coverage_pct = 100 * (1 - missing_records / total_days) if total_days > 0 else 0

        # Annual summaries
        annual_data = []
        for year in df['year'].unique():
            year_df = df[df['year'] == year]
            year_precip = year_df[precip_col].dropna()
            if len(year_precip) > 0:
                annual_total = year_precip.sum()
                wet_days = (year_precip > 0).sum()
                dry_days = (year_precip == 0).sum()
                
                # Calculate max wet/dry runs for this year
                max_wet_run = 0
                max_dry_run = 0
                current_wet = 0
                current_dry = 0
                
                for val in year_precip:
                    if val > 0:
                        current_wet += 1
                        current_dry = 0
                        max_wet_run = max(max_wet_run, current_wet)
                    else:
                        current_dry += 1
                        current_wet = 0
                        max_dry_run = max(max_dry_run, current_dry)
                
                annual_data.append({
                    'year': year,
                    'total': annual_total,
                    'wet_days': wet_days,
                    'dry_days': dry_days,
                    'max_wet_run': max_wet_run,
                    'max_dry_run': max_dry_run
                })

        if not annual_data:
            print("❌ No valid precipitation data found.")
            return

        # Calculate overall statistics
        annual_totals = [d['total'] for d in annual_data]
        annual_wet_days = [d['wet_days'] for d in annual_data]
        annual_dry_days = [d['dry_days'] for d in annual_data]
        annual_wet_runs = [d['max_wet_run'] for d in annual_data]
        annual_dry_runs = [d['max_dry_run'] for d in annual_data]

        min_annual = min(annual_totals)
        max_annual = max(annual_totals)
        avg_annual = sum(annual_totals) / len(annual_totals)
        avg_wet_days = sum(annual_wet_days) / len(annual_wet_days)
        avg_dry_days = sum(annual_dry_days) / len(annual_dry_days)
        avg_max_wet_run = sum(annual_wet_runs) / len(annual_wet_runs)
        avg_max_dry_run = sum(annual_dry_runs) / len(annual_dry_runs)

        # Max daily precip
        max_daily = df[precip_col].max()

        # Monthly totals averaged across all years
        # First get monthly totals for each year, then average those totals
        monthly_totals_by_year = df.groupby(['year', 'month'])[precip_col].sum().unstack(fill_value=0)
        monthly_avg = monthly_totals_by_year.mean(axis=0)  # Average the monthly totals across years

        # Longest missing run
        is_missing = df[precip_col].isna()
        max_missing_run = 0
        current_run = 0
        for val in is_missing:
            if val:
                current_run += 1
                max_missing_run = max(max_missing_run, current_run)
            else:
                current_run = 0

        # Years with >60 missing days
        missing_by_year = df.groupby('year')[precip_col].apply(lambda x: x.isna().sum())
        bad_years = missing_by_year[missing_by_year > 60]

        # Data quality rating
        if coverage_pct > 98 and bad_years.empty:
            quality = "EXCELLENT"
        elif coverage_pct > 95 and len(bad_years) <= 2:
            quality = "GOOD"
        elif coverage_pct > 90:
            quality = "FAIR"
        else:
            quality = "POOR"

        # Print comprehensive report
        print("="*70)
        print(f"Station ID: {station_id}")
        print(f"Station Name: {station_name}")
        print(f"Location: {lat}, {lon}")
        print(f"Date Range: {start_date} to {end_date}")
        print(f"Overall Coverage: {coverage_pct:.1f}%")
        print(f"Data saved in: {os.path.relpath(data_file)}")
        
        print("\n" + "-"*70)
        print("OVERALL SUMMARY:")
        print(f"  Average annual total precip: {avg_annual:.1f} mm")
        print(f"  Min annual total precip: {min_annual:.1f} mm")
        print(f"  Max annual total precip: {max_annual:.1f} mm")
        print(f"  Average annual wet days: {avg_wet_days:.1f}")
        print(f"  Average annual dry days: {avg_dry_days:.1f}")
        print(f"  Average annual max wet run: {avg_max_wet_run:.1f} days")
        print(f"  Average annual max dry run: {avg_max_dry_run:.1f} days")
        print(f"  Maximum daily precip total: {max_daily:.1f} mm")
        
        print("\n" + "-"*70)
        print("MONTHLY AVERAGE PRECIPITATION (all years):")
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for m in range(1, 13):
            print(f"  {month_names[m-1]}: {monthly_avg.get(m, 0):.1f} mm")
        
        print("\n" + "-"*70)
        print("MISSING DATA ANALYSIS:")
        print(f"  Total missing records: {missing_records:,}")
        print(f"  Longest run of missing records: {max_missing_run} days")
        
        print("\n" + "-"*70)
        print("YEARS WITH >60 MISSING RECORDS:")
        if not bad_years.empty:
            for year, miss in bad_years.items():
                total_year_days = len(df[df['year'] == year])
                pct_missing = (miss / total_year_days) * 100 if total_year_days > 0 else 0
                print(f"  {year}: {miss} missing days ({pct_missing:.1f}%)")
        else:
            print("  ✅ None - all years have ≤60 missing days")
        
        print("\n" + "-"*70)
        print(f"OVERALL DATA QUALITY RATING: {quality}")
        
        if quality == "EXCELLENT":
            print("  ✅ This data is ideal for precipitation analysis and modeling")
        elif quality == "GOOD":
            print("  ✅ This data is suitable for most precipitation analyses")
        elif quality == "FAIR":
            print("  ⚠️  This data may need gap filling for reliable analysis")
        else:
            print("  ❌ This data requires significant preprocessing before use")
        
        print("="*70)

    except Exception as e:
        print(f"❌ Error analyzing station data: {e}")

def main():
    """Main menu loop."""
    print_header()
    
    # Check installation first
    if not check_installation():
        input("Press Enter to exit...")
        return
    
    # Ensure output directory is set up
    get_output_directory()
    
    while True:
        print_menu()
        
        choice = input("Enter your choice (1-12): ").strip()
        
        if choice == '1':
            find_stations()
            
        elif choice == '2':
            download_station_data()
            
        elif choice == '3':
            show_station_data_info()
            
        elif choice == '4':
            data_file = select_time_series_file("data filling")
            if data_file:
                run_data_filling(data_file)
            
        elif choice == '5':
            data_file = select_time_series_file("gap analysis")
            if data_file:
                run_gap_analysis(data_file)
            
        elif choice == '6':
            data_file = select_time_series_file("parameter calculation")
            if data_file:
                run_param_calculation(data_file)
            
        elif choice == '7':
            data_file = select_time_series_file("wave analysis")
            if data_file:
                run_wave_analysis(data_file)
            
        elif choice == '8':
            data_file = select_time_series_file("complete workflow")
            if data_file:
                run_complete_workflow(data_file)
            
        elif choice == '9':
            show_help()
            
        elif choice == '10':
            change_output_directory()
            
        elif choice == '11':
            show_current_config()
            
        elif choice == '12' or choice.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
            
        else:
            print(f"Invalid choice '{choice}'. Please enter 1-12.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your installation and try again.")
        input("Press Enter to exit...")
