#!/usr/bin/env python3
"""
Test suite for wave function enhanced PrecipGen modules
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from time_series import TimeSeries
from wave_functions import WaveFunctionAnalyzer, analyze_precipitation_waves
from precipgen_wave import WaveBasedPrecipGen, create_wave_enhanced_precipgen, WaveSimulationParams


class TestWaveFunctions(unittest.TestCase):
    """Test wave function analysis capabilities."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for wave function tests."""
        # Create synthetic precipitation data with known cycles
        dates = pd.date_range('2000-01-01', '2010-12-31', freq='D')
        n_days = len(dates)
        
        # Create synthetic precipitation with multiple cycles
        time_days = np.arange(n_days)
        
        # Annual cycle (strongest)
        annual_cycle = 50 * np.sin(2 * np.pi * time_days / 365.25)
        
        # Biannual cycle
        biannual_cycle = 20 * np.sin(2 * np.pi * time_days / (365.25 * 2))
        
        # Monthly cycle
        monthly_cycle = 10 * np.sin(2 * np.pi * time_days / 30.44)
        
        # Combine cycles and add noise
        base_signal = annual_cycle + biannual_cycle + monthly_cycle + 100
        noise = np.random.normal(0, 15, n_days)
        precipitation = np.maximum(base_signal + noise, 0)
        
        # Add dry days (make some days zero)
        dry_mask = np.random.random(n_days) < 0.7  # 70% chance of dry day
        precipitation[dry_mask] = 0
        
        cls.test_data = pd.DataFrame({
            'PRCP': precipitation
        }, index=dates)
    
    def test_wave_analyzer_initialization(self):
        """Test WaveFunctionAnalyzer initialization."""
        analyzer = WaveFunctionAnalyzer(self.test_data)
        
        self.assertIsNotNone(analyzer.daily_data)
        self.assertIsNotNone(analyzer.monthly_data)
        self.assertIsNotNone(analyzer.annual_data)
        self.assertEqual(len(analyzer.daily_data), len(self.test_data))
        self.assertGreater(len(analyzer.monthly_data), 0)
        self.assertGreater(len(analyzer.annual_data), 0)
    
    def test_frequency_analysis(self):
        """Test frequency analysis functionality."""
        analyzer = WaveFunctionAnalyzer(self.test_data)
        
        # Test monthly frequency analysis
        monthly_results = analyzer.analyze_frequency_components('monthly')
        self.assertIn('dominant_frequencies', monthly_results)
        self.assertIn('dominant_periods', monthly_results)
        self.assertIn('power_spectrum', monthly_results)
        self.assertGreater(len(monthly_results['dominant_frequencies']), 0)
        
        # Test annual frequency analysis
        annual_results = analyzer.analyze_frequency_components('annual')
        self.assertIn('dominant_frequencies', annual_results)
        self.assertGreater(len(annual_results['dominant_frequencies']), 0)
    
    def test_wave_component_extraction(self):
        """Test wave component extraction."""
        analyzer = WaveFunctionAnalyzer(self.test_data)
        wave_components = analyzer.extract_wave_components(num_components=3)
        
        self.assertIn('monthly', wave_components)
        self.assertIn('annual', wave_components)
        
        # Check component structure
        for time_scale, components in wave_components.items():
            for comp in components:
                self.assertIn('frequency', comp)
                self.assertIn('period', comp)
                self.assertIn('amplitude', comp)
                self.assertIn('phase', comp)
                self.assertGreater(comp['amplitude'], 0)
                self.assertGreater(comp['period'], 0)
    
    def test_synthetic_generation(self):
        """Test synthetic time series generation."""
        analyzer = WaveFunctionAnalyzer(self.test_data)
        analyzer.extract_wave_components(num_components=3)
        
        # Generate synthetic monthly series
        synthetic_monthly = analyzer.generate_wave_function(24, 'monthly')
        self.assertEqual(len(synthetic_monthly), 24)
        self.assertTrue(all(val >= 0 for val in synthetic_monthly))
        
        # Generate synthetic annual series
        synthetic_annual = analyzer.generate_wave_function(5, 'annual')
        self.assertEqual(len(synthetic_annual), 5)
        self.assertTrue(all(val >= 0 for val in synthetic_annual))
    
    def test_cycle_characterization(self):
        """Test cycle characterization functionality."""
        analyzer = WaveFunctionAnalyzer(self.test_data)
        analyzer.extract_wave_components(num_components=5)
        
        cycle_char = analyzer.characterize_cycles()
        
        for time_scale, char in cycle_char.items():
            self.assertIn('short_cycles', char)
            self.assertIn('medium_cycles', char)
            self.assertIn('long_cycles', char)
            self.assertIn('total_components', char)
            
            total_components = (len(char['short_cycles']) + 
                              len(char['medium_cycles']) + 
                              len(char['long_cycles']))
            self.assertEqual(total_components, char['total_components'])
    
    def test_convenience_function(self):
        """Test the convenience function for wave analysis."""
        analyzer = analyze_precipitation_waves(self.test_data, num_components=3)
        
        self.assertIsInstance(analyzer, WaveFunctionAnalyzer)
        self.assertIn('monthly', analyzer.wave_components)
        self.assertIn('annual', analyzer.wave_components)


