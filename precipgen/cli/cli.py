#!/usr/bin/env python3
"""
PrecipGen Parameter CLI Tool

A command-line interface for precipitation parameter generation and analysis.
This tool provides various functions for analyzing precipitation time series data.
"""

import argparse
import sys
import os
import math
from pathlib import Path
import pandas as pd
import numpy as np

# Import precipgen modules
from precipgen.core.time_series import TimeSeries
from precipgen.core.pgpar import calculate_params, calculate_window_params
from precipgen.core.pgpar_ext import calculate_ext_params
from precipgen.core.pgpar_wave import PrecipGenPARWave, analyze_precipgen_parameter_waves
from precipgen.core.random_walk_params import RandomWalkParameterAnalyzer, analyze_random_walk_parameters
from precipgen.data.ghcn_data import GHCNData
from precipgen.data.find_ghcn_stations import filter_stations_by_climate_zone, read_inventory, get_climate_zones
from precipgen.data.find_stations import fetch_ghcn_inventory, parse_ghcn_inventory, fetch_station_data, analyze_data_format
from precipgen.data.gap_analyzer import analyze_gaps
from precipgen.data.data_filler import fill_precipitation_data

# Import project-aware output functions
from easy_start import get_output_path as get_project_output_path, get_project_aware_output_path


def get_output_path(filename, input_file=None):
    """
    Get project-aware output path for CLI operations.
    
    Args:
        filename (str): The filename or path
        input_file (str): Optional input file to determine project context
    
    Returns:
        str: Full path with project-aware output directory
    """
    if filename is None:
        return None
    
    # Convert to Path object for easier manipulation
    path = Path(filename)
    
    # If it's just a filename (no directory), use project-aware output
    if len(path.parts) == 1:
        if input_file:
            # Try to use project-aware path based on input file location
            try:
                return get_project_aware_output_path(input_file, filename)
            except:
                # Fall back to global output path
                return get_project_output_path(filename)
        else:
            # Use global output path
            return get_project_output_path(filename)
    
    # If it's already a full path, use as-is
    return str(path)


