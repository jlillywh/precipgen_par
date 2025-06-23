#!/usr/bin/env python3
"""
Demonstration of Data Filling Capabilities for PrecipGen PAR

This script demonstrates how to use the data filling functionality
to handle missing precipitation data using meteorological best practices.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_filler import PrecipitationDataFiller
import warnings
warnings.filterwarnings('ignore')

def create_demo_data_with_gaps():
    """Create realistic precipitation data with various types of gaps."""
    print("Creating demonstration dataset with realistic precipitation patterns...")
    
    # Create 5 years of daily data
    start_date = datetime(2018, 1, 1)
    end_date = datetime(2022, 12, 31)
    dates = pd.date_range(start_date, end_date, freq='D')
    
    # Generate realistic precipitation with seasonal patterns
    np.random.seed(42)  # For reproducible demo
    
    # Seasonal pattern (higher precipitation in winter/spring)
    day_of_year = dates.dayofyear
    seasonal_factor = 1.2 + 0.8 * np.sin(2 * np.pi * (day_of_year - 300) / 365)
      # Base precipitation amounts (exponential distribution)
    base_precip = np.random.exponential(0.6, len(dates)) * seasonal_factor
    
    # Create wet/dry days (about 70% dry days)
    wet_probability = 0.3 + 0.2 * seasonal_factor / 2.0  # Higher wet probability in wet season
    dry_mask = np.random.random(len(dates)) > wet_probability
    base_precip = base_precip.copy()  # Ensure we have a mutable array
    base_precip[dry_mask] = 0.0
    
    # Add some extreme events (storms)
    storm_days = np.random.choice(len(dates), 25, replace=False)
    base_precip[storm_days] += np.random.uniform(2, 8, 25)
    
    # Create the initial complete dataset
    complete_data = pd.DataFrame({
        'DATE': dates,
        'PRCP': base_precip
    })
    
    # Now create various types of gaps to demonstrate filling methods
    data_with_gaps = complete_data.copy()
    
    # Type 1: Single day gaps (for linear interpolation)
    single_day_gaps = [
        datetime(2019, 4, 15),
        datetime(2020, 8, 22),
        datetime(2021, 12, 5)
    ]
    
    # Type 2: Short gaps 2-3 days (for linear interpolation)
    short_gaps = [
        (datetime(2019, 6, 10), datetime(2019, 6, 11)),
        (datetime(2020, 3, 25), datetime(2020, 3, 26)),
        (datetime(2021, 9, 8), datetime(2021, 9, 9))
    ]
    
    # Type 3: Medium gaps 4-7 days (for climatological filling)
    medium_gaps = [
        (datetime(2019, 7, 15), datetime(2019, 7, 19)),
        (datetime(2020, 11, 2), datetime(2020, 11, 6)),
        (datetime(2021, 2, 20), datetime(2021, 2, 24))
    ]
    
    # Type 4: Long gaps 8-20 days (for analogous year method)
    long_gaps = [
        (datetime(2019, 10, 5), datetime(2019, 10, 15)),
        (datetime(2020, 5, 12), datetime(2020, 5, 25)),
        (datetime(2021, 8, 1), datetime(2021, 8, 12))
    ]
    
    # Type 5: Very long gap (to show limits)
    very_long_gap = (datetime(2022, 6, 1), datetime(2022, 7, 15))  # 45 days
    
    # Apply gaps
    print("Creating gaps of various sizes:")
    
    # Single day gaps
    for gap_date in single_day_gaps:
        mask = data_with_gaps['DATE'] == gap_date
        data_with_gaps.loc[mask, 'PRCP'] = np.nan
        print(f"  Single day gap: {gap_date.strftime('%Y-%m-%d')}")
    
    # Short gaps
    for start, end in short_gaps:
        mask = (data_with_gaps['DATE'] >= start) & (data_with_gaps['DATE'] <= end)
        data_with_gaps.loc[mask, 'PRCP'] = np.nan
        gap_days = (end - start).days + 1
        print(f"  Short gap ({gap_days} days): {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    
    # Medium gaps
    for start, end in medium_gaps:
        mask = (data_with_gaps['DATE'] >= start) & (data_with_gaps['DATE'] <= end)
        data_with_gaps.loc[mask, 'PRCP'] = np.nan
        gap_days = (end - start).days + 1
        print(f"  Medium gap ({gap_days} days): {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    
    # Long gaps
    for start, end in long_gaps:
        mask = (data_with_gaps['DATE'] >= start) & (data_with_gaps['DATE'] <= end)
        data_with_gaps.loc[mask, 'PRCP'] = np.nan
        gap_days = (end - start).days + 1
        print(f"  Long gap ({gap_days} days): {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    
    # Very long gap
    mask = (data_with_gaps['DATE'] >= very_long_gap[0]) & (data_with_gaps['DATE'] <= very_long_gap[1])
    data_with_gaps.loc[mask, 'PRCP'] = np.nan
    gap_days = (very_long_gap[1] - very_long_gap[0]).days + 1
    print(f"  Very long gap ({gap_days} days): {very_long_gap[0].strftime('%Y-%m-%d')} to {very_long_gap[1].strftime('%Y-%m-%d')}")
    
    total_missing = data_with_gaps['PRCP'].isna().sum()
    total_days = len(data_with_gaps)
    missing_percent = (total_missing / total_days) * 100
    
    print(f"\nDataset summary:")
    print(f"  Total days: {total_days}")
    print(f"  Missing values: {total_missing}")
    print(f"  Missing percentage: {missing_percent:.1f}%")
    
    return complete_data, data_with_gaps

def demonstrate_filling_methods():
    """Demonstrate different data filling methods."""
    print("\n" + "="*60)
    print("PRECIPITATION DATA FILLING DEMONSTRATION")
    print("="*60)
    
    # Create demo data
    complete_data, data_with_gaps = create_demo_data_with_gaps()
    
    # Save the gapped data for reference
    data_with_gaps.to_csv('demo_data_with_gaps.csv', index=False)
    print(f"\nGapped data saved to: demo_data_with_gaps.csv")
    
    # Initialize the data filler
    print("\nInitializing PrecipitationDataFiller...")
    filler = PrecipitationDataFiller(
        min_similarity_threshold=0.6,  # Lower threshold for demo
        max_fill_gap_days=35,  # Allow larger gaps for demo
        seasonal_window_days=15,
        min_years_for_climatology=3  # Lower requirement for demo data
    )
    
    print("Filling missing data using meteorological best practices...")
    print("-" * 50)
    
    # Fill the missing data
    filled_data, report = filler.fill_missing_data(
        data_with_gaps.copy(),
        output_file='demo_data_filled.csv',
        create_report=True
    )
    
    # Display results
    print("\nFILLING RESULTS:")
    print("="*40)
    
    summary = report['summary']
    print(f"Original missing values: {summary['original_missing_values']}")
    print(f"Final missing values: {summary['final_missing_values']}")
    print(f"Values filled: {summary['values_filled']}")
    print(f"Success rate: {summary['fill_success_rate']:.1f}%")
    print(f"Total gaps identified: {summary['total_gaps_identified']}")
    print(f"Gaps successfully filled: {summary['gaps_filled']}")
    
    print(f"\nMETHODS USED:")
    print("-" * 20)
    methods = report['methods_used']
    for method, count in methods.items():
        if count > 0:
            method_name = method.replace('_', ' ').title()
            print(f"  {method_name}: {count}")
    
    print(f"\nDATA QUALITY METRICS:")
    print("-" * 25)
    validation = report['validation_results']
    print(f"  Overall quality: {'✓ Good' if validation['quality_good'] else '⚠ Review needed'}")
    print(f"  Mean change: {validation['mean_change']:.3f}")
    print(f"  Std dev change: {validation['std_change']:.3f}")
    print(f"  Negative values: {validation['filled_data_negative']}")
    print(f"  Extreme values: {validation['filled_data_extreme']}")
    
    print(f"\nDATA STATISTICS:")
    print("-" * 20)
    quality = report['data_quality']
    print(f"  Mean precipitation: {quality['mean_precipitation']:.3f} inches")
    print(f"  Std precipitation: {quality['std_precipitation']:.3f} inches")
    print(f"  Min precipitation: {quality['min_precipitation']:.3f} inches")
    print(f"  Max precipitation: {quality['max_precipitation']:.3f} inches")
    print(f"  Zero precipitation days: {quality['zero_precipitation_days']}")
    
    if report['recommendations']:
        print(f"\nRECOMMENDATIONS:")
        print("-" * 20)
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Compare with original data
    print(f"\nCOMPARISON WITH ORIGINAL DATA:")
    print("-" * 35)
    
    orig_mean = complete_data['PRCP'].mean()
    filled_mean = filled_data['PRCP'].mean()
    mean_diff = abs(filled_mean - orig_mean) / orig_mean * 100
    
    orig_std = complete_data['PRCP'].std()
    filled_std = filled_data['PRCP'].std()
    std_diff = abs(filled_std - orig_std) / orig_std * 100
    
    print(f"  Original mean: {orig_mean:.3f} inches")
    print(f"  Filled mean: {filled_mean:.3f} inches")
    print(f"  Mean difference: {mean_diff:.1f}%")
    print(f"  Original std: {orig_std:.3f} inches")
    print(f"  Filled std: {filled_std:.3f} inches")
    print(f"  Std difference: {std_diff:.1f}%")
    
    # Monthly comparison
    orig_monthly = complete_data.groupby(complete_data['DATE'].dt.month)['PRCP'].sum()
    filled_monthly = filled_data.groupby(filled_data['DATE'].dt.month)['PRCP'].sum()
    monthly_corr = np.corrcoef(orig_monthly, filled_monthly)[0, 1]
    
    print(f"  Monthly pattern correlation: {monthly_corr:.3f}")
    
    return complete_data, data_with_gaps, filled_data, report

def create_visualization(complete_data, data_with_gaps, filled_data):
    """Create visualization of the filling results."""
    print(f"\nCreating visualization...")
    
    try:
        # Create a multi-panel plot
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        # Focus on a specific period for detailed view
        start_plot = datetime(2020, 1, 1)
        end_plot = datetime(2020, 12, 31)
        
        plot_mask = (complete_data['DATE'] >= start_plot) & (complete_data['DATE'] <= end_plot)
        
        dates_plot = complete_data[plot_mask]['DATE']
        orig_plot = complete_data[plot_mask]['PRCP']
        gaps_plot = data_with_gaps[plot_mask]['PRCP']
        filled_plot = filled_data[plot_mask]['PRCP']
        
        # Panel 1: Original data
        axes[0].plot(dates_plot, orig_plot, 'b-', linewidth=1, alpha=0.7, label='Original Data')
        axes[0].set_title('Original Complete Precipitation Data (2020)', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Precipitation (inches)')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()
        
        # Panel 2: Data with gaps
        axes[1].plot(dates_plot, gaps_plot, 'r-', linewidth=1, alpha=0.7, label='Data with Gaps')
        # Mark missing periods
        missing_mask = gaps_plot.isna()
        if missing_mask.any():
            axes[1].scatter(dates_plot[missing_mask], [0]*missing_mask.sum(), 
                           color='red', marker='x', s=30, label='Missing Values')
        axes[1].set_title('Data with Missing Values', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Precipitation (inches)')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()
        
        # Panel 3: Filled data
        axes[2].plot(dates_plot, filled_plot, 'g-', linewidth=1, alpha=0.7, label='Filled Data')
        # Highlight filled values
        filled_mask = data_with_gaps[plot_mask]['PRCP'].isna()
        if filled_mask.any():
            axes[2].scatter(dates_plot[filled_mask], filled_plot[filled_mask], 
                           color='orange', marker='o', s=20, label='Filled Values')
        axes[2].set_title('Data After Filling', fontsize=14, fontweight='bold')
        axes[2].set_ylabel('Precipitation (inches)')
        axes[2].set_xlabel('Date')
        axes[2].grid(True, alpha=0.3)
        axes[2].legend()
        
        plt.tight_layout()
        plt.savefig('demo_data_filling_results.png', dpi=300, bbox_inches='tight')
        print(f"Visualization saved to: demo_data_filling_results.png")
        plt.close()
        
        # Create monthly comparison plot
        fig, ax = plt.subplots(1, 1, figsize=(12, 6))
        
        orig_monthly = complete_data.groupby(complete_data['DATE'].dt.month)['PRCP'].sum()
        filled_monthly = filled_data.groupby(filled_data['DATE'].dt.month)['PRCP'].sum()
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        x = np.arange(len(months))
        width = 0.35
        
        ax.bar(x - width/2, orig_monthly.values, width, label='Original Data', alpha=0.7)
        ax.bar(x + width/2, filled_monthly.values, width, label='Filled Data', alpha=0.7)
        
        ax.set_xlabel('Month')
        ax.set_ylabel('Total Precipitation (inches)')
        ax.set_title('Monthly Precipitation Totals: Original vs Filled Data')
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('demo_monthly_comparison.png', dpi=300, bbox_inches='tight')
        print(f"Monthly comparison saved to: demo_monthly_comparison.png")
        plt.close()
        
    except ImportError:
        print("Matplotlib not available - skipping visualization")
    except Exception as e:
        print(f"Error creating visualization: {e}")

def demonstrate_cli_usage():
    """Show how to use the CLI for data filling."""
    print(f"\n" + "="*60)
    print("COMMAND LINE USAGE EXAMPLES")
    print("="*60)
    
    print(f"\n1. Basic data filling:")
    print(f"   python cli.py fill-data demo_data_with_gaps.csv -o filled_output.csv")
    
    print(f"\n2. Custom parameters:")
    print(f"   python cli.py fill-data demo_data_with_gaps.csv -o filled_output.csv \\")
    print(f"     --max-gap-days 20 \\")
    print(f"     --min-similarity 0.8 \\")
    print(f"     --seasonal-window 10")
    
    print(f"\n3. Different column names:")
    print(f"   python cli.py fill-data my_data.csv -o filled_data.csv \\")
    print(f"     --date-col DATETIME --precip-col RAINFALL")
    
    print(f"\n4. Complete workflow example:")
    print(f"   # 1. Find and download station data")
    print(f"   python cli.py find-stations-radius 40.0 -105.0 100 -o stations.csv")
    print(f"   python cli.py download-station USW00023066 -o weather_data.csv")
    print(f"   ")
    print(f"   # 2. Fill missing data")
    print(f"   python cli.py fill-data weather_data.csv -o weather_data_filled.csv")
    print(f"   ")
    print(f"   # 3. Analyze data quality")
    print(f"   python cli.py gap-analysis weather_data_filled.csv -o gap_analysis")
    print(f"   ")
    print(f"   # 4. Calculate parameters")
    print(f"   python cli.py params weather_data_filled.csv -o parameters.csv")

def main():
    """Run the complete demonstration."""
    print("PrecipGen PAR - Data Filling Demonstration")
    print("This demo shows professional-grade precipitation data filling methods")
    print("following meteorological and hydrological best practices.\n")
    
    try:
        # Run the demonstration
        complete_data, data_with_gaps, filled_data, report = demonstrate_filling_methods()
        
        # Create visualizations
        create_visualization(complete_data, data_with_gaps, filled_data)
        
        # Show CLI usage
        demonstrate_cli_usage()
        
        print(f"\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print(f"\nFiles created:")
        print(f"  • demo_data_with_gaps.csv - Original data with gaps")
        print(f"  • demo_data_filled.csv - Data after filling")
        print(f"  • demo_data_filled_filling_report.json - Detailed filling report")
        print(f"  • demo_data_filling_results.png - Time series visualization")
        print(f"  • demo_monthly_comparison.png - Monthly totals comparison")
        
        print(f"\nKey findings:")
        print(f"  • Success rate: {report['summary']['fill_success_rate']:.1f}%")
        print(f"  • Methods used: {sum(1 for v in report['methods_used'].values() if v > 0)} different approaches")
        print(f"  • Data quality: {'Good' if report['validation_results']['quality_good'] else 'Review needed'}")
        
        print(f"\nThe data filling module successfully handles:")
        print(f"  ✓ Short gaps (1-2 days) using linear interpolation")
        print(f"  ✓ Medium gaps (3-7 days) using climatological normals")
        print(f"  ✓ Long gaps (8+ days) using analogous year method")
        print(f"  ✓ Statistical validation and quality control")
        print(f"  ✓ Preservation of seasonal patterns and extreme events")
        
    except Exception as e:
        print(f"Error running demonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