class TestWaveBasedPrecipGen(unittest.TestCase):
    """Test wave-based precipitation generation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for precipitation generation tests."""
        # Use the same synthetic data as wave function tests
        dates = pd.date_range('2000-01-01', '2005-12-31', freq='D')
        n_days = len(dates)
        
        # Create realistic precipitation data
        np.random.seed(42)  # For reproducible tests
        precipitation = []
        
        for date in dates:
            # Higher probability of rain in winter months
            month = date.month
            if month in [11, 12, 1, 2, 3]:  # Winter months
                rain_prob = 0.4
            else:  # Summer months
                rain_prob = 0.2
            
            if np.random.random() < rain_prob:
                # Rain amount from gamma distribution
                amount = np.random.gamma(2, 3)
                precipitation.append(amount)
            else:
                precipitation.append(0.0)
        
        cls.test_data = pd.DataFrame({
            'PRCP': precipitation
        }, index=dates)
    
    def test_wave_precipgen_initialization(self):
        """Test WaveBasedPrecipGen initialization."""
        generator = WaveBasedPrecipGen(self.test_data)
        
        self.assertIsNotNone(generator.markov_params)
        self.assertIsNotNone(generator.wave_analyzer)
        self.assertIsNotNone(generator.high_freq_components)
        self.assertIsNotNone(generator.low_freq_components)
        self.assertEqual(len(generator.markov_params), 12)  # 12 months
    
    def test_wave_simulation_params(self):
        """Test WaveSimulationParams configuration."""
        params = WaveSimulationParams(
            high_freq_weight=0.8,
            low_freq_weight=0.3,
            stochastic_component=0.1
        )
        
        generator = WaveBasedPrecipGen(self.test_data, params)
        self.assertEqual(generator.wave_params.high_freq_weight, 0.8)
        self.assertEqual(generator.wave_params.low_freq_weight, 0.3)
        self.assertEqual(generator.wave_params.stochastic_component, 0.1)
    
    def test_precipitation_simulation(self):
        """Test precipitation simulation functionality."""
        generator = WaveBasedPrecipGen(self.test_data)
        
        # Short simulation for testing
        results = generator.simulate_precipitation('2021-01-01', '2021-12-31')
        
        self.assertEqual(len(results), 365)  # 2021 is not a leap year
        self.assertIn('PRCP', results.columns)
        self.assertIn('STATE', results.columns)
        self.assertIn('WAVE_MODULATION', results.columns)
        
        # Check that precipitation values are non-negative
        self.assertTrue(all(results['PRCP'] >= 0))
        
        # Check that states are either 'wet' or 'dry'
        unique_states = set(results['STATE'].unique())
        self.assertTrue(unique_states.issubset({'wet', 'dry'}))
        
        # Check that wet days have positive precipitation
        wet_days = results[results['STATE'] == 'wet']
        if len(wet_days) > 0:
            self.assertTrue(all(wet_days['PRCP'] > 0))
        
        # Check that dry days have zero precipitation
        dry_days = results[results['STATE'] == 'dry']
        if len(dry_days) > 0:
            self.assertTrue(all(dry_days['PRCP'] == 0))
    
    def test_wave_modulation_generation(self):
        """Test wave modulation generation."""
        generator = WaveBasedPrecipGen(self.test_data)
        
        # Create test dates
        dates = pd.date_range('2021-01-01', '2021-12-31', freq='D')
        modulation = generator._generate_wave_modulation(dates)
        
        self.assertEqual(len(modulation), len(dates))
        self.assertTrue(all(modulation > 0))  # Modulation should be positive
    
    def test_simulation_quality_analysis(self):
        """Test simulation quality analysis."""
        generator = WaveBasedPrecipGen(self.test_data)
        
        # Run simulation
        results = generator.simulate_precipitation('2021-01-01', '2021-06-30')
        
        # Analyze quality
        quality_metrics = generator.analyze_simulation_quality()
        
        self.assertIn('historical_annual_mean', quality_metrics)
        self.assertIn('simulated_annual_mean', quality_metrics)
        self.assertIn('simulation_length_days', quality_metrics)
        self.assertEqual(quality_metrics['simulation_length_days'], len(results))
    
    def test_export_functionality(self):
        """Test simulation export functionality."""
        generator = WaveBasedPrecipGen(self.test_data)
        
        # Run simulation
        generator.simulate_precipitation('2021-01-01', '2021-03-31')
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_filename = f.name
        
        try:
            generator.export_simulation(temp_filename)
            
            # Verify file was created and has correct content
            self.assertTrue(os.path.exists(temp_filename))
            
            # Read back and verify
            exported_data = pd.read_csv(temp_filename, index_col=0, parse_dates=True)
            self.assertEqual(len(exported_data), len(generator.simulation_results))
            
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_convenience_function(self):
        """Test convenience function for creating wave-enhanced generator."""
        generator = create_wave_enhanced_precipgen(
            self.test_data, 
            high_freq_weight=0.7,
            low_freq_weight=0.3,
            stochastic_component=0.2
        )
        
        self.assertIsInstance(generator, WaveBasedPrecipGen)
        self.assertEqual(generator.wave_params.high_freq_weight, 0.7)
        self.assertEqual(generator.wave_params.low_freq_weight, 0.3)
        self.assertEqual(generator.wave_params.stochastic_component, 0.2)