def load_data(file_path, start_year=None, end_year=None):
    """Load and optionally trim precipitation data."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    
    print(f"Loading data from: {file_path}")
    timeseries = TimeSeries()
    timeseries.load_and_preprocess(file_path)
    
    if start_year and end_year:
        print(f"Trimming data to years {start_year}-{end_year}")
        timeseries.trim(start_year, end_year)
    
    return timeseries


def cmd_params(args):
    """Calculate basic precipitation parameters (PWW, PWD, ALPHA, BETA) for each month."""
    timeseries = load_data(args.input, args.start_year, args.end_year)
    
    print("Calculating monthly parameters...")
    params = calculate_params(timeseries.get_data())
    
    print("\nMonthly Parameters:")
    print(params)
    
    if args.output:
        output_path = get_output_path(args.output, args.input)
        params.to_csv(output_path, index=True)
        print(f"\nParameters saved to: {output_path}")


def cmd_window_params(args):
    """Calculate window-based parameter statistics (volatility and reversion rates)."""
    timeseries = load_data(args.input, args.start_year, args.end_year)
    
    print(f"Calculating window parameters using {args.window_years}-year windows...")
    volatilities, reversion_rates = calculate_window_params(timeseries.get_data(), args.window_years)
    
    print(f"\nVolatilities [PWW, PWD, ALPHA, BETA]: {volatilities}")
    print(f"Reversion Rates [PWW, PWD, ALPHA, BETA]: {reversion_rates}")
    
    if args.output:
        import pandas as pd
        results_df = pd.DataFrame({
            'Parameter': ['PWW', 'PWD', 'ALPHA', 'BETA'],
            'Volatility': volatilities,
            'Reversion_Rate': reversion_rates
        })
        output_path = get_output_path(args.output, args.input)
        results_df.to_csv(output_path, index=False)
        print(f"\nWindow parameters saved to: {output_path}")


def cmd_ext_params(args):
    """Calculate extended parameters with distribution fitting."""
    timeseries = load_data(args.input, args.start_year, args.end_year)
    
    print(f"Calculating extended parameters using {args.window_years}-year windows...")
    
    # Prepare output path for ext_params function
    output_path_for_ext = get_output_path(args.output, args.input) if args.output else None
    ext_params = calculate_ext_params(timeseries.get_data(), args.window_years, output_path_for_ext)
    
    print("\nExtended Parameters (Distribution fits):")
    for param_name, param_data in ext_params.items():
        print(f"\n{param_name}:")
        print(param_data)
    
    if args.output:
        # Save each parameter's distribution data to separate files
        output_path = get_output_path(args.output, args.input)
        base_name = Path(output_path).stem
        base_dir = Path(output_path).parent
        
        for param_name, param_data in ext_params.items():
            output_file = base_dir / f"{base_name}_{param_name}.csv"
            param_data.to_csv(output_file, index=True)
            print(f"{param_name} parameters saved to: {output_file}")


def cmd_info(args):
    """Display information about the precipitation dataset."""
    timeseries = load_data(args.input)
    data = timeseries.get_data()
    
    print("\nDataset Information:")
    print(f"Start Date: {data.index.min()}")
    print(f"End Date: {data.index.max()}")
    print(f"Total Days: {len(data)}")
    print(f"Date Range: {(data.index.max() - data.index.min()).days} days")
    
    # Basic precipitation statistics
    prcp_data = data['PRCP']
    wet_days = prcp_data[prcp_data > 0]
    
    print(f"\nPrecipitation Statistics:")
    print(f"Total Wet Days: {len(wet_days)}")
    print(f"Total Dry Days: {len(prcp_data) - len(wet_days)}")
    print(f"Wet Day Frequency: {len(wet_days) / len(prcp_data):.3f}")
    print(f"Mean Precipitation (wet days): {wet_days.mean():.3f}")
    print(f"Max Precipitation: {prcp_data.max():.3f}")
    print(f"Total Precipitation: {prcp_data.sum():.3f}")


def cmd_test(args):
    """Run the test suite."""
    import unittest
    
    print("Running test suite...")
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Ran {result.testsRun} test(s)")
    if result.wasSuccessful():
        print("All tests passed!")
        return 0
    else:
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        return 1


def cmd_ghcn_info(args):
    """Display information about GHCN stations and climate zones."""
    # Load GHCN station inventory
    inventory = read_inventory(args.inventory)
    
    print(f"\nLoaded {len(inventory)} stations from inventory.")
    
    # Filter stations by climate zone if specified
    if args.climate_zone:
        filtered_stations = filter_stations_by_climate_zone(inventory, args.climate_zone)
        print(f"Filtered stations by climate zone '{args.climate_zone}': {len(filtered_stations)} stations")
    else:
        filtered_stations = inventory
    
    # Display basic information about the stations
    for station in filtered_stations:
        print(f"Station ID: {station['station_id']}, Location: {station['latitude']}, {station['longitude']}")
    
    # Optionally, fetch and display data for the first station
    if args.fetch_data and filtered_stations:
        first_station = filtered_stations[0]
        print(f"\nFetching data for station {first_station['station_id']}...")
        data = fetch_station_data(first_station['station_id'], args.start_year, args.end_year)
        print(data.head())


def cmd_fetch_inventory(args):
    """Fetch GHCN station inventory from the NOAA website."""
    print(f"Fetching GHCN station inventory from NOAA...")
    inventory = fetch_ghcn_inventory()
    
    # Save inventory to file
    if args.output:
        import pandas as pd
        df = pd.DataFrame(inventory)
        df.to_csv(args.output, index=False)
        print(f"Inventory saved to {args.output}")
    else:
        print(f"Fetched {len(inventory)} stations.")


def cmd_parse_inventory(args):
    """Parse a local GHCN inventory file."""
    if not os.path.exists(args.input):
        print(f"Error: File '{args.input}' not found.")
        sys.exit(1)
    
    print(f"Parsing GHCN inventory file: {args.input}")
    stations = parse_ghcn_inventory(args.input)
    
    print(f"Parsed {len(stations)} stations.")
    
    # Optionally, filter by climate zone
    if args.climate_zone:
        stations = filter_stations_by_climate_zone(stations, args.climate_zone)
        print(f"Filtered to {len(stations)} stations in climate zone '{args.climate_zone}'")
    
    # Display station information
    for station in stations:
        print(f"Station ID: {station['station_id']}, Location: {station['latitude']}, {station['longitude']}")


def cmd_analyze_format(args):
    """Analyze the data format of a GHCN station."""
    if not os.path.exists(args.input):
        print(f"Error: File '{args.input}' not found.")
        sys.exit(1)
    
    print(f"Analyzing data format for station file: {args.input}")
    analyze_data_format(args.input)


def cmd_find_stations(args):
    """Find GHCN stations by climate zone with quality criteria."""
    print(f"Searching for stations in {args.climate_zone} climate zones...")
    
    # Check if inventory file exists, if not download it
    if not os.path.exists(args.inventory_file):
        print(f"Inventory file not found at {args.inventory_file}")
        if args.download:
            print("Downloading GHCN inventory...")
            raw_data = fetch_ghcn_inventory()
            if raw_data:
                with open(args.inventory_file, 'w') as f:
                    f.write(raw_data)
                print(f"Inventory saved to {args.inventory_file}")
            else:
                print("Failed to download inventory")
                return 1
        else:
            print("Use --download flag to automatically download the inventory file")
            return 1
    
    # Read and process inventory
    try:
        df = read_inventory(args.inventory_file)
        print(f"Loaded {len(df)} records from inventory")
        
        valid_stations = filter_stations_by_climate_zone(df, args.climate_zone)
        
        print(f"\nFound {len(valid_stations)} stations matching criteria:")
        print("- Located in specified climate zone")
        print("- Has PRCP, TMAX, TMIN data")
        print("- At least 90 years of data")
        print("- Data ends after 2023")
        print("- Starts on or before 1900")
        print("- >95% data coverage")
        
        if valid_stations:
            # Display results
            results_df = pd.DataFrame(valid_stations)
            print("\nStation Results:")
            print(results_df.to_string(index=False))
            
            if args.output:
                results_df.to_csv(args.output, index=False)
                print(f"\nResults saved to: {args.output}")
        else:
            print("No stations found matching the criteria")
            
    except Exception as e:
        print(f"Error processing inventory: {e}")
        return 1


def cmd_download_station(args):
    """Download data for a specific GHCN station."""
    print(f"Downloading data for station: {args.station_id}")
    
    try:
        ghcn_data = GHCNData()
        ghcn_data.fetch(args.station_id)
        if ghcn_data.data is not None:
            print(f"Successfully downloaded data for {args.station_id}")
            print(f"Station: {ghcn_data.station_name}")
            print(f"Location: {ghcn_data.latitude:.4f}, {ghcn_data.longitude:.4f}")
            print(f"Date Range: {ghcn_data.start_date} to {ghcn_data.end_date}")
            print(f"Coverage: {ghcn_data.coverage:.1f}%")
            
            if args.output:
                output_file = args.output
            else:
                output_file = f"{args.station_id}_data.csv"
            
            # Check if file exists and confirm overwrite
            if os.path.exists(output_file) and not args.force:
                print(f"\nWARNING: File '{output_file}' already exists!")
                while True:
                    response = input("Do you want to overwrite it? (y/n): ").strip().lower()
                    if response in ['y', 'yes']:
                        break
                    elif response in ['n', 'no']:
                        print("Operation cancelled. Data not saved.")
                        return 0
                    else:
                        print("Please enter 'y' for yes or 'n' for no.")
            elif os.path.exists(output_file) and args.force:
                print(f"Overwriting existing file: {output_file}")
            
            # Save data
            ghcn_data.save_to_csv(output_file)
            print(f"Data saved to: {output_file}")
              # Show enhanced precipitation statistics
            if hasattr(ghcn_data, 'data') and 'PRCP' in ghcn_data.data.columns:
                df = ghcn_data.data.copy()
                df['DATE'] = pd.to_datetime(df['DATE'])
                df['YEAR'] = df['DATE'].dt.year
                
                # Calculate annual statistics
                annual_stats = df.groupby('YEAR').agg({
                    'PRCP': ['sum', 'count']
                }).round(1)
                annual_stats.columns = ['annual_precip', 'total_days']
                
                # Calculate wet/dry days per year
                annual_wet_dry = df.groupby('YEAR')['PRCP'].apply(
                    lambda x: pd.Series({
                        'wet_days': (x > 0).sum(),
                        'dry_days': (x == 0).sum()
                    })
                ).unstack()
                
                # Calculate maximum consecutive dry days
                def max_consecutive_dry_days(precip_series):
                    dry_streaks = []
                    current_streak = 0
                    for value in precip_series:
                        if value == 0:
                            current_streak += 1
                        else:
                            if current_streak > 0:
                                dry_streaks.append(current_streak)
                            current_streak = 0
                    if current_streak > 0:  # Handle streak at end
                        dry_streaks.append(current_streak)
                    return max(dry_streaks) if dry_streaks else 0
                
                max_dry_streak = max_consecutive_dry_days(df['PRCP'])
                max_daily_precip = df['PRCP'].max()
                
                print(f"\nPrecipitation Summary:")
                print(f"Average annual precipitation: {annual_stats['annual_precip'].mean():.1f} mm")
                print(f"Average annual wet days: {annual_wet_dry['wet_days'].mean():.0f} days")
                print(f"Average annual dry days: {annual_wet_dry['dry_days'].mean():.0f} days")
                print(f"Maximum daily precipitation: {max_daily_precip:.1f} mm")
                print(f"Maximum consecutive dry days: {max_dry_streak} days")
        else:
            print(f"Failed to download data for station {args.station_id}")
            return 1
            
    except Exception as e:
        print(f"Error downloading station data: {e}")
        return 1


def cmd_list_climate_zones(args):
    """List available climate zones and their coordinate ranges."""
    print("Available Climate Zones:\n")
    
    zones = {
        "arid": "Hot, dry climates with low precipitation",
        "tropical": "Hot, humid climates near the equator", 
        "temperate": "Moderate climates with distinct seasons"
    }
    
    for zone_type, description in zones.items():
        print(f"{zone_type.upper()}:")
        print(f"  Description: {description}")
        
        climate_areas = get_climate_zones(zone_type)
        if climate_areas:
            print("  Geographic areas:")
            for i, area in enumerate(climate_areas, 1):
                lat_range = area["lat_range"]
                long_range = area["long_range"] 
                print(f"    {i}. Latitude: {lat_range[0]} to {lat_range[1]}, "
                      f"Longitude: {long_range[0]} to {long_range[1]}")
        print()


def cmd_station_info(args):
    """Get information about a specific GHCN station without downloading full dataset."""
    print(f"Getting information for station: {args.station_id}")
    
    try:
        # Try to get basic info first
        raw_data = fetch_station_data(args.station_id)
        if raw_data:
            format_info = analyze_data_format(raw_data, args.station_id)
            print(f"Data format: {format_info}")
            
            # Try to load with GHCNData for more details
            ghcn_data = GHCNData()
            ghcn_data.fetch(args.station_id)
            
            if ghcn_data.data is not None:
                print(f"Station: {ghcn_data.station_name}")
                print(f"Station ID: {ghcn_data.station_id}")
                print(f"Location: {ghcn_data.latitude:.4f}, {ghcn_data.longitude:.4f}")
                print(f"Date Range: {ghcn_data.start_date} to {ghcn_data.end_date}")
                print(f"Coverage: {ghcn_data.coverage:.1f}%")
                
                # Show available data types
                if hasattr(ghcn_data.data, 'columns'):
                    data_types = [col for col in ghcn_data.data.columns if col not in ['DATE']]
                    print(f"Available data types: {', '.join(data_types)}")
            else:
                print(f"Could not retrieve detailed information for station {args.station_id}")
        else:
            print(f"Station {args.station_id} not found or not accessible")
            return 1
            
    except Exception as e:
        print(f"Error getting station information: {e}")
        return 1


def cmd_gap_analysis(args):
    """Perform gap analysis on precipitation dataset to identify missing data patterns."""
    from gap_analyzer import analyze_yearly_gaps
    
    timeseries = load_data(args.input, args.start_year, args.end_year)
    data = timeseries.get_data()
    
    print(f"Performing gap analysis on: {args.input}")
    if args.start_year and args.end_year:
        print(f"Analysis period: {args.start_year}-{args.end_year}")
    
    # Analyze gaps for precipitation data
    print(f"Gap threshold: {args.gap_threshold} day(s)")
    print("=" * 60)
    
    results = analyze_gaps(data, args.column, args.gap_threshold)
    
    if results is None:
        print("Gap analysis failed - see error messages above")
        return 1
    
    # Display comprehensive results
    print(f"\nGAP ANALYSIS SUMMARY")
    print(f"=" * 60)
    print(f"Analysis Period: {results['min_date'].strftime('%Y-%m-%d')} to {results['max_date'].strftime('%Y-%m-%d')}")
    print(f"Total Days in Range: {results['total_days']:,}")
    print(f"Total Missing Days: {results['total_missing_days']:,}")
    
    if results['total_days'] > 0:
        coverage_pct = ((results['total_days'] - results['total_missing_days']) / results['total_days']) * 100
        print(f"Data Coverage: {coverage_pct:.2f}%")
    
    print(f"\nGAP DISTRIBUTION")
    print(f"=" * 60)
    print(f"Short Gaps (<={args.gap_threshold} days): {results['short_gap_count']}")
    print(f"Long Gaps (>{args.gap_threshold} days): {results['long_gap_count']}")
    
    # Display long gaps details if any
    if results['long_gap_count'] > 0:
        print(f"\nLONG GAPS DETAILS")
        print(f"=" * 60)
        long_gaps_df = results['long_gaps']
        
        for idx, gap in long_gaps_df.iterrows():
            start_str = gap['start_date'].strftime('%Y-%m-%d')
            end_str = gap['end_date'].strftime('%Y-%m-%d')
            duration = gap['duration']
            
            print(f"Gap #{idx + 1}:")
            print(f"  Period: {start_str} to {end_str}")
            print(f"  Duration: {duration} days")
            print(f"  Years affected: {duration / 365.25:.1f}")
            print()
    
    # Data quality assessment
    print(f"DATA QUALITY ASSESSMENT")
    print(f"=" * 60)
    
    if coverage_pct >= 95:
        quality_status = "EXCELLENT"
        recommendation = "Data is suitable for parameter calculation"
    elif coverage_pct >= 90:
        quality_status = "GOOD"
        recommendation = "Data is generally suitable, consider gap filling for long gaps"
    elif coverage_pct >= 80:
        quality_status = "FAIR"
        recommendation = "Consider gap filling or use with caution"
    else:
        quality_status = "POOR"
        recommendation = "Gap filling strongly recommended before analysis"
    
    print(f"Quality Status: {quality_status}")
    print(f"Recommendation: {recommendation}")
    
    # Parameter calculation recommendations
    if results['long_gap_count'] == 0:
        print(f"Ready for parameter calculation - no significant gaps detected")
    elif results['long_gap_count'] <= 3 and coverage_pct >= 90:
        print(f"WARNING: Proceed with caution - {results['long_gap_count']} long gap(s) detected")
    else:
        print(f"WARNING: Consider data preprocessing before parameter calculation")
    
    # Add yearly gap analysis
    print(f"\nYEARLY GAP ANALYSIS")
    print(f"=" * 60)
    
    yearly_results = analyze_yearly_gaps(data, args.column)
    if yearly_results:
        yearly_stats = yearly_results['summary_statistics']
        significant_years = yearly_results['years_with_significant_gaps']
        
        print(f"Years analyzed: {yearly_stats['total_years_analyzed']}")
        print(f"Average missing days per year: {yearly_stats['avg_missing_days_per_year']}")
        print(f"Maximum missing days in any year: {yearly_stats['max_missing_days_any_year']}")
        print(f"Maximum consecutive missing: {yearly_stats['max_consecutive_missing_any_year']} days")
        print(f"Years with no gaps: {yearly_stats['years_with_no_gaps']}")
        
        if significant_years:
            print(f"\nWARNING: YEARS WITH SIGNIFICANT GAPS (>{yearly_stats['significant_threshold']} days):")
            print(f"   Found {len(significant_years)} years that may impact statistical modeling")
            print(f"   {'Year':<8} {'Missing':<8} {'Max Run':<8} {'% Missing':<10}")
            print(f"   {'-'*8} {'-'*8} {'-'*8} {'-'*10}")
            
            for year, data in list(significant_years.items())[:10]:  # Show top 10
                print(f"   {year:<8} {data['total_missing_days']:<8} {data['max_consecutive_missing']:<8} {data['percent_missing']:<10}%")
            
            if len(significant_years) > 10:
                print(f"   ... and {len(significant_years) - 10} more years")
            
            print(f"\n   NOTE: Consider these years carefully for statistical modeling")
            print(f"   NOTE: Filled data in these years may bias PrecipGen parameters")
        else:
            print(f"No years with >{yearly_stats['significant_threshold']} missing days found")
            print(f"All years appear suitable for statistical analysis")
    else:
        print("Yearly analysis could not be completed")
    
      # Save detailed results if requested
    if args.output:
        output_path = get_output_path(args.output, args.input)
        
        # Create a comprehensive results file
        summary_data = {
            'Metric': [
                'Analysis Period Start', 'Analysis Period End', 'Total Days',
                'Missing Days', 'Data Coverage (%)', 'Short Gaps', 'Long Gaps',
                'Years Analyzed', 'Years with Significant Gaps', 
                'Avg Missing Days/Year', 'Max Missing Days (Any Year)',
                'Max Consecutive Missing Days'
            ],
            'Value': [
                results['min_date'].strftime('%Y-%m-%d'),
                results['max_date'].strftime('%Y-%m-%d'),
                results['total_days'],
                results['total_missing_days'],
                f"{coverage_pct:.2f}",
                results['short_gap_count'],
                results['long_gap_count'],
                yearly_stats.get('total_years_analyzed', 'N/A'),
                yearly_stats.get('years_with_significant_gaps', 'N/A'),
                yearly_stats.get('avg_missing_days_per_year', 'N/A'),
                yearly_stats.get('max_missing_days_any_year', 'N/A'),
                yearly_stats.get('max_consecutive_missing_any_year', 'N/A')
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Save summary
        base_name = Path(output_path).stem
        base_dir = Path(output_path).parent
        
        summary_file = base_dir / f"{base_name}_gap_analysis_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"\nGap analysis summary saved to: {summary_file}")
        
        # Save long gaps details if any exist
        if results['long_gap_count'] > 0:
            gaps_file = base_dir / f"{base_name}_long_gaps.csv"
            results['long_gaps'].to_csv(gaps_file, index=False)
            print(f"Long gaps details saved to: {gaps_file}")
            
        # Save yearly analysis details if significant years exist
        if yearly_results and yearly_results['years_with_significant_gaps']:
            yearly_data = []
            for year, data in yearly_results['years_with_significant_gaps'].items():
                yearly_data.append({
                    'Year': year,
                    'Total_Missing_Days': data['total_missing_days'],
                    'Max_Consecutive_Missing': data['max_consecutive_missing'],
                    'Total_Days_in_Year': data['total_days_in_year'],
                    'Percent_Missing': data['percent_missing']
                })
            
            if yearly_data:
                yearly_df = pd.DataFrame(yearly_data)
                yearly_file = base_dir / f"{base_name}_significant_years.csv"
                yearly_df.to_csv(yearly_file, index=False)
                print(f"Significant years analysis saved to: {yearly_file}")
    
    print(f"\n" + "=" * 60)
    return 0 if coverage_pct >= 80 else 1  # Return error code if coverage is poor


def cmd_find_stations_radius(args):
    """Find GHCN stations within a radius of specified coordinates."""
    import math
    
    print(f"Searching for stations within {args.radius} km of ({args.latitude}, {args.longitude})")
    
    # Check if inventory file exists, if not download it
    if not os.path.exists(args.inventory_file):
        print(f"Inventory file not found at {args.inventory_file}")
        if args.download:
            print("Downloading GHCN inventory...")
            raw_data = fetch_ghcn_inventory()
            if raw_data:
                with open(args.inventory_file, 'w') as f:
                    f.write(raw_data)
                print(f"Inventory saved to {args.inventory_file}")
            else:
                print("Failed to download inventory")
                return 1
        else:
            print("Use --download flag to automatically download the inventory file")
            return 1
    
    # Read inventory
    try:
        df = read_inventory(args.inventory_file)
        print(f"Loaded {len(df)} records from inventory")
        
        # Calculate distance for each station
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
        
        # Filter by distance and data requirements
        target_lat, target_lon = args.latitude, args.longitude
        
        # Add distance column
        df['distance'] = df.apply(lambda row: calculate_distance(
            target_lat, target_lon, row['LAT'], row['LONG']), axis=1)
        
        # Filter by radius
        nearby_df = df[df['distance'] <= args.radius]
        print(f"Found {len(nearby_df)} stations within {args.radius} km")
        
        if nearby_df.empty:
            print("No stations found in the specified radius")
            return 1
        
        # Group by station and check data requirements
        grouped = nearby_df.groupby("STATION")
        valid_stations = []
        
        print("Filtering stations by data quality criteria...")
        from tqdm import tqdm
        
        for station, group in tqdm(grouped, desc="Processing stations"):
            types = set(group["TYPE"])
            
            # Check for required data types
            required_types = set(args.data_types.split(','))
            if not required_types.issubset(types):
                continue
                
            min_begin = group["BEGIN"].min()
            max_end = group["END"].max()
            duration = max_end - min_begin
            
            # Check duration and date range requirements
            if (duration >= args.min_years and 
                max_end >= args.end_after and 
                min_begin <= args.start_before):
                
                station_info = {
                    "STATION": station,
                    "LAT": group["LAT"].iloc[0],
                    "LONG": group["LONG"].iloc[0],
                    "DISTANCE_KM": group["distance"].iloc[0],
                    "BEGIN": min_begin,
                    "END": max_end,
                    "DURATION_YEARS": duration,
                    "DATA_TYPES": ",".join(sorted(types))
                }
                valid_stations.append(station_info)
        
        if not valid_stations:
            print("No stations found meeting the data quality criteria")
            return 1
        
        # Sort by distance
        valid_stations.sort(key=lambda x: x['DISTANCE_KM'])
        
        print(f"\nFound {len(valid_stations)} stations meeting criteria:")
        print("- Located within specified radius")
        print(f"- Has required data types: {args.data_types}")
        print(f"- At least {args.min_years} years of data")
        print(f"- Data ends after {args.end_after}")
        print(f"- Starts on or before {args.start_before}")
          # Display results
        results_df = pd.DataFrame(valid_stations)
        print(f"\nStation Results (sorted by distance):")
        print(results_df.to_string(index=False))
        
        if args.output:
            output_path = get_output_path(args.output)
            results_df.to_csv(output_path, index=False)
            print(f"\nResults saved to: {output_path}")
            
        return 0
        
    except Exception as e:
        print(f"Error processing inventory: {e}")
        return 1


def cmd_batch_gap_analysis(args):
    """Perform gap analysis on multiple stations and create a wellness summary."""
    print(f"Performing batch gap analysis on stations from: {args.stations_file}")
    
    try:
        # Read stations file
        stations_df = pd.read_csv(args.stations_file)
        
        if 'STATION' not in stations_df.columns:
            print("Error: Stations file must have a 'STATION' column")
            return 1
        
        station_ids = stations_df['STATION'].tolist()
        print(f"Found {len(station_ids)} stations to analyze")
        
        wellness_results = []
        download_failed = []
        
        for i, station_id in enumerate(station_ids, 1):
            print(f"\n{'='*60}")
            print(f"ANALYZING STATION {i}/{len(station_ids)}: {station_id}")
            print(f"{'='*60}")
            
            try:
                # Download station data
                print(f"Downloading data for {station_id}...")
                ghcn_data = GHCNData()
                ghcn_data.fetch(station_id)
                
                if ghcn_data.data is None:
                    print(f"Failed to download data for {station_id}")
                    download_failed.append(station_id)
                    continue
                
                # Prepare data for gap analysis
                data = ghcn_data.data.copy()
                if 'DATE' in data.columns:
                    data['DATE'] = pd.to_datetime(data['DATE'])
                    data.set_index('DATE', inplace=True)
                
                # Apply date filtering if specified
                if args.start_year or args.end_year:
                    if args.start_year:
                        start_date = f"{args.start_year}-01-01"
                        data = data[data.index >= start_date]
                    if args.end_year:
                        end_date = f"{args.end_year}-12-31"
                        data = data[data.index <= end_date]
                
                if data.empty:
                    print(f"No data available for {station_id} in specified date range")
                    continue
                
                # Perform gap analysis
                print(f"Analyzing gaps...")
                gap_results = analyze_gaps(data, args.column, args.gap_threshold)
                
                if gap_results is None:
                    print(f"Gap analysis failed for {station_id}")
                    continue
                
                # Calculate wellness metrics
                coverage_pct = ((gap_results['total_days'] - gap_results['total_missing_days']) 
                               / gap_results['total_days']) * 100 if gap_results['total_days'] > 0 else 0
                
                # Determine quality rating
                if coverage_pct >= 95:
                    quality_rating = "EXCELLENT"
                    quality_score = 4
                elif coverage_pct >= 90:
                    quality_rating = "GOOD"
                    quality_score = 3
                elif coverage_pct >= 80:
                    quality_rating = "FAIR"
                    quality_score = 2
                else:
                    quality_rating = "POOR"
                    quality_score = 1
                
                # Get station metadata
                station_info = stations_df[stations_df['STATION'] == station_id].iloc[0] if station_id in stations_df['STATION'].values else {}
                
                # Compile wellness results
                wellness_data = {
                    'STATION_ID': station_id,
                    'STATION_NAME': getattr(ghcn_data, 'station_name', 'Unknown'),
                    'LATITUDE': getattr(ghcn_data, 'latitude', station_info.get('LAT', 'Unknown')),
                    'LONGITUDE': getattr(ghcn_data, 'longitude', station_info.get('LONG', 'Unknown')),
                    'DISTANCE_KM': station_info.get('DISTANCE_KM', 'Unknown'),
                    'ANALYSIS_START': gap_results['min_date'].strftime('%Y-%m-%d'),
                    'ANALYSIS_END': gap_results['max_date'].strftime('%Y-%m-%d'),
                    'TOTAL_DAYS': gap_results['total_days'],
                    'MISSING_DAYS': gap_results['total_missing_days'],
                    'COVERAGE_PCT': round(coverage_pct, 2),
                    'SHORT_GAPS': gap_results['short_gap_count'],
                    'LONG_GAPS': gap_results['long_gap_count'],
                    'QUALITY_RATING': quality_rating,
                    'QUALITY_SCORE': quality_score,
                    'LONGEST_GAP_DAYS': gap_results['long_gaps']['duration'].max() if not gap_results['long_gaps'].empty else 0
                }
                
                wellness_results.append(wellness_data)
                
                # Print summary for this station
                print(f"Analysis complete:")
                print(f"   Period: {wellness_data['ANALYSIS_START']} to {wellness_data['ANALYSIS_END']}")
                print(f"   Coverage: {wellness_data['COVERAGE_PCT']}%")
                print(f"   Quality: {wellness_data['QUALITY_RATING']}")
                print(f"   Long gaps: {wellness_data['LONG_GAPS']}")
                
            except Exception as e:
                print(f"Error analyzing {station_id}: {e}")
                continue
        
        # Create wellness summary
        if wellness_results:
            wellness_df = pd.DataFrame(wellness_results)
            
            # Sort by quality score (descending) then by coverage percentage (descending)
            wellness_df = wellness_df.sort_values(['QUALITY_SCORE', 'COVERAGE_PCT'], ascending=[False, False])
            
            print(f"\n{'='*80}")
            print(f"BATCH GAP ANALYSIS SUMMARY")
            print(f"{'='*80}")
            print(f"Total stations analyzed: {len(wellness_results)}")
            print(f"Download failures: {len(download_failed)}")
            
            # Quality distribution
            quality_counts = wellness_df['QUALITY_RATING'].value_counts()
            print(f"\nQuality Distribution:")
            for quality, count in quality_counts.items():
                print(f"  {quality}: {count} stations")
            
            # Best stations
            print(f"\nTOP STATIONS BY QUALITY:")
            top_stations = wellness_df.head(min(10, len(wellness_df)))
            
            display_cols = ['STATION_ID', 'STATION_NAME', 'DISTANCE_KM', 'COVERAGE_PCT', 'QUALITY_RATING', 'LONG_GAPS']
            print(top_stations[display_cols].to_string(index=False))
              # Save results
            if args.output:
                output_path = get_output_path(args.output)
                wellness_df.to_csv(output_path, index=False)
                print(f"\nWellness summary saved to: {output_path}")
                
                # Also save failed downloads list
                if download_failed:
                    failed_file = output_path.replace('.csv', '_failed.txt')
                    with open(failed_file, 'w') as f:
                        for station in download_failed:
                            f.write(f"{station}\n")
                    print(f"Failed downloads list saved to: {failed_file}")
            
            print(f"\n{'='*80}")
            return 0
        else:
            print("No successful analyses completed")
            return 1
            
    except Exception as e:
        print(f"Error in batch gap analysis: {e}")
        return 1


def cmd_wave_analysis(args):
    """Analyze temporal evolution of PrecipGen parameters using wave function decomposition."""
    timeseries = load_data(args.input, args.start_year, args.end_year)
    
    print(f"Running parameter wave analysis with {args.window_years}-year windows...")
    print(f"Window overlap: {args.overlap:.1%}")
    print(f"Max wave components: {args.num_components}")
    
    # Initialize analyzer
    analyzer = PrecipGenPARWave(
        timeseries, 
        window_size=args.window_years, 
        overlap=args.overlap,
        min_data_threshold=args.min_data_threshold
    )
    
    # Extract parameter history
    print("\nExtracting parameter history...")
    param_history = analyzer.extract_parameter_history()
    print(f"Extracted parameters for {len(param_history)} time windows")
    
    # Analyze wave components
    print("\nAnalyzing wave components...")
    wave_components = analyzer.analyze_parameter_waves(num_components=args.num_components)
    
    print("Wave components found:")
    for param, components in wave_components.items():
        n_comp = len(components['components'])
        print(f"  {param}: {n_comp} components")
    
    # Fit parameter evolution
    print("\nFitting parameter evolution...")
    fitted_params = analyzer.fit_parameter_evolution()
    
    # Display summary
    print("\nAnalysis Summary:")
    print("-" * 50)
    for param in ['PWW', 'PWD', 'alpha', 'beta']:
        if param in fitted_params:
            fitted = fitted_params[param]
            trend_slope = fitted['trend']['slope']
            dominant_period = fitted['wave_summary']['dominant_period']
            total_amplitude = fitted['wave_summary']['total_amplitude']
            
            print(f"\n{param}:")
            print(f"  Trend: {trend_slope:+.6f} per year")
            if dominant_period and dominant_period < 200:
                print(f"  Dominant period: {dominant_period:.1f} years")
            print(f"  Total wave amplitude: {total_amplitude:.4f}")
    
    # Save outputs
    if args.output:
        output_base = get_output_path(args.output, args.input)
        output_dir = Path(output_base).parent
        output_stem = Path(output_base).stem
        
        # Create output directory
        output_dir.mkdir(exist_ok=True)
        
        # Save wave parameters (JSON)
        json_file = output_dir / f"{output_stem}_wave_params.json"
        analyzer.export_wave_parameters(str(json_file), format='json')
        print(f"\nWave parameters saved to: {json_file}")
        
        # Save component summary (CSV)
        csv_file = output_dir / f"{output_stem}_components.csv"
        analyzer.export_wave_parameters(str(csv_file), format='csv')
        print(f"Component summary saved to: {csv_file}")
        
        # Save parameter history
        history_file = output_dir / f"{output_stem}_history.csv"
        param_history.to_csv(str(history_file), index=False)
        print(f"Parameter history saved to: {history_file}")
        
        # Generate synthetic future parameters if requested
        if args.project_years > 0:
            data = timeseries.get_data()
            end_year = data.index.year.max()
            future_years = np.arange(end_year + 1, end_year + args.project_years + 1)
            
            synthetic_params = analyzer.generate_synthetic_parameters(future_years)
            synthetic_file = output_dir / f"{output_stem}_projections.csv"
            synthetic_params.to_csv(str(synthetic_file), index=False)
            print(f"Future projections saved to: {synthetic_file}")
        
        # Create plots if requested
        if args.create_plots:
            evolution_plot = output_dir / f"{output_stem}_evolution.png"
            analyzer.plot_parameter_evolution(save_path=str(evolution_plot))
            print(f"Evolution plot saved to: {evolution_plot}")
            
            components_plot = output_dir / f"{output_stem}_components.png"
            analyzer.plot_wave_components(save_path=str(components_plot))
            print(f"Components plot saved to: {components_plot}")
    
    print("\nWave analysis complete!")
    return 0


def cmd_fill_data(args):
    """Fill missing values in precipitation data using smart interpolation."""
    print(f"Filling missing data in {args.input_file}...")
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    # Fill missing data
    report = fill_precipitation_data(
        input_file=args.input_file,
        output_file=args.output,
        date_col=args.date_col,
        precip_col=args.precip_col,
        max_fill_gap_days=args.max_gap_days
    )
    
    # Print summary
    print("\nData Filling Summary:")
    print("-" * 40)
    print(f"Original missing values: {report['summary']['original_missing_values']}")
    print(f"Final missing values: {report['summary']['final_missing_values']}")
    print(f"Values filled: {report['summary']['values_filled']}")
    print(f"Success rate: {report['summary']['fill_success_rate']:.1f}%")
    
    print(f"\nMethods used:")
    for method, count in report['methods_used'].items():
        if count > 0:
            print(f"  {method.replace('_', ' ').title()}: {count}")
    
    print(f"\nQuality metrics:")
    validation = report['validation_results']
    print(f"  Statistical quality: {'Good' if validation['quality_good'] else 'Review needed'}")
    print(f"  Negative values: {validation['filled_data_negative']}")
    print(f"  Extreme values: {validation['filled_data_extreme']}")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    print(f"\nFilled data saved to: {args.output}")
    report_file = args.output.replace('.csv', '_filling_report.json')
    print(f"Detailed report saved to: {report_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='PrecipGen Parameter CLI Tool',        formatter_class=argparse.RawDescriptionHelpFormatter,        epilog="""
