#!/usr/bin/env python3
"""
Wave Function Analysis Module for PrecipGen

This module provides functions to analyze and characterize precipitation patterns
using wave functions on monthly, annual, and decadal time scales.
Replaces traditional random walk approaches with deterministic wave-based modeling.
"""

import numpy as np
import pandas as pd
from scipy import signal
from scipy.fft import fft, fftfreq, ifft
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from typing import Tuple, Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WaveFunctionAnalyzer:
    """
    Analyzes precipitation time series to extract wave function components
    at multiple time scales (monthly, annual, decadal).
    """
    
    def __init__(self, time_series: pd.DataFrame):
        """
        Initialize the wave function analyzer.
        
        Parameters
        ----------
        time_series : pd.DataFrame
            Time series with datetime index and 'PRCP' column
        """
        self.time_series = time_series.copy()
        self.daily_data = None
        self.monthly_data = None
        self.annual_data = None
        self.wave_components = {}
        
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data at different temporal resolutions."""
        # Daily data (already provided)
        self.daily_data = self.time_series.copy()
        
        # Monthly aggregated data
        self.monthly_data = self.time_series.resample('M').agg({
            'PRCP': ['sum', 'mean', 'count']
        }).round(4)
        self.monthly_data.columns = ['monthly_total', 'daily_mean', 'days_count']
        
        # Annual aggregated data
        self.annual_data = self.time_series.resample('Y').agg({
            'PRCP': ['sum', 'mean', 'count']
        }).round(4)
        self.annual_data.columns = ['annual_total', 'daily_mean', 'days_count']
        
        logger.info(f"Data prepared: {len(self.daily_data)} daily records, "
                   f"{len(self.monthly_data)} monthly records, "
                   f"{len(self.annual_data)} annual records")
    
    def analyze_frequency_components(self, data_type: str = 'monthly') -> Dict:
        """
        Perform frequency analysis to identify dominant cycles.
        
        Parameters
        ----------
        data_type : str
            Type of data to analyze ('daily', 'monthly', 'annual')
            
        Returns
        -------
        Dict
            Dictionary containing frequency analysis results
        """
        if data_type == 'daily':
            data = self.daily_data['PRCP'].values
            sampling_freq = 365.25  # days per year
            time_unit = 'days'
        elif data_type == 'monthly':
            data = self.monthly_data['monthly_total'].values
            sampling_freq = 12  # months per year
            time_unit = 'months'
        elif data_type == 'annual':
            data = self.annual_data['annual_total'].values
            sampling_freq = 1  # years
            time_unit = 'years'
        else:
            raise ValueError("data_type must be 'daily', 'monthly', or 'annual'")
        
        # Remove trend (detrend)
        detrended_data = signal.detrend(data)
        
        # Perform FFT
        n = len(detrended_data)
        fft_values = fft(detrended_data)
        frequencies = fftfreq(n, d=1/sampling_freq)
        
        # Get magnitude spectrum (only positive frequencies)
        positive_freq_idx = frequencies > 0
        frequencies_positive = frequencies[positive_freq_idx]
        magnitude_spectrum = np.abs(fft_values[positive_freq_idx])
        power_spectrum = magnitude_spectrum ** 2
        
        # Find dominant frequencies
        peak_indices = signal.find_peaks(power_spectrum, 
                                       height=np.max(power_spectrum) * 0.1)[0]
        dominant_frequencies = frequencies_positive[peak_indices]
        dominant_powers = power_spectrum[peak_indices]
        
        # Convert to periods
        dominant_periods = 1 / dominant_frequencies
        
        # Sort by power (descending)
        sorted_indices = np.argsort(dominant_powers)[::-1]
        dominant_frequencies = dominant_frequencies[sorted_indices]
        dominant_periods = dominant_periods[sorted_indices]
        dominant_powers = dominant_powers[sorted_indices]
        
        results = {
            'data_type': data_type,
            'time_unit': time_unit,
            'sampling_frequency': sampling_freq,
            'frequencies': frequencies_positive,
            'power_spectrum': power_spectrum,
            'dominant_frequencies': dominant_frequencies[:10],  # Top 10
            'dominant_periods': dominant_periods[:10],
            'dominant_powers': dominant_powers[:10],
            'total_variance': np.var(data),
            'explained_variance_ratio': dominant_powers[:10] / np.sum(power_spectrum)
        }
        
        logger.info(f"Frequency analysis complete for {data_type} data. "
                   f"Found {len(dominant_frequencies)} dominant frequencies.")
        
        return results
    
    def extract_wave_components(self, num_components: int = 5) -> Dict:
        """
        Extract wave function components at multiple time scales.
        
        Parameters
        ----------
        num_components : int
            Number of dominant wave components to extract per time scale
            
        Returns
        -------
        Dict
            Dictionary containing wave components for each time scale
        """
        wave_components = {}
        
        for data_type in ['monthly', 'annual']:
            freq_analysis = self.analyze_frequency_components(data_type)
            
            # Extract top components
            components = []
            for i in range(min(num_components, len(freq_analysis['dominant_frequencies']))):
                frequency = freq_analysis['dominant_frequencies'][i]
                period = freq_analysis['dominant_periods'][i]
                amplitude = np.sqrt(freq_analysis['dominant_powers'][i])
                
                # Estimate phase by fitting sine wave
                if data_type == 'monthly':
                    x = np.arange(len(self.monthly_data))
                    y = self.monthly_data['monthly_total'].values
                elif data_type == 'annual':
                    x = np.arange(len(self.annual_data))
                    y = self.annual_data['annual_total'].values
                
                # Fit sine wave to estimate phase
                try:
                    def sine_wave(t, A, omega, phi, offset):
                        return A * np.sin(omega * t + phi) + offset
                    
                    omega = 2 * np.pi * frequency / freq_analysis['sampling_frequency']
                    initial_guess = [amplitude, omega, 0, np.mean(y)]
                    
                    popt, _ = curve_fit(sine_wave, x, y, p0=initial_guess, maxfev=1000)
                    fitted_amplitude, fitted_omega, phase, offset = popt
                    
                except:
                    # If fitting fails, use default values
                    phase = 0
                    offset = np.mean(y)
                    fitted_amplitude = amplitude
                
                component = {
                    'frequency': frequency,
                    'period': period,
                    'amplitude': fitted_amplitude,
                    'phase': phase,
                    'offset': offset,
                    'power': freq_analysis['dominant_powers'][i],
                    'variance_explained': freq_analysis['explained_variance_ratio'][i]
                }
                components.append(component)
            
            wave_components[data_type] = components
            
        self.wave_components = wave_components
        logger.info(f"Extracted wave components for {len(wave_components)} time scales.")
        
        return wave_components
    
    def generate_wave_function(self, target_length: int, 
                             time_scale: str = 'monthly') -> np.ndarray:
        """
        Generate synthetic precipitation using wave function components.
        
        Parameters
        ----------
        target_length : int
            Length of synthetic series to generate
        time_scale : str
            Time scale for generation ('monthly' or 'annual')
            
        Returns
        -------
        np.ndarray
            Synthetic precipitation time series
        """
        if time_scale not in self.wave_components:
            raise ValueError(f"Wave components not available for {time_scale}")
        
        components = self.wave_components[time_scale]
        
        # Create time vector
        t = np.arange(target_length)
        
        # Initialize synthetic series
        synthetic_series = np.zeros(target_length)
        
        # Add each wave component
        for component in components:
            frequency = component['frequency']
            amplitude = component['amplitude']
            phase = component['phase']
            offset = component['offset']
            
            # Determine sampling frequency based on time scale
            if time_scale == 'monthly':
                sampling_freq = 12
            else:  # annual
                sampling_freq = 1
            
            omega = 2 * np.pi * frequency / sampling_freq
            wave = amplitude * np.sin(omega * t + phase)
            synthetic_series += wave
        
        # Add offset (mean level)
        if components:
            mean_offset = np.mean([comp['offset'] for comp in components])
            synthetic_series += mean_offset
        
        # Ensure non-negative values (precipitation can't be negative)
        synthetic_series = np.maximum(synthetic_series, 0)
        
        logger.info(f"Generated synthetic {time_scale} series of length {target_length}")
        
        return synthetic_series
    
    def characterize_cycles(self) -> Dict:
        """
        Characterize different types of cycles in the precipitation data.
        
        Returns
        -------
        Dict
            Dictionary containing cycle characterization
        """
        cycle_characterization = {}
        
        for data_type in ['monthly', 'annual']:
            if data_type in self.wave_components:
                components = self.wave_components[data_type]
                
                # Classify cycles by period length
                short_cycles = []  # < 2 years
                medium_cycles = []  # 2-10 years
                long_cycles = []  # > 10 years
                
                for comp in components:
                    period = comp['period']
                    
                    if data_type == 'monthly':
                        period_years = period / 12  # Convert months to years
                    else:
                        period_years = period
                    
                    if period_years < 2:
                        short_cycles.append(comp)
                    elif period_years <= 10:
                        medium_cycles.append(comp)
                    else:
                        long_cycles.append(comp)
                
                cycle_characterization[data_type] = {
                    'short_cycles': short_cycles,
                    'medium_cycles': medium_cycles,
                    'long_cycles': long_cycles,
                    'total_components': len(components)
                }
        
        return cycle_characterization
    
    def plot_wave_analysis(self, save_path: Optional[str] = None):
        """
        Create comprehensive plots of wave function analysis.
        
        Parameters
        ----------
        save_path : str, optional
            Path to save the plot
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Wave Function Analysis of Precipitation Data', fontsize=16)
        
        # Plot 1: Original time series
        axes[0, 0].plot(self.monthly_data.index, self.monthly_data['monthly_total'])
        axes[0, 0].set_title('Monthly Precipitation Totals')
        axes[0, 0].set_ylabel('Precipitation (mm)')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Power spectrum
        if 'monthly' in self.wave_components:
            freq_analysis = self.analyze_frequency_components('monthly')
            axes[0, 1].semilogy(freq_analysis['frequencies'], 
                               freq_analysis['power_spectrum'])
            axes[0, 1].set_title('Power Spectrum (Monthly Data)')
            axes[0, 1].set_xlabel('Frequency (cycles/year)')
            axes[0, 1].set_ylabel('Power')
            axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Synthetic vs Original (Monthly)
        if len(self.monthly_data) > 0:
            synthetic_monthly = self.generate_wave_function(
                len(self.monthly_data), 'monthly'
            )
            axes[1, 0].plot(self.monthly_data.index, 
                           self.monthly_data['monthly_total'], 
                           label='Original', alpha=0.7)
            axes[1, 0].plot(self.monthly_data.index, synthetic_monthly, 
                           label='Synthetic', alpha=0.7)
            axes[1, 0].set_title('Original vs Synthetic (Monthly)')
            axes[1, 0].set_ylabel('Precipitation (mm)')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Cycle characterization
        cycle_char = self.characterize_cycles()
        if 'monthly' in cycle_char:
            char = cycle_char['monthly']
            cycle_types = ['Short\n(<2 yr)', 'Medium\n(2-10 yr)', 'Long\n(>10 yr)']
            cycle_counts = [len(char['short_cycles']), 
                          len(char['medium_cycles']), 
                          len(char['long_cycles'])]
            
            axes[1, 1].bar(cycle_types, cycle_counts, 
                          color=['lightblue', 'orange', 'lightgreen'])
            axes[1, 1].set_title('Cycle Distribution')
            axes[1, 1].set_ylabel('Number of Components')
            axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")
        
        plt.show()


