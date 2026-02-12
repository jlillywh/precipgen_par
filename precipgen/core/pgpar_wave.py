#!/usr/bin/env python3
"""
PrecipGen Parameter Wave Analysis Module

This module analyzes the temporal evolution of PrecipGen parameters (PWW, PWD, alpha, beta)
using wave function decomposition. It extracts parameters over time using sliding windows
and characterizes their evolution with frequency analysis and wave fitting.
"""

import numpy as np
import pandas as pd
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple
import json
import logging
from datetime import datetime

from precipgen.core.pgpar import calculate_params
from precipgen.core.time_series import TimeSeries

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PrecipGenPARWave:
    """
    Analyzes temporal evolution of PrecipGen parameters using wave function decomposition.
    
    This class extracts PWW, PWD, alpha, and beta parameters over time using sliding windows,
    then performs frequency analysis to characterize their temporal evolution with wave functions.
    """
    
    def __init__(self, time_series: TimeSeries, window_size: int = 10, 
                 overlap: float = 0.5, min_data_threshold: float = 0.8):
        """
        Initialize the PrecipGen parameter wave analyzer.
        
        Parameters
        ----------
        time_series : TimeSeries
            Time series object containing precipitation data
        window_size : int
            Size of sliding window in years for parameter extraction
        overlap : float
            Overlap fraction between windows (0.0 to 1.0)
        min_data_threshold : float
            Minimum fraction of data required in window for parameter calculation
        """
        self.time_series = time_series
        self.window_size = window_size
        self.overlap = overlap
        self.min_data_threshold = min_data_threshold
        
        self.parameter_history = None
        self.wave_components = {}
        self.fitted_parameters = {}
        
        logger.info(f"Initialized PrecipGenPARWave with {window_size}-year windows, "
                   f"{overlap:.1%} overlap")
    
    def extract_parameter_history(self) -> pd.DataFrame:
        """
        Extract PrecipGen parameters over time using sliding windows.
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: year, PWW, PWD, alpha, beta, data_coverage
        """
        data = self.time_series.get_data()
        
        if data.empty:
            raise ValueError("Time series data is empty")
        
        # Get year range
        start_year = data.index.year.min()
        end_year = data.index.year.max()
        
        # Calculate window step size
        step_size = max(1, int(self.window_size * (1 - self.overlap)))
        
        parameter_records = []
        
        # Slide window through time
        for window_start in range(start_year, end_year - self.window_size + 2, step_size):
            window_end = window_start + self.window_size - 1
            
            # Extract window data
            window_mask = ((data.index.year >= window_start) & 
                          (data.index.year <= window_end))
            window_data = data[window_mask].copy()
            
            if len(window_data) == 0:
                continue
            
            # Check data coverage
            expected_days = (pd.Timestamp(f"{window_end+1}-01-01") - 
                           pd.Timestamp(f"{window_start}-01-01")).days
            actual_days = len(window_data)
            data_coverage = actual_days / expected_days            
            if data_coverage < self.min_data_threshold:
                logger.warning(f"Skipping window {window_start}-{window_end}: "
                             f"insufficient data coverage ({data_coverage:.2%})")
                continue
            
            try:
                # Calculate parameters for this window
                monthly_params = calculate_params(window_data)
                  # Aggregate monthly parameters to yearly averages for this window
                params = {
                    'PWW': monthly_params['PWW'].mean(),
                    'PWD': monthly_params['PWD'].mean(), 
                    'alpha': monthly_params['ALPHA'].mean(),
                    'beta': monthly_params['BETA'].mean()
                }
                
                # Store results
                record = {
                    'year': window_start + self.window_size // 2,  # Center year
                    'window_start': window_start,
                    'window_end': window_end,
                    'PWW': params['PWW'],
                    'PWD': params['PWD'],                    'alpha': params['alpha'],
                    'beta': params['beta'],
                    'data_coverage': data_coverage
                }
                parameter_records.append(record)
                
                logger.debug(f"Extracted parameters for {window_start}-{window_end}: "
                           f"PWW={params['PWW']:.3f}, PWD={params['PWD']:.3f}")
                
            except Exception as e:
                logger.warning(f"Failed to calculate parameters for window "
                             f"{window_start}-{window_end}: {e}")
                continue
        
        if not parameter_records:
            raise ValueError("No valid parameter windows could be extracted")
        
        self.parameter_history = pd.DataFrame(parameter_records)
        
        logger.info(f"Extracted parameters for {len(parameter_records)} time windows "
                   f"spanning {parameter_records[0]['year']} to {parameter_records[-1]['year']}")
        
        return self.parameter_history
    
    def analyze_parameter_waves(self, parameters: List[str] = None, 
                              num_components: int = 5) -> Dict:
        """
        Analyze wave components for each parameter's temporal evolution.
        
        Parameters
        ----------
        parameters : List[str], optional
            List of parameters to analyze ['PWW', 'PWD', 'alpha', 'beta']
        num_components : int
            Number of dominant wave components to extract per parameter
            
        Returns
        -------
        Dict
            Dictionary containing wave components for each parameter
        """
        if self.parameter_history is None:
            raise ValueError("Must extract parameter history first")
        
        if parameters is None:
            parameters = ['PWW', 'PWD', 'alpha', 'beta']
        
        wave_results = {}
        
        for param in parameters:
            if param not in self.parameter_history.columns:
                logger.warning(f"Parameter {param} not found in history")
                continue
            
            # Get parameter time series
            years = self.parameter_history['year'].values
            values = self.parameter_history[param].values
            
            # Remove any NaN values
            valid_mask = ~np.isnan(values)
            years_clean = years[valid_mask]
            values_clean = values[valid_mask]
            
            if len(values_clean) < 3:
                logger.warning(f"Insufficient data for {param} wave analysis")
                continue
            
            # Perform frequency analysis
            wave_components = self._analyze_frequency_components(
                years_clean, values_clean, param, num_components
            )
            
            wave_results[param] = wave_components
            
        self.wave_components = wave_results
        logger.info(f"Completed wave analysis for {len(wave_results)} parameters")
        
        return wave_results
    
    def _analyze_frequency_components(self, years: np.ndarray, values: np.ndarray,
                                    param_name: str, num_components: int) -> Dict:
        """
        Analyze frequency components for a single parameter.
        
        Parameters
        ----------
        years : np.ndarray
            Years corresponding to parameter values
        values : np.ndarray
            Parameter values
        param_name : str
            Name of the parameter
        num_components : int
            Number of components to extract
            
        Returns
        -------
        Dict
            Dictionary containing wave analysis results
        """
        # Detrend the data
        detrended_values = signal.detrend(values)
        
        # Perform FFT
        n = len(detrended_values)
        fft_values = fft(detrended_values)
        frequencies = fftfreq(n, d=1.0)  # Assuming annual sampling
        
        # Get positive frequencies only
        positive_freq_idx = frequencies > 0
        frequencies_pos = frequencies[positive_freq_idx]
        magnitude_spectrum = np.abs(fft_values[positive_freq_idx])
        power_spectrum = magnitude_spectrum ** 2
        
        # Find peaks
        if len(power_spectrum) > 0:
            peak_threshold = np.max(power_spectrum) * 0.1
            peak_indices = signal.find_peaks(power_spectrum, height=peak_threshold)[0]
            
            if len(peak_indices) > 0:
                # Sort by power
                peak_powers = power_spectrum[peak_indices]
                sorted_indices = np.argsort(peak_powers)[::-1]
                peak_indices = peak_indices[sorted_indices]
                
                # Extract top components
                components = []
                for i, peak_idx in enumerate(peak_indices[:num_components]):
                    frequency = frequencies_pos[peak_idx]
                    period = 1.0 / frequency if frequency > 0 else np.inf
                    
                    # Correct amplitude scaling for real signals
                    amplitude = 2.0 * magnitude_spectrum[peak_idx] / n
                    power = power_spectrum[peak_idx]
                    
                    # Fit sine wave to get phase using detrended data
                    phase = self._estimate_phase(years, detrended_values, frequency)
                    
                    component = {
                        'frequency': frequency,
                        'period': period,
                        'amplitude': amplitude,
                        'phase': phase,
                        'power': power,
                        'variance_explained': power / np.sum(power_spectrum)
                    }
                    components.append(component)
            else:
                components = []
        else:
            components = []
        
        # Calculate trend
        trend_slope, trend_intercept = np.polyfit(years, values, 1)
        
        return {
            'parameter': param_name,
            'n_points': len(values),
            'mean_value': np.mean(values),
            'std_value': np.std(values),
            'trend_slope': trend_slope,
            'trend_intercept': trend_intercept,
            'total_variance': np.var(values),
            'components': components,
            'frequencies': frequencies_pos,
            'power_spectrum': power_spectrum
        }
    
    def _estimate_phase(self, years: np.ndarray, values: np.ndarray, 
                       frequency: float) -> float:
        """
        Estimate phase of a sine wave component.
        
        Parameters
        ----------
        years : np.ndarray
            Time points
        values : np.ndarray
            Parameter values
        frequency : float
            Frequency of the component
            
        Returns
        -------
        float
            Estimated phase
        """
        try:
            def sine_wave(t, A, phi, offset):
                return A * np.sin(2 * np.pi * frequency * t + phi) + offset
            
            # Initial guess
            amplitude_guess = np.std(values)
            offset_guess = np.mean(values)
            phase_guess = 0.0
            
            popt, _ = curve_fit(sine_wave, years, values, 
                              p0=[amplitude_guess, phase_guess, offset_guess],
                              maxfev=1000)
            
            return popt[1]  # phase
        except:
            return 0.0
    
    def fit_parameter_evolution(self, parameters: List[str] = None) -> Dict:
        """
        Fit wave functions to parameter evolution and extract fitted parameters.
        
        Parameters
        ----------
        parameters : List[str], optional
            Parameters to fit
            
        Returns
        -------
        Dict
            Dictionary containing fitted wave function parameters
        """
        if not self.wave_components:
            raise ValueError("Must analyze wave components first")
        
        if parameters is None:
            parameters = list(self.wave_components.keys())
        
        fitted_results = {}
        
        for param in parameters:
            if param not in self.wave_components:
                continue
            
            wave_data = self.wave_components[param]
            components = wave_data['components']
            
            if not components:
                logger.warning(f"No wave components found for {param}")
                continue
            
            # Characterize components by period
            short_term = []  # < 5 years
            medium_term = []  # 5-20 years  
            long_term = []  # > 20 years
            
            for comp in components:
                period = comp['period']
                if period < 5:
                    short_term.append(comp)
                elif period <= 20:
                    medium_term.append(comp)
                else:
                    long_term.append(comp)
            
            # Summary statistics
            total_amplitude = sum(comp['amplitude'] for comp in components)
            dominant_period = components[0]['period'] if components else None
            dominant_frequency = components[0]['frequency'] if components else None
            
            fitted_params = {
                'parameter': param,
                'trend': {
                    'slope': wave_data['trend_slope'],
                    'intercept': wave_data['trend_intercept']
                },
                'wave_summary': {
                    'total_amplitude': total_amplitude,
                    'dominant_period': dominant_period,
                    'dominant_frequency': dominant_frequency,
                    'n_components': len(components)
                },
                'component_groups': {
                    'short_term': short_term,
                    'medium_term': medium_term,
                    'long_term': long_term
                },
                'all_components': components
            }
            
            fitted_results[param] = fitted_params
        
        self.fitted_parameters = fitted_results
        logger.info(f"Fitted wave parameters for {len(fitted_results)} parameters")
        
        return fitted_results
    
    def generate_synthetic_parameters(self, target_years: np.ndarray,
                                    parameters: List[str] = None) -> pd.DataFrame:
        """
        Generate synthetic parameter values using fitted wave functions.
        
        Parameters
        ----------
        target_years : np.ndarray
            Years for which to generate synthetic parameters
        parameters : List[str], optional
            Parameters to generate
            
        Returns
        -------
        pd.DataFrame
            DataFrame with synthetic parameter values
        """
        if not self.fitted_parameters:
            raise ValueError("Must fit parameter evolution first")
        
        if parameters is None:
            parameters = list(self.fitted_parameters.keys())
        
        synthetic_data = {'year': target_years}
        
        for param in parameters:
            if param not in self.fitted_parameters:
                continue
            
            fitted = self.fitted_parameters[param]
            components = fitted['all_components']
            trend = fitted['trend']
            
            # Start with trend
            synthetic_values = (trend['slope'] * target_years + 
                              trend['intercept'])
            
            # Add wave components
            for comp in components:
                frequency = comp['frequency']
                amplitude = comp['amplitude']
                phase = comp['phase']
                
                wave = amplitude * np.sin(2 * np.pi * frequency * target_years + phase)
                synthetic_values += wave
            
            # Apply bounds constraints for probability parameters
            if param in ['PWW', 'PWD']:
                # Constrain to [0, 1] for probability parameters
                synthetic_values = np.clip(synthetic_values, 0.0, 1.0)
            elif param in ['alpha', 'beta']:
                # Constrain to positive values for gamma parameters
                synthetic_values = np.clip(synthetic_values, 0.01, None)  # Small minimum to avoid zero
            
            synthetic_data[param] = synthetic_values
        
        return pd.DataFrame(synthetic_data)
    
    def export_wave_parameters(self, filepath: str, format: str = 'json'):
        """
        Export wave function parameters to file.
        
        Parameters
        ----------
        filepath : str
            Output file path
        format : str
            Output format ('json' or 'csv')
        """
        if not self.fitted_parameters:
            raise ValueError("No fitted parameters to export")
        
        if format.lower() == 'json':
            # Convert numpy types to native Python types for JSON serialization
            exportable_data = {}
            
            for param, data in self.fitted_parameters.items():
                exportable_data[param] = self._convert_for_json(data)
            
            # Add metadata
            exportable_data['metadata'] = {
                'generated_date': datetime.now().isoformat(),
                'window_size_years': self.window_size,
                'overlap_fraction': self.overlap,
                'min_data_threshold': self.min_data_threshold,
                'parameters_analyzed': list(self.fitted_parameters.keys())
            }
            
            with open(filepath, 'w') as f:
                json.dump(exportable_data, f, indent=2)
                
        elif format.lower() == 'csv':
            # Export component summary to CSV
            records = []
            for param, data in self.fitted_parameters.items():
                for i, comp in enumerate(data['all_components']):
                    record = {
                        'parameter': param,
                        'component_index': i,
                        'frequency': comp['frequency'],
                        'period': comp['period'],
                        'amplitude': comp['amplitude'],
                        'phase': comp['phase'],
                        'power': comp['power'],
                        'variance_explained': comp['variance_explained']
                    }
                    records.append(record)
            
            df = pd.DataFrame(records)
            df.to_csv(filepath, index=False)
        
        logger.info(f"Exported wave parameters to {filepath}")
    
    def _convert_for_json(self, obj):
        """Convert numpy types to JSON-serializable types."""
        if isinstance(obj, dict):
            return {key: self._convert_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_for_json(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        else:
            return obj
    
    def plot_parameter_evolution(self, save_path: Optional[str] = None):
        """
        Create comprehensive plots of parameter evolution and wave analysis.
        
        Parameters
        ----------
        save_path : str, optional
            Path to save the plot
        """
        if self.parameter_history is None:
            raise ValueError("Must extract parameter history first")
        
        params = ['PWW', 'PWD', 'alpha', 'beta']
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('PrecipGen Parameter Evolution Analysis', fontsize=16)
        
        axes = axes.flatten()
        
        for i, param in enumerate(params):
            if param not in self.parameter_history.columns:
                continue
            
            ax = axes[i]
            years = self.parameter_history['year']
            values = self.parameter_history[param]
            
            # Plot original data
            ax.scatter(years, values, alpha=0.6, color='blue', s=30, 
                      label='Extracted Values')
            
            # Plot trend line if available
            if param in self.fitted_parameters:
                fitted = self.fitted_parameters[param]
                trend = fitted['trend']
                trend_line = trend['slope'] * years + trend['intercept']
                ax.plot(years, trend_line, 'r--', alpha=0.8, 
                       label=f'Trend (slope={trend["slope"]:.4f})')
                
                # Plot synthetic reconstruction
                synthetic = self.generate_synthetic_parameters(years.values, [param])
                ax.plot(years, synthetic[param], 'g-', alpha=0.7, linewidth=2,
                       label='Wave Reconstruction')
            
            ax.set_title(f'{param} Evolution')
            ax.set_xlabel('Year')
            ax.set_ylabel(param)
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Parameter evolution plot saved to {save_path}")
        
        plt.show()
    
    def plot_wave_components(self, save_path: Optional[str] = None):
        """
        Plot wave component analysis for each parameter.
        
        Parameters
        ----------
        save_path : str, optional
            Path to save the plot
        """
        if not self.wave_components:
            raise ValueError("Must analyze wave components first")
        
        params = list(self.wave_components.keys())
        n_params = len(params)
        
        fig, axes = plt.subplots(n_params, 2, figsize=(15, 4*n_params))
        fig.suptitle('Wave Component Analysis', fontsize=16)
        
        if n_params == 1:
            axes = axes.reshape(1, -1)
        
        for i, param in enumerate(params):
            wave_data = self.wave_components[param]
            components = wave_data['components']
            
            # Plot power spectrum
            ax1 = axes[i, 0]
            frequencies = wave_data['frequencies']
            power_spectrum = wave_data['power_spectrum']
            
            ax1.semilogy(frequencies, power_spectrum, 'b-', alpha=0.7)
            
            # Mark dominant frequencies
            for comp in components[:3]:  # Top 3 components
                freq = comp['frequency']
                power = comp['power']
                ax1.axvline(freq, color='red', linestyle='--', alpha=0.7)
                ax1.text(freq, power, f'P={comp["period"]:.1f}y', 
                        rotation=90, verticalalignment='bottom')
            
            ax1.set_title(f'{param} - Power Spectrum')
            ax1.set_xlabel('Frequency (cycles/year)')
            ax1.set_ylabel('Power')
            ax1.grid(True, alpha=0.3)
            
            # Plot component periods
            ax2 = axes[i, 1]
            if components:
                periods = [comp['period'] for comp in components]
                amplitudes = [comp['amplitude'] for comp in components]
                colors = ['red' if p < 5 else 'orange' if p <= 20 else 'green' 
                         for p in periods]
                
                bars = ax2.bar(range(len(components)), amplitudes, color=colors, alpha=0.7)
                ax2.set_title(f'{param} - Component Amplitudes')
                ax2.set_xlabel('Component Index')
                ax2.set_ylabel('Amplitude')
                ax2.set_xticks(range(len(components)))
                
                # Add period labels
                for j, (bar, period) in enumerate(zip(bars, periods)):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{period:.1f}y', ha='center', va='bottom')
            
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Wave components plot saved to {save_path}")
        
        plt.show()


def analyze_precipgen_parameter_waves(time_series: TimeSeries, 
                                    window_size: int = 10,
                                    overlap: float = 0.5,
                                    num_components: int = 5) -> PrecipGenPARWave:
    """
    Convenience function to perform complete PrecipGen parameter wave analysis.
    
    Parameters
    ----------
    time_series : TimeSeries
        Time series object containing precipitation data
    window_size : int
        Size of sliding window in years
    overlap : float
        Overlap fraction between windows
    num_components : int
        Number of wave components to extract per parameter
        
    Returns
    -------
    PrecipGenPARWave
        Configured analyzer with complete wave analysis
    """
    analyzer = PrecipGenPARWave(time_series, window_size, overlap)
    
    # Extract parameter history
    analyzer.extract_parameter_history()
    
    # Analyze wave components
    analyzer.analyze_parameter_waves(num_components=num_components)
    
    # Fit wave parameters
    analyzer.fit_parameter_evolution()
    
    return analyzer


if __name__ == "__main__":
    print("PrecipGen Parameter Wave Analysis Module")
    print("Use: analyzer = analyze_precipgen_parameter_waves(your_time_series)")
    
    # Quick test if test data is available
    try:
        import os
        
        test_file = os.path.join("tests", "GrandJunction", "USW00023066_data.csv")
        if os.path.exists(test_file):
            print(f"\nTesting with {test_file}...")
            
            # Load and prepare data
            ts = TimeSeries()
            ts.load_and_preprocess(test_file)
            ts.trim(1990, 2020)  # Use subset for testing
            
            # Run parameter wave analysis
            analyzer = analyze_precipgen_parameter_waves(ts, window_size=8, num_components=3)
            
            print(f"Analysis complete!")
            print(f"Extracted parameters for {len(analyzer.parameter_history)} windows")
            
            for param in ['PWW', 'PWD', 'alpha', 'beta']:
                if param in analyzer.wave_components:
                    n_components = len(analyzer.wave_components[param]['components'])
                    print(f"{param}: {n_components} wave components")
        else:
            print("Test data not found - module loaded successfully")
            
    except ImportError as e:
        print(f"Dependencies not available for testing: {e}")