Examples:
  %(prog)s gap-analysis input.csv --gap-threshold 14
  %(prog)s params input.csv -o params.csv
  %(prog)s window input.csv --window-years 3 -o window_stats.csv
  %(prog)s ext-params input.csv --start-year 1950 --end-year 2020
  %(prog)s wave-analysis input.csv --window-years 10 --create-plots -o wave_results
  %(prog)s info input.csv
  %(prog)s test
  
  # Station discovery and data download
  %(prog)s list-zones
  %(prog)s find-stations temperate --download -o temperate_stations.csv
  %(prog)s download-station USW00023066 -o denver_data.csv
  %(prog)s station-info USW00023066
  
  # Fill missing data (Note: May affect statistics for PrecipGen modeling)
  %(prog)s fill-data data.csv -o filled_data.csv

WARNING: The fill-data command uses deterministic gap filling that may
affect precipitation statistics needed for PrecipGen stochastic modeling.
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Common arguments for data processing commands
    def add_common_args(parser):
        parser.add_argument('input', help='Input precipitation data file (CSV)')
        parser.add_argument('-o', '--output', help='Output file path')
        parser.add_argument('--start-year', type=int, help='Start year for data trimming')
        parser.add_argument('--end-year', type=int, help='End year for data trimming')
    
    # Parameters command
    params_parser = subparsers.add_parser('params', help='Calculate monthly precipitation parameters')
    add_common_args(params_parser)
    params_parser.set_defaults(func=cmd_params)
    
    # Window parameters command
    window_parser = subparsers.add_parser('window', help='Calculate window-based parameter statistics')
    add_common_args(window_parser)
    window_parser.add_argument('--window-years', type=int, default=2, 
                              help='Number of years per window (default: 2)')
    window_parser.set_defaults(func=cmd_window_params)
      # Extended parameters command
    ext_parser = subparsers.add_parser('ext-params', help='Calculate extended parameters with distribution fitting')
    add_common_args(ext_parser)
    ext_parser.add_argument('--window-years', type=int, default=3,
                           help='Number of years per window (default: 3)')
    ext_parser.set_defaults(func=cmd_ext_params)
    
    # Wave analysis command
    wave_parser = subparsers.add_parser('wave-analysis', help='Analyze temporal evolution of parameters using wave functions')
    add_common_args(wave_parser)
    wave_parser.add_argument('--window-years', type=int, default=10,
                           help='Number of years per window (default: 10)')
    wave_parser.add_argument('--overlap', type=float, default=0.5,
                           help='Window overlap fraction (default: 0.5)')
    wave_parser.add_argument('--num-components', type=int, default=5,
                           help='Number of wave components to extract (default: 5)')
    wave_parser.add_argument('--min-data-threshold', type=float, default=0.8,
                           help='Minimum data coverage required per window (default: 0.8)')
    wave_parser.add_argument('--project-years', type=int, default=0,
                           help='Number of years to project into future (default: 0)')
    wave_parser.add_argument('--create-plots', action='store_true',
                           help='Create visualization plots')
    wave_parser.set_defaults(func=cmd_wave_analysis)
      # Info command
    info_parser = subparsers.add_parser('info', help='Display dataset information')
    info_parser.add_argument('input', help='Input precipitation data file (CSV)')
    info_parser.set_defaults(func=cmd_info)
    
    # Gap analysis command
    gap_parser = subparsers.add_parser('gap-analysis', help='Analyze missing data gaps in precipitation dataset')
    gap_parser.add_argument('input', help='Input precipitation data file (CSV)')
    gap_parser.add_argument('-o', '--output', help='Output file prefix for gap analysis results')
    gap_parser.add_argument('--start-year', type=int, help='Start year for data trimming')
    gap_parser.add_argument('--end-year', type=int, help='End year for data trimming')
    gap_parser.add_argument('--column', default='PRCP', help='Column to analyze for gaps (default: PRCP)')
    gap_parser.add_argument('--gap-threshold', type=int, default=7, 
                           help='Threshold for short vs long gaps in days (default: 7)')
    gap_parser.set_defaults(func=cmd_gap_analysis)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run the test suite')
    test_parser.set_defaults(func=cmd_test)
    
    # GHCN info command
    ghcn_info_parser = subparsers.add_parser('ghcn-info', help='Display GHCN station information')
    ghcn_info_parser.add_argument('--inventory', help='Path to GHCN station inventory file')
    ghcn_info_parser.add_argument('--climate-zone', help='Filter stations by climate zone')
    ghcn_info_parser.add_argument('--start-year', type=int, help='Start year for data fetching')
    ghcn_info_parser.add_argument('--end-year', type=int, help='End year for data fetching')
    ghcn_info_parser.add_argument('--fetch-data', action='store_true', help='Fetch station data')
    ghcn_info_parser.set_defaults(func=cmd_ghcn_info)
    
    # Fetch inventory command
    fetch_inventory_parser = subparsers.add_parser('fetch-inventory', help='Fetch GHCN station inventory')
    fetch_inventory_parser.add_argument('-o', '--output', help='Output file path for inventory')
    fetch_inventory_parser.set_defaults(func=cmd_fetch_inventory)
    
    # Parse inventory command
    parse_inventory_parser = subparsers.add_parser('parse-inventory', help='Parse local GHCN inventory file')
    parse_inventory_parser.add_argument('input', help='Input GHCN inventory file (CSV)')
    parse_inventory_parser.add_argument('--climate-zone', help='Filter stations by climate zone')
    parse_inventory_parser.set_defaults(func=cmd_parse_inventory)
    
    # Analyze format command
    analyze_format_parser = subparsers.add_parser('analyze-format', help='Analyze data format of a GHCN station')
    analyze_format_parser.add_argument('input', help='Input station data file (CSV)')
    analyze_format_parser.set_defaults(func=cmd_analyze_format)
      # Station discovery commands
    find_parser = subparsers.add_parser('find-stations', help='Find GHCN stations by climate zone')
    find_parser.add_argument('climate_zone', choices=['arid', 'tropical', 'temperate'],
                           help='Climate zone to search in')
    find_parser.add_argument('--inventory-file', default='ghcnd-inventory.txt',
                           help='Path to GHCN inventory file (default: ghcnd-inventory.txt)')
    find_parser.add_argument('--download', action='store_true',
                           help='Download inventory file if not found')
    find_parser.add_argument('-o', '--output', help='Output file for station results')
    find_parser.set_defaults(func=cmd_find_stations)
    
    # Geographic station search
    find_radius_parser = subparsers.add_parser('find-stations-radius', 
                                             help='Find GHCN stations within radius of coordinates')
    find_radius_parser.add_argument('latitude', type=float, help='Target latitude')
    find_radius_parser.add_argument('longitude', type=float, help='Target longitude')
    find_radius_parser.add_argument('radius', type=float, help='Search radius in kilometers')
    find_radius_parser.add_argument('--inventory-file', default='ghcnd-inventory.txt',
                                   help='Path to GHCN inventory file (default: ghcnd-inventory.txt)')
    find_radius_parser.add_argument('--download', action='store_true',
                                   help='Download inventory file if not found')
    find_radius_parser.add_argument('--data-types', default='PRCP,TMAX,TMIN',
                                   help='Required data types (comma-separated, default: PRCP,TMAX,TMIN)')
    find_radius_parser.add_argument('--min-years', type=int, default=30,
                                   help='Minimum years of data required (default: 30)')
    find_radius_parser.add_argument('--start-before', type=int, default=1990,
                                   help='Data must start on or before this year (default: 1990)')
    find_radius_parser.add_argument('--end-after', type=int, default=2020,
                                   help='Data must end after this year (default: 2020)')
    find_radius_parser.add_argument('-o', '--output', help='Output file for station results')
    find_radius_parser.set_defaults(func=cmd_find_stations_radius)
    
    # Batch gap analysis
    batch_gap_parser = subparsers.add_parser('batch-gap-analysis', 
                                           help='Perform gap analysis on multiple stations')
    batch_gap_parser.add_argument('stations_file', help='CSV file containing station list (must have STATION column)')
    batch_gap_parser.add_argument('-o', '--output', help='Output file for wellness summary')
    batch_gap_parser.add_argument('--start-year', type=int, help='Start year for analysis period')
    batch_gap_parser.add_argument('--end-year', type=int, help='End year for analysis period')
    batch_gap_parser.add_argument('--column', default='PRCP', help='Column to analyze for gaps (default: PRCP)')
    batch_gap_parser.add_argument('--gap-threshold', type=int, default=7, 
                                 help='Threshold for short vs long gaps in days (default: 7)')
    batch_gap_parser.set_defaults(func=cmd_batch_gap_analysis)
      # Download station command  
    download_parser = subparsers.add_parser('download-station', help='Download data for a specific GHCN station')
    download_parser.add_argument('station_id', help='GHCN station ID (e.g., USW00023066)')
    download_parser.add_argument('-o', '--output', help='Output file path')
    download_parser.add_argument('--force', action='store_true', 
                                help='Overwrite existing files without prompting')
    download_parser.set_defaults(func=cmd_download_station)
    
    # List climate zones command
    zones_parser = subparsers.add_parser('list-zones', help='List available climate zones')
    zones_parser.set_defaults(func=cmd_list_climate_zones)
      # Station info command
    station_info_parser = subparsers.add_parser('station-info', help='Get information about a GHCN station')
    station_info_parser.add_argument('station_id', help='GHCN station ID (e.g., USW00023066)')
    station_info_parser.set_defaults(func=cmd_station_info)
  
    # Data filling subparser
    fill_parser = subparsers.add_parser(
        'fill-data',
        help='Fill missing values in precipitation data using smart interpolation'
    )
    fill_parser.add_argument('input_file', help='Input CSV file with missing data')
    fill_parser.add_argument('-o', '--output', required=True, help='Output file for filled data')
    fill_parser.add_argument('--date-col', default='DATE', help='Date column name (default: DATE)')
    fill_parser.add_argument('--precip-col', default='PRCP', help='Precipitation column name (default: PRCP)')
    fill_parser.add_argument('--max-gap-days', type=int, default=365, 
                           help='Maximum gap size to attempt filling (default: 365)')
    fill_parser.set_defaults(func=cmd_fill_data)
  
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'params':
            cmd_params(args)
        elif args.command == 'window':
            cmd_window_params(args)
        elif args.command == 'ext-params':
            cmd_ext_params(args)
        elif args.command == 'info':
            cmd_info(args)
        elif args.command == 'test':
            cmd_test(args)
        elif args.command == 'ghcn-info':
            cmd_ghcn_info(args)
        elif args.command == 'fetch-inventory':
            cmd_fetch_inventory(args)
        elif args.command == 'parse-inventory':
            cmd_parse_inventory(args)
        elif args.command == 'analyze-format':
            cmd_analyze_format(args)
        elif args.command == 'find-stations':
            cmd_find_stations(args)
        elif args.command == 'find-stations-radius':
            cmd_find_stations_radius(args)
        elif args.command == 'batch-gap-analysis':
            cmd_batch_gap_analysis(args)
        elif args.command == 'download-station':
            cmd_download_station(args)
        elif args.command == 'list-zones':
            cmd_list_climate_zones(args)
        elif args.command == 'station-info':
            cmd_station_info(args)
        elif args.command == 'gap-analysis':
            cmd_gap_analysis(args)
        elif args.command == 'wave-analysis':
            cmd_wave_analysis(args)
        elif args.command == 'fill-data':
            cmd_fill_data(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
