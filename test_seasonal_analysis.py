#!/usr/bin/env python3
"""
Test script for seasonal random walk analysis
"""

import os
import sys
from time_series import TimeSeries
from random_walk_params import analyze_random_walk_parameters

def test_seasonal_analysis():
    """Test seasonal random walk analysis on sample data."""
    
    # Test with sample data
    test_file = os.path.join("tests", "GrandJunction", "USW00023066_data.csv")
    if not os.path.exists(test_file):
        print("❌ Test data not found")
        return
    
    print(f"🔍 Testing seasonal random walk analysis with {test_file}")
    
    try:
        # Load time series data
        ts = TimeSeries()
        ts.load_and_preprocess(test_file)
        ts.trim(1990, 2020)  # Use subset for faster testing
        
        print(f"📊 Loaded data: {len(ts.get_data())} days")
        
        # Run seasonal analysis
        print("🌱 Running seasonal random walk analysis...")
        analyzer = analyze_random_walk_parameters(ts, window_size=2, seasonal_analysis=True)
        
        print("\n✅ SEASONAL ANALYSIS RESULTS:")
        print("=" * 50)
        
        # Display annual results
        print(f"\n📈 ANNUAL ANALYSIS:")
        print(f"   Windows analyzed: {len(analyzer.parameter_sequence)}")
        for param in ['PWW', 'PWD']:
            if param in analyzer.volatilities:
                vol = analyzer.volatilities[param]
                rev = analyzer.reversion_rates[param]
                mean = analyzer.long_term_means[param]
                print(f"   {param}: σ={vol:.6f}, r={rev:.6f}, μ={mean:.4f}")
        
        # Display seasonal results
        if analyzer.seasonal_sequences:
            print(f"\n🌍 SEASONAL ANALYSIS:")
            seasonal_vol = analyzer.calculate_seasonal_volatilities()
            seasonal_rev = analyzer.calculate_seasonal_reversion_rates()
            seasonal_means = analyzer.calculate_seasonal_long_term_means()
            
            for season in ['winter', 'spring', 'summer', 'fall']:
                if season in analyzer.seasonal_sequences:
                    n_windows = len(analyzer.seasonal_sequences[season])
                    print(f"\n   {season.upper()} ({n_windows} windows):")
                    
                    for param in ['PWW', 'PWD']:
                        if (season in seasonal_vol and param in seasonal_vol[season]):
                            vol = seasonal_vol[season][param]
                            rev = seasonal_rev[season][param]
                            mean = seasonal_means[season][param]
                            print(f"     {param}: σ={vol:.6f}, r={rev:.6f}, μ={mean:.4f}")
        
        print("\n🎯 SEASONAL TREND DETECTION:")
        print("=" * 50)
        
        # Look for evidence of seasonal trends
        for season in ['winter', 'spring', 'summer', 'fall']:
            if season in analyzer.seasonal_sequences:
                season_data = analyzer.seasonal_sequences[season]
                
                for param in ['PWW', 'PWD']:
                    if param in season_data.columns and len(season_data) > 3:
                        years = season_data['year'].values
                        values = season_data[param].values
                        
                        # Calculate linear trend
                        import numpy as np
                        if len(years) > 2:
                            trend_coef = np.polyfit(years, values, 1)[0]
                            trend_per_decade = trend_coef * 10
                            
                            trend_strength = "STRONG" if abs(trend_per_decade) > 0.01 else "WEAK"
                            trend_direction = "INCREASING" if trend_per_decade > 0 else "DECREASING"
                            
                            print(f"   {season} {param}: {trend_direction} {trend_per_decade:+.4f}/decade ({trend_strength})")
        
        print(f"\n✅ Seasonal analysis completed successfully!")
        
        # Save test results
        analyzer.export_seasonal_results("test_seasonal_results.json", "json")
        analyzer.export_seasonal_results("test_seasonal_results.csv", "csv")
        print(f"📁 Results saved to test_seasonal_results.*")
        
    except Exception as e:
        print(f"❌ Seasonal analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_seasonal_analysis()