class TestWaveIntegration(unittest.TestCase):
    """Test integration between wave functions and traditional parameters."""
    
    def setUp(self):
        """Set up integration test data."""
        # Create minimal test dataset
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        precipitation = np.random.exponential(2, len(dates))
        # Make 70% of days dry
        dry_mask = np.random.random(len(dates)) < 0.7
        precipitation[dry_mask] = 0
        
        self.test_data = pd.DataFrame({
            'PRCP': precipitation
        }, index=dates)
    
    def test_wave_traditional_comparison(self):
        """Test comparison between wave-enhanced and traditional simulation."""
        # Traditional approach (no wave enhancement)
        traditional_gen = create_wave_enhanced_precipgen(
            self.test_data,
            high_freq_weight=0.0,
            low_freq_weight=0.0,
            stochastic_component=1.0
        )
        
        # Wave-enhanced approach
        wave_gen = create_wave_enhanced_precipgen(
            self.test_data,
            high_freq_weight=0.6,
            low_freq_weight=0.4,
            stochastic_component=0.1
        )
        
        # Run both simulations
        traditional_results = traditional_gen.simulate_precipitation('2021-01-01', '2021-03-31')
        wave_results = wave_gen.simulate_precipitation('2021-01-01', '2021-03-31')
        
        # Both should produce valid results
        self.assertEqual(len(traditional_results), len(wave_results))
        self.assertTrue(all(traditional_results['PRCP'] >= 0))
        self.assertTrue(all(wave_results['PRCP'] >= 0))
        
        # Wave-enhanced should have modulation values different from 1
        wave_modulation = wave_results['WAVE_MODULATION']
        self.assertFalse(all(abs(mod - 1.0) < 0.01 for mod in wave_modulation))


if __name__ == '__main__':
    unittest.main(verbosity=2)