def analyze_precipitation_waves(time_series: pd.DataFrame, 
                              num_components: int = 5) -> WaveFunctionAnalyzer:
    """
    Convenience function to perform complete wave function analysis.
    
    Parameters
    ----------
    time_series : pd.DataFrame
        Time series with datetime index and 'PRCP' column
    num_components : int
        Number of wave components to extract per time scale
        
    Returns
    -------
    WaveFunctionAnalyzer
        Configured analyzer with extracted wave components
    """
    analyzer = WaveFunctionAnalyzer(time_series)
    analyzer.extract_wave_components(num_components)
    
    return analyzer


# Additional utility functions for enhanced wave analysis

def combine_wave_frequencies(high_freq_components: List[Dict], 
                           low_freq_components: List[Dict],
                           weights: Tuple[float, float] = (0.7, 0.3)) -> List[Dict]:
    """
    Combine high and low frequency wave components with specified weights.
    
    Parameters
    ----------
    high_freq_components : List[Dict]
        High frequency wave components (short-term cycles)
    low_freq_components : List[Dict] 
        Low frequency wave components (long-term cycles)
    weights : Tuple[float, float]
        Weights for (high_freq, low_freq) components
        
    Returns
    -------
    List[Dict]
        Combined wave components
    """
    high_weight, low_weight = weights
    
    combined_components = []
    
    # Weight high frequency components
    for comp in high_freq_components:
        weighted_comp = comp.copy()
        weighted_comp['amplitude'] *= high_weight
        weighted_comp['power'] *= high_weight
        combined_components.append(weighted_comp)
    
    # Weight low frequency components  
    for comp in low_freq_components:
        weighted_comp = comp.copy()
        weighted_comp['amplitude'] *= low_weight
        weighted_comp['power'] *= low_weight
        combined_components.append(weighted_comp)
    
    return combined_components


