#!/usr/bin/env python3
"""
PrecipGen Parameter Wave Analysis Demo

This script demonstrates how to use the PrecipGenPARWave module to analyze
the temporal evolution of PrecipGen parameters using wave function decomposition.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add the current directory to the path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from time_series import TimeSeries
from pgpar_wave import PrecipGenPARWave, analyze_precipgen_parameter_waves

# Import project-aware output functions
try:
    from easy_start import get_output_path, get_output_directory
except ImportError:
    # Fallback for standalone execution
    def get_output_path(filename):
        return filename
    def get_output_directory():
        return "."


def demo_parameter_wave_analysis(data_file: str, output_dir: str = None):
    """
    Demonstrate complete parameter wave analysis workflow.
    
    Parameters
    ----------
    data_file : str
        Path to precipitation data CSV file
    output_dir : str
        Directory to save output files (default: uses project-aware output)
    """
    print("=" * 60)
    print("PrecipGen Parameter Wave Analysis Demo")
    print("=" * 60)
    
    if output_dir is None:
        # Use project-aware output directory
        base_output = get_output_directory()
        output_dir = os.path.join(base_output, "wave_output")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Load and prepare time series data
    print("\n1. Loading precipitation data...")
    ts = TimeSeries()
    ts.load_and_preprocess(data_file)
    
    # Get data overview
    data = ts.get_data()
    start_year = data.index.year.min()
    end_year = data.index.year.max()
    total_years = end_year - start_year + 1
    
    print(f"   Loaded data from {start_year} to {end_year} ({total_years} years)")
    print(f"   Total observations: {len(data)}")
    print(f"   Missing data: {data.isna().sum()} days")
    
    # Step 2: Configure analysis parameters
    print("\n2. Configuring analysis parameters...")
    window_size = min(15, total_years // 3)  # Adaptive window size
    overlap = 0.5
    num_components = 5
    
    print(f"   Window size: {window_size} years")
    print(f"   Window overlap: {overlap:.1%}")
    print(f"   Max wave components: {num_components}")
    
    # Step 3: Run parameter wave analysis
    print("\n3. Running parameter wave analysis...")
    analyzer = PrecipGenPARWave(ts, window_size=window_size, overlap=overlap)
    
    # Extract parameter history
    print("   Extracting parameter history...")
    param_history = analyzer.extract_parameter_history()
    print(f"   Extracted parameters for {len(param_history)} time windows")
    
    # Analyze wave components
    print("   Analyzing wave components...")
    wave_components = analyzer.analyze_parameter_waves(num_components=num_components)
    
    print("   Wave components found:")
    for param, components in wave_components.items():
        n_comp = len(components['components'])
        print(f"     {param}: {n_comp} components")
    
    # Fit parameter evolution
    print("   Fitting parameter evolution...")
    fitted_params = analyzer.fit_parameter_evolution()
    
    # Step 4: Generate analysis summary
    print("\n4. Analysis Summary:")
    print("-" * 40)
    
    for param in ['PWW', 'PWD', 'alpha', 'beta']:
        if param in fitted_params:
            fitted = fitted_params[param]
            trend_slope = fitted['trend']['slope']
            dominant_period = fitted['wave_summary']['dominant_period']
            total_amplitude = fitted['wave_summary']['total_amplitude']
            
            print(f"\n{param}:")
            print(f"   Trend: {trend_slope:+.6f} per year")
            print(f"   Dominant period: {dominant_period:.1f} years")
            print(f"   Total wave amplitude: {total_amplitude:.4f}")
            
            # Show component breakdown
            groups = fitted['component_groups']
            print(f"   Components: {len(groups['short_term'])} short-term, "
                  f"{len(groups['medium_term'])} medium-term, "
                  f"{len(groups['long_term'])} long-term")
    
    # Step 5: Generate synthetic parameters for future years
    print("\n5. Generating synthetic parameter projections...")
    future_years = np.arange(end_year + 1, end_year + 21)  # 20 years ahead
    synthetic_params = analyzer.generate_synthetic_parameters(future_years)
    
    print(f"   Generated synthetic parameters for {len(future_years)} future years")
    print(f"   Future period: {future_years[0]} to {future_years[-1]}")
    
    # Step 6: Export results
    print("\n6. Exporting results...")
    
    # Export wave parameters to JSON
    json_file = os.path.join(output_dir, "wave_parameters.json")
    analyzer.export_wave_parameters(json_file, format='json')
    print(f"   Wave parameters: {json_file}")
    
    # Export component summary to CSV
    csv_file = os.path.join(output_dir, "wave_components.csv")
    analyzer.export_wave_parameters(csv_file, format='csv')
    print(f"   Component summary: {csv_file}")
    
    # Export parameter history
    history_file = os.path.join(output_dir, "parameter_history.csv")
    param_history.to_csv(history_file, index=False)
    print(f"   Parameter history: {history_file}")
    
    # Export synthetic parameters
    synthetic_file = os.path.join(output_dir, "synthetic_parameters.csv")
    synthetic_params.to_csv(synthetic_file, index=False)
    print(f"   Synthetic parameters: {synthetic_file}")
    
    # Step 7: Create visualizations
    print("\n7. Creating visualizations...")
    
    # Parameter evolution plot
    evolution_plot = os.path.join(output_dir, "parameter_evolution.png")
    analyzer.plot_parameter_evolution(save_path=evolution_plot)
    print(f"   Parameter evolution: {evolution_plot}")
    
    # Wave components plot
    components_plot = os.path.join(output_dir, "wave_components.png")
    analyzer.plot_wave_components(save_path=components_plot)
    print(f"   Wave components: {components_plot}")
    
    # Create projection plot
    projection_plot = os.path.join(output_dir, "parameter_projections.png")
    create_projection_plot(analyzer, future_years, synthetic_params, projection_plot)
    print(f"   Future projections: {projection_plot}")
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print(f"Results saved to: {os.path.abspath(output_dir)}")
    print("=" * 60)
    
    return analyzer


def create_projection_plot(analyzer: PrecipGenPARWave, future_years: np.ndarray,
                          synthetic_params: dict, save_path: str):
    """Create a plot showing historical and projected parameters."""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('PrecipGen Parameter Projections', fontsize=16)
    
    params = ['PWW', 'PWD', 'alpha', 'beta']
    axes = axes.flatten()
    
    # Get historical data
    hist_years = analyzer.parameter_history['year']
    
    for i, param in enumerate(params):
        if param not in analyzer.parameter_history.columns:
            continue
        
        ax = axes[i]
        
        # Plot historical data
        hist_values = analyzer.parameter_history[param]
        ax.plot(hist_years, hist_values, 'o-', color='blue', alpha=0.7,
               label='Historical', markersize=4)
        
        # Plot projection
        if param in synthetic_params.columns:
            proj_values = synthetic_params[param]
            ax.plot(future_years, proj_values, 's-', color='red', alpha=0.7,
                   label='Projected', markersize=4)
        
        # Add vertical line at transition
        ax.axvline(hist_years.iloc[-1], color='gray', linestyle='--', alpha=0.5)
        
        ax.set_title(f'{param} - Historical and Projected')
        ax.set_xlabel('Year')
        ax.set_ylabel(param)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def main():
    """Main demo function."""
    
    # Check for test data
    test_files = [
        os.path.join("tests", "GrandJunction", "USW00023066_data.csv"),
        os.path.join("tests", "denver_stapleton_test.csv"),
        "test_data.csv"
    ]
    
    data_file = None
    for test_file in test_files:
        if os.path.exists(test_file):
            data_file = test_file
            break
    
    if data_file is None:
        print("No test data files found. Available files:")
        for test_file in test_files:
            print(f"  {test_file}")
        print("\nPlease ensure test data is available or modify the file paths.")
        return
    
    print(f"Using data file: {data_file}")
    
    # Run the demo
    try:
        analyzer = demo_parameter_wave_analysis(data_file)
        
        # Print quick summary
        print("\nQuick Summary:")
        if analyzer.parameter_history is not None:
            n_windows = len(analyzer.parameter_history)
            year_range = (analyzer.parameter_history['year'].min(),
                         analyzer.parameter_history['year'].max())
            print(f"  Analyzed {n_windows} parameter windows")
            print(f"  Time range: {year_range[0]} to {year_range[1]}")
        
        if analyzer.fitted_parameters:
            n_params = len(analyzer.fitted_parameters)
            print(f"  Successfully analyzed {n_params} parameters")
            
            # Show dominant periods
            print("  Dominant cycles:")
            for param, data in analyzer.fitted_parameters.items():
                period = data['wave_summary']['dominant_period']
                if period and period < 100:  # Reasonable period
                    print(f"    {param}: {period:.1f} years")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
