#!/usr/bin/env python3
"""
Easy launcher for PrecipGen PAR - Perfect for beginners!

This script provides a simple menu-driven interface to run precipitation analysis.
"""

import os
import sys
import subprocess
from pathlib import Path

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
    print("3. Fill missing data (RECOMMENDED)")
    print("4. Check data quality (Gap Analysis)")
    print("5. Calculate basic parameters")
    print("6. Advanced wave analysis")
    print("7. Complete workflow (find → download → fill → analyze)")
    print("8. Help - Understanding the process")
    print("9. Exit")
    print()

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
        cmd = f'python cli.py gap-analysis "{data_file}" -o "{output_file}"'
    else:
        cmd = f'python cli.py gap-analysis "{data_file}"'
    
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("\n✅ Gap analysis completed successfully!")
        if output_file:
            print(f"Results saved to: {output_file}")
    else:
        print("\n❌ Gap analysis failed. Check the error messages above.")
    
    input("\nPress Enter to continue...")

def run_param_calculation(data_file):
    """Run parameter calculation."""
    print(f"\nCalculating parameters for: {os.path.basename(data_file)}")
    
    output_file = input("Output file name (default=parameters.csv): ").strip()
    if not output_file:
        output_file = "parameters.csv"
    
    cmd = f'python cli.py params "{data_file}" -o "{output_file}"'
    
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"\n✅ Parameters calculated successfully!")
        print(f"Results saved to: {output_file}")
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
            
            output_file = input("Save results to file (default=found_stations.csv): ").strip()
            if not output_file:
                output_file = "found_stations.csv"
            
            cmd = f'python cli.py find-stations-radius {lat} {lon} {radius} --min-years 20 -o "{output_file}"'
            print(f"\nRunning: {cmd}")
            result = subprocess.run(cmd, shell=True)
            
            if result.returncode == 0:
                print(f"\n✅ Station search completed!")
                print(f"Results saved to: {output_file}")
                print(f"Open {output_file} to see the available stations.")
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

def download_station_data():
    """Help user download data from a station."""
    print("\n" + "="*50)
    print("DOWNLOAD STATION DATA")
    print("="*50)
    print()
    
    station_id = input("Enter station ID (e.g., USW00023066): ").strip()
    if not station_id:
        print("❌ Station ID required.")
        input("Press Enter to continue...")
        return
    
    output_file = input("Output file name (default=station_data.csv): ").strip()
    if not output_file:
        output_file = "station_data.csv"
    
    cmd = f'python cli.py download-station {station_id} -o "{output_file}"'
    print(f"\nRunning: {cmd}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"\n✅ Data downloaded successfully!")
        print(f"Data saved to: {output_file}")
        print(f"You can now analyze this data with the other tools.")
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
        
        print(f"\nSearching for stations within {radius}km of ({lat}, {lon})...")
        cmd1 = f'python cli.py find-stations-radius {lat} {lon} {radius} --min-years 25 -o workflow_stations.csv'
        print(f"Running: {cmd1}")
        result1 = subprocess.run(cmd1, shell=True)
        
        if result1.returncode != 0:
            print("❌ Station search failed.")
            input("Press Enter to continue...")
            return
        
        print("✅ Stations found! Check workflow_stations.csv")
        
        # Step 2: Get best station
        station_id = input("\nEnter the station ID from the results (or press Enter to use USW00023066): ").strip()
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
        result = subprocess.run(['python', '-c', 'import pandas, numpy, scipy, matplotlib'], 
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
    print("This will use professional meteorological methods to fill gaps:")
    print("• Linear interpolation for 1-2 day gaps")
    print("• Climatological normals for 3-7 day gaps")
    print("• Analogous year method for longer gaps")
    print()
    
    output_file = input("Output file name (default=filled_data.csv): ").strip()
    if not output_file:
        output_file = "filled_data.csv"
    
    # Advanced options
    print("\nAdvanced options (press Enter for defaults):")
    max_gap = input("Maximum gap size to fill in days (default=30): ").strip()
    if not max_gap:
        max_gap = "30"
    
    similarity = input("Minimum similarity for analogous years 0-1 (default=0.7): ").strip()
    if not similarity:
        similarity = "0.7"
    
    cmd_parts = [
        f'python cli.py fill-data "{data_file}"',
        f'-o "{output_file}"',
        f'--max-gap-days {max_gap}',
        f'--min-similarity {similarity}'
    ]
    
    cmd = ' '.join(cmd_parts)
    
    print(f"\nRunning: {cmd}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"\n✅ Data filling completed successfully!")
        print(f"Filled data saved to: {output_file}")
        report_file = output_file.replace('.csv', '_filling_report.json')
        print(f"Detailed report saved to: {report_file}")
        
        print("\nRECOMMENDATION: Always run gap analysis on filled data")
        print("to verify the quality of the filling process.")
    else:
        print("\n❌ Data filling failed. Check the error messages above.")
    
    input("\nPress Enter to continue...")

def main():
    """Main menu loop."""
    print_header()
    
    # Check installation first
    if not check_installation():
        input("Press Enter to exit...")
        return
    
    while True:
        print_menu()
        
        choice = input("Enter your choice (1-9): ").strip()
        
        if choice == '1':
            find_stations()
            
        elif choice == '2':
            download_station_data()
            
        elif choice == '3':
            data_file = get_data_file()
            run_data_filling(data_file)
            
        elif choice == '4':
            data_file = get_data_file()
            run_gap_analysis(data_file)
            
        elif choice == '5':
            data_file = get_data_file()
            run_param_calculation(data_file)
            
        elif choice == '6':
            data_file = get_data_file()
            run_wave_analysis(data_file)
            
        elif choice == '7':
            data_file = get_data_file()
            run_complete_workflow(data_file)
            
        elif choice == '8':
            show_help()
            
        elif choice == '9':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please enter 1-9.")
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