def validate_wave_parameters(components: List[Dict]) -> bool:
    """
    Validate that wave function parameters are physically reasonable.
    
    Parameters
    ----------
    components : List[Dict]
        List of wave components to validate
        
    Returns
    -------
    bool
        True if all parameters are valid
    """
    for comp in components:
        # Check for required keys
        required_keys = ['frequency', 'period', 'amplitude', 'phase']
        if not all(key in comp for key in required_keys):
            return False
            
        # Check for reasonable values
        if comp['frequency'] <= 0 or comp['period'] <= 0:
            return False
        if comp['amplitude'] < 0:
            return False
        if not (-2*np.pi <= comp['phase'] <= 2*np.pi):
            return False
            
    return True


if __name__ == "__main__":
    # Example usage and testing
    print("Wave Function Analysis Module for PrecipGen")
    print("Use: analyzer = analyze_precipitation_waves(your_time_series)")
    
    # Quick test with sample data
    try:
        from time_series import TimeSeries
        import os
        
        # Try to load test data if available
        test_file = os.path.join("tests", "GrandJunction", "USW00023066_data.csv")
        if os.path.exists(test_file):
            print(f"\nTesting with {test_file}...")
            ts = TimeSeries()
            ts.load_and_preprocess(test_file)
            ts.trim(2000, 2020)  # Use subset for faster testing
            
            # Run wave analysis
            analyzer = analyze_precipitation_waves(ts.get_data(), num_components=3)
            
            # Display results
            print(f"Wave analysis complete!")
            print(f"Monthly components: {len(analyzer.wave_components.get('monthly', []))}")
            print(f"Annual components: {len(analyzer.wave_components.get('annual', []))}")
            
            # Show cycle characterization
            cycles = analyzer.characterize_cycles()
            for scale, char in cycles.items():
                print(f"\n{scale.title()} scale cycles:")
                print(f"  Short cycles: {len(char['short_cycles'])}")
                print(f"  Medium cycles: {len(char['medium_cycles'])}")
                print(f"  Long cycles: {len(char['long_cycles'])}")
        else:
            print("Test data not found - module loaded successfully")
            
    except ImportError:
        print("Dependencies not available for testing - module structure complete")
