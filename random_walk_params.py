#!/usr/bin/env python3
"""
Random Walk Parameter Analysis Module

This module implements the random walk parameter estimation approach described in:
"Introducing Long-Term Variability via a Random Walk"

The module calculates volatility and reversion rate parameters for PrecipGen parameters
(PWW, PWD, alpha, beta) using overlapping 2-year windows from historical data.
These parameters enable mean-reverting random walk processes for long-term variability.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from typing import Dict, List, Optional, Tuple
import json
import logging
from datetime import datetime

from pgpar import calculate_params
from time_series import TimeSeries

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RandomWalkParameterAnalyzer:
    """
    Analyzes precipitation parameters to estimate volatility and reversion rates
    for mean-reverting random walk processes.
    
    This class implements the methodology described in the paper for capturing
    long-term variability in precipitation parameters through stochastic processes.
    """
    
    def __init__(self, time_series: TimeSeries, window_size: int = 2, 
                 seasonal_analysis: bool = False):
        """
        Initialize the random walk parameter analyzer.
        
        Parameters
        ----------
        time_series : TimeSeries
            Time series object containing precipitation data
        window_size : int
            Size of sliding window in years for parameter extraction (default=2)
        seasonal_analysis : bool
            If True, calculate separate parameters for each season (default=False)
        """
        self.time_series = time_series
        self.window_size = window_size
        self.seasonal_analysis = seasonal_analysis
        
        # Season definitions (month numbers)
        self.seasons = {
            'winter': [12, 1, 2],    # Dec, Jan, Feb
            'spring': [3, 4, 5],  # Mar, Apr, May
            'summer': [6, 7, 8],     # Jun, Jul, Aug
            'fall': [9, 10, 11]         # Sep, Oct, Nov
        }
        
        self.parameter_sequence = None
        self.seasonal_sequences = {}  # For seasonal analysis
        self.volatilities = {}
        self.reversion_rates = {}
        self.correlations = {}
        self.long_term_means = {}
        
        analysis_type = "seasonal" if seasonal_analysis else "annual"
        logger.info(f"Initialized RandomWalkParameterAnalyzer with {window_size}-year windows, {analysis_type} analysis")
    
    def extract_parameter_sequence(self) -> pd.DataFrame:
        """
        Extract parameter sequence using overlapping 2-year windows.
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: year, PWW, PWD, alpha, beta
        """
        data = self.time_series.get_data()
        
        if data.empty:
            raise ValueError("Time series data is empty")
        
        # Get year range
        start_year = data.index.year.min()
        end_year = data.index.year.max()
        
        if end_year - start_year + 1 < self.window_size:
            raise ValueError(f"Insufficient data: need at least {self.window_size} years")
        
        parameter_records = []
        
        # Slide window through time (1-year steps for overlapping windows)
        for window_start in range(start_year, end_year - self.window_size + 2):
            window_end = window_start + self.window_size - 1
            
            # Extract window data
            window_mask = ((data.index.year >= window_start) & 
                          (data.index.year <= window_end))
            window_data = data[window_mask].copy()
            
            if len(window_data) == 0:
                continue
            
            try:
                # Calculate parameters for this window
                monthly_params = calculate_params(window_data)
                
                # Aggregate to annual averages for this window
                params = {
                    'PWW': monthly_params['PWW'].mean(),
                    'PWD': monthly_params['PWD'].mean(), 
                    'alpha': monthly_params['ALPHA'].mean(),
                    'beta': monthly_params['BETA'].mean()
                }
                
                # Store results (center year of window)
                record = {
                    'year': window_start + self.window_size // 2,
                    'window_start': window_start,
                    'window_end': window_end,
                    'PWW': params['PWW'],
                    'PWD': params['PWD'],
                    'alpha': params['alpha'],
                    'beta': params['beta']
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
        
        self.parameter_sequence = pd.DataFrame(parameter_records)
        
        logger.info(f"Extracted parameter sequence for {len(parameter_records)} windows "
                   f"spanning {parameter_records[0]['year']} to {parameter_records[-1]['year']}")
        
        return self.parameter_sequence
    
    def extract_seasonal_parameter_sequences(self) -> Dict[str, pd.DataFrame]:
        """
        Extract parameter sequences for each season using overlapping windows.
        
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary with seasonal parameter sequences (winter, spring, summer, fall)
        """
        data = self.time_series.get_data()
        
        if data.empty:
            raise ValueError("Time series data is empty")
        
        # Get year range
        start_year = data.index.year.min()
        end_year = data.index.year.max()
        
        if end_year - start_year + 1 < self.window_size:
            raise ValueError(f"Insufficient data: need at least {self.window_size} years")
        
        seasonal_sequences = {}
        
        for season_name, season_months in self.seasons.items():
            logger.info(f"Extracting {season_name} parameter sequence (months {season_months})")
            
            parameter_records = []
            
            # Slide window through time (1-year steps for overlapping windows)
            for window_start in range(start_year, end_year - self.window_size + 2):
                window_end = window_start + self.window_size - 1
                
                # Extract window data for this season only
                window_mask = ((data.index.year >= window_start) & 
                              (data.index.year <= window_end) &
                              (data.index.month.isin(season_months)))
                window_data = data[window_mask].copy()
                
                if len(window_data) == 0:
                    logger.debug(f"No {season_name} data for window {window_start}-{window_end}")
                    continue
                
                # Check if we have sufficient seasonal data
                expected_seasonal_days = self._estimate_seasonal_days(window_start, window_end, season_months)
                actual_days = len(window_data)
                seasonal_coverage = actual_days / expected_seasonal_days if expected_seasonal_days > 0 else 0
                
                if seasonal_coverage < 0.7:  # Require at least 70% of seasonal data
                    logger.debug(f"Insufficient {season_name} data for window {window_start}-{window_end}: "
                               f"{seasonal_coverage:.1%} coverage")
                    continue
                
                try:
                    # Calculate parameters for this seasonal window
                    monthly_params = calculate_params(window_data)
                    
                    # Aggregate monthly parameters to seasonal averages for this window
                    params = {
                        'PWW': monthly_params['PWW'].mean(),
                        'PWD': monthly_params['PWD'].mean(), 
                        'alpha': monthly_params['ALPHA'].mean(),
                        'beta': monthly_params['BETA'].mean()
                    }
                    
                    # Store results (center year of window)
                    record = {
                        'year': window_start + self.window_size // 2,
                        'window_start': window_start,
                        'window_end': window_end,
                        'season': season_name,
                        'PWW': params['PWW'],
                        'PWD': params['PWD'],
                        'alpha': params['alpha'],
                        'beta': params['beta'],
                        'seasonal_coverage': seasonal_coverage
                    }
                    parameter_records.append(record)
                    
                    logger.debug(f"Extracted {season_name} parameters for {window_start}-{window_end}: "
                               f"PWW={params['PWW']:.3f}, PWD={params['PWD']:.3f}")
                    
                except Exception as e:
                    logger.warning(f"Failed to calculate {season_name} parameters for window "
                                 f"{window_start}-{window_end}: {e}")
                    continue
            
            if parameter_records:
                seasonal_sequences[season_name] = pd.DataFrame(parameter_records)
                logger.info(f"Extracted {season_name} parameters for {len(parameter_records)} windows")
            else:
                logger.warning(f"No valid {season_name} parameter windows could be extracted")
        
        self.seasonal_sequences = seasonal_sequences
        return seasonal_sequences
    
    def _estimate_seasonal_days(self, start_year: int, end_year: int, season_months: List[int]) -> int:
        """
        Estimate the expected number of days for a season across multiple years.
        
        Parameters
        ----------
        start_year : int
            Start year of window
        end_year : int
            End year of window
        season_months : List[int]
            List of month numbers for the season
            
        Returns
        -------
        int
            Estimated number of seasonal days
        """
        total_days = 0
        
        for year in range(start_year, end_year + 1):
            for month in season_months:
                if month == 2:  # February
                    # Check for leap year
                    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                        total_days += 29
                    else:
                        total_days += 28
                elif month in [4, 6, 9, 11]:  # April, June, September, November
                    total_days += 30
                else:  # All other months
                    total_days += 31
        
        return total_days
    
    def calculate_volatilities(self) -> Dict[str, float]:
        """
        Calculate volatility (σ) for each parameter using first-order differences.
        
        Formula: σ_x = sqrt(1/(N-1) * sum((x_{t+1} - x_t)^2))
        
        Returns
        -------
        Dict[str, float]
            Dictionary with volatility values for each parameter
        """
        if self.parameter_sequence is None:
            raise ValueError("Must extract parameter sequence first")
        
        params = ['PWW', 'PWD', 'alpha', 'beta']
        volatilities = {}
        
        for param in params:
            if param not in self.parameter_sequence.columns:
                logger.warning(f"Parameter {param} not found in sequence")
                continue
            
            values = self.parameter_sequence[param].values
            
            # Calculate first-order differences
            differences = np.diff(values)
            
            # Calculate volatility (standard deviation of differences)
            volatility = np.std(differences, ddof=1)
            volatilities[param] = volatility
            
            logger.info(f"Volatility for {param}: {volatility:.6f}")
        
        self.volatilities = volatilities
        return volatilities
    
    def calculate_reversion_rates(self) -> Dict[str, float]:
        """
        Calculate reversion rate (r) for each parameter using regression analysis.
        
        The reversion rate is estimated by regressing parameter changes on parameter levels:
        Δx_t = r * (μ - x_{t-1}) + ε
        
        Returns
        -------
        Dict[str, float]
            Dictionary with reversion rate values for each parameter
        """
        if self.parameter_sequence is None:
            raise ValueError("Must extract parameter sequence first")
        
        params = ['PWW', 'PWD', 'alpha', 'beta']
        reversion_rates = {}
        
        for param in params:
            if param not in self.parameter_sequence.columns:
                logger.warning(f"Parameter {param} not found in sequence")
                continue
            
            values = self.parameter_sequence[param].values
            
            if len(values) < 3:
                logger.warning(f"Insufficient data for {param} reversion rate calculation")
                continue
            
            # Calculate differences and lagged values
            differences = np.diff(values)  # Δx_t = x_t - x_{t-1}
            lagged_values = values[:-1]    # x_{t-1}
            mean_value = np.mean(values)   # μ
            
            # Mean-adjusted lagged values: (μ - x_{t-1})
            mean_adjusted = mean_value - lagged_values
            
            # Regression: Δx_t = r * (μ - x_{t-1}) + ε
            # This gives us the reversion rate directly
            if np.var(mean_adjusted) > 1e-10:  # Avoid division by zero
                slope, intercept, r_value, p_value, std_err = stats.linregress(mean_adjusted, differences)
                reversion_rate = slope
            else:
                logger.warning(f"No variation in {param} values - setting reversion rate to 0")
                reversion_rate = 0.0
            
            # Ensure reversion rate is positive (faster reversion for larger deviations)
            reversion_rate = abs(reversion_rate)
            
            reversion_rates[param] = reversion_rate
            
            logger.info(f"Reversion rate for {param}: {reversion_rate:.6f}")
        
        self.reversion_rates = reversion_rates
        return reversion_rates
    
    def calculate_correlations(self) -> Dict[str, float]:
        """
        Calculate correlations between key parameter pairs.
        
        Focus on PWW-PWD and PWW-alpha correlations as mentioned in the paper.
        
        Returns
        -------
        Dict[str, float]
            Dictionary with correlation coefficients
        """
        if self.parameter_sequence is None:
            raise ValueError("Must extract parameter sequence first")
        
        correlations = {}
        
        # Key correlations mentioned in the paper
        correlation_pairs = [
            ('PWW', 'PWD'),
            ('PWW', 'alpha'),
            ('PWD', 'alpha'),
            ('alpha', 'beta')
        ]
        
        for param1, param2 in correlation_pairs:
            if param1 in self.parameter_sequence.columns and param2 in self.parameter_sequence.columns:
                values1 = self.parameter_sequence[param1].values
                values2 = self.parameter_sequence[param2].values
                
                # Remove any NaN pairs
                valid_mask = ~(np.isnan(values1) | np.isnan(values2))
                if np.sum(valid_mask) > 2:
                    corr_coef = np.corrcoef(values1[valid_mask], values2[valid_mask])[0, 1]
                    correlations[f"{param1}_{param2}"] = corr_coef
                    
                    logger.info(f"Correlation {param1}-{param2}: {corr_coef:.4f}")
                else:
                    logger.warning(f"Insufficient valid data for {param1}-{param2} correlation")
        
        self.correlations = correlations
        return correlations
    
    def calculate_long_term_means(self) -> Dict[str, float]:
        """
        Calculate long-term historical means for each parameter.
        
        These serve as the target values (T_new) in the random walk equation.
        
        Returns
        -------
        Dict[str, float]
            Dictionary with long-term mean values for each parameter
        """
        if self.parameter_sequence is None:
            raise ValueError("Must extract parameter sequence first")
        
        params = ['PWW', 'PWD', 'alpha', 'beta']
        means = {}
        
        for param in params:
            if param in self.parameter_sequence.columns:
                mean_value = self.parameter_sequence[param].mean()
                means[param] = mean_value
                
                logger.info(f"Long-term mean for {param}: {mean_value:.6f}")
        
        self.long_term_means = means
        return means
    
    def calculate_seasonal_volatilities(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate volatility (σ) for each parameter by season using first-order differences.
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            Nested dictionary: {season: {parameter: volatility}}
        """
        if not self.seasonal_sequences:
            raise ValueError("Must extract seasonal parameter sequences first")
        
        seasonal_volatilities = {}
        params = ['PWW', 'PWD', 'alpha', 'beta']
        
        for season_name, season_data in self.seasonal_sequences.items():
            season_volatilities = {}
            
            for param in params:
                if param not in season_data.columns:
                    logger.warning(f"Parameter {param} not found in {season_name} sequence")
                    continue
                
                values = season_data[param].values
                
                if len(values) < 3:
                    logger.warning(f"Insufficient {season_name} data for {param} volatility calculation")
                    continue
                
                # Calculate first-order differences
                differences = np.diff(values)
                
                # Calculate volatility (standard deviation of differences)
                volatility = np.std(differences, ddof=1)
                season_volatilities[param] = volatility
                
                logger.info(f"{season_name} volatility for {param}: {volatility:.6f}")
            
            seasonal_volatilities[season_name] = season_volatilities
        
        return seasonal_volatilities
    
    def calculate_seasonal_reversion_rates(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate reversion rate (r) for each parameter by season using regression analysis.
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            Nested dictionary: {season: {parameter: reversion_rate}}
        """
        if not self.seasonal_sequences:
            raise ValueError("Must extract seasonal parameter sequences first")
        
        seasonal_reversion_rates = {}
        params = ['PWW', 'PWD', 'alpha', 'beta']
        
        for season_name, season_data in self.seasonal_sequences.items():
            season_reversion_rates = {}
            
            for param in params:
                if param not in season_data.columns:
                    logger.warning(f"Parameter {param} not found in {season_name} sequence")
                    continue
                
                values = season_data[param].values
                
                if len(values) < 3:
                    logger.warning(f"Insufficient {season_name} data for {param} reversion rate calculation")
                    continue
                
                # Calculate differences and lagged values
                differences = np.diff(values)  # Δx_t = x_t - x_{t-1}
                lagged_values = values[:-1]    # x_{t-1}
                mean_value = np.mean(values)   # μ
                
                # Mean-adjusted lagged values: (μ - x_{t-1})
                mean_adjusted = mean_value - lagged_values
                
                # Regression: Δx_t = r * (μ - x_{t-1}) + ε
                if np.var(mean_adjusted) > 1e-10:  # Avoid division by zero
                    slope, intercept, r_value, p_value, std_err = stats.linregress(mean_adjusted, differences)
                    reversion_rate = slope
                else:
                    logger.warning(f"No variation in {season_name} {param} values - setting reversion rate to 0")
                    reversion_rate = 0.0
                
                # Ensure reversion rate is positive
                reversion_rate = abs(reversion_rate)
                season_reversion_rates[param] = reversion_rate
                
                logger.info(f"{season_name} reversion rate for {param}: {reversion_rate:.6f}")
            
            seasonal_reversion_rates[season_name] = season_reversion_rates
        
        return seasonal_reversion_rates
    
    def calculate_seasonal_long_term_means(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate long-term historical means for each parameter by season.
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            Nested dictionary: {season: {parameter: mean}}
        """
        if not self.seasonal_sequences:
            raise ValueError("Must extract seasonal parameter sequences first")
        
        seasonal_means = {}
        params = ['PWW', 'PWD', 'alpha', 'beta']
        
        for season_name, season_data in self.seasonal_sequences.items():
            season_means = {}
            
            for param in params:
                if param in season_data.columns:
                    mean_value = season_data[param].mean()
                    season_means[param] = mean_value
                    
                    logger.info(f"{season_name} long-term mean for {param}: {mean_value:.6f}")
            
            seasonal_means[season_name] = season_means
        
        return seasonal_means
    
    def analyze_all_parameters(self) -> Dict:
        """
        Perform complete random walk parameter analysis.
        
        If seasonal_analysis is True, performs both annual and seasonal analysis.
        
        Returns
        -------
        Dict
            Complete analysis results including volatilities, reversion rates,
            correlations, and long-term means
        """
        results = {}
        
        # Always do annual analysis
        self.extract_parameter_sequence()
        
        volatilities = self.calculate_volatilities()
        reversion_rates = self.calculate_reversion_rates()
        correlations = self.calculate_correlations()
        long_term_means = self.calculate_long_term_means()
        
        results['annual'] = {
            'volatilities': volatilities,
            'reversion_rates': reversion_rates,
            'correlations': correlations,
            'long_term_means': long_term_means,
            'parameter_sequence': self.parameter_sequence,
        }
        
        # Add seasonal analysis if requested
        if self.seasonal_analysis:
            logger.info("Performing seasonal analysis...")
            seasonal_results = self.analyze_seasonal_parameters()
            results['seasonal'] = seasonal_results
        
        results['metadata'] = {
            'window_size_years': self.window_size,
            'seasonal_analysis': self.seasonal_analysis,
            'n_windows': len(self.parameter_sequence),
            'analysis_date': datetime.now().isoformat(),
            'analysis_type': 'seasonal_and_annual' if self.seasonal_analysis else 'annual_only'
        }
        
        # Store results in instance variables for compatibility
        self.volatilities = volatilities
        self.reversion_rates = reversion_rates
        self.correlations = correlations
        self.long_term_means = long_term_means
        
        logger.info("Random walk parameter analysis complete")
        
        return results
    
    def analyze_seasonal_parameters(self) -> Dict:
        """
        Perform seasonal random walk parameter analysis.
        
        Returns
        -------
        Dict
            Complete seasonal analysis results
        """
        # Extract seasonal parameter sequences
        self.extract_seasonal_parameter_sequences()
        
        # Calculate seasonal metrics
        seasonal_volatilities = self.calculate_seasonal_volatilities()
        seasonal_reversion_rates = self.calculate_seasonal_reversion_rates()
        seasonal_means = self.calculate_seasonal_long_term_means()
        
        results = {
            'seasonal_volatilities': seasonal_volatilities,
            'seasonal_reversion_rates': seasonal_reversion_rates,
            'seasonal_long_term_means': seasonal_means,
            'seasonal_sequences': self.seasonal_sequences,
            'seasons_defined': self.seasons
        }
        
        logger.info("Seasonal random walk parameter analysis complete")
        
        return results
    
    def export_results(self, filepath: str, format: str = 'json'):
        """
        Export random walk analysis results to file.
        
        Parameters
        ----------
        filepath : str
            Output file path
        format : str
            Output format ('json' or 'csv')
        """
        if not self.volatilities or not self.reversion_rates:
            raise ValueError("Must run analysis first")
        
        if format.lower() == 'json':
            results = {
                'volatilities': self.volatilities,
                'reversion_rates': self.reversion_rates,
                'correlations': self.correlations,
                'long_term_means': self.long_term_means,
                'metadata': {
                    'window_size_years': self.window_size,
                    'n_windows': len(self.parameter_sequence) if self.parameter_sequence is not None else 0,
                    'analysis_date': datetime.now().isoformat(),
                    'method': 'random_walk_parameter_analysis'
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
                
        elif format.lower() == 'csv':
            # Export parameter sequence and summary stats
            if self.parameter_sequence is not None:
                # Save parameter sequence
                sequence_file = filepath.replace('.csv', '_sequence.csv')
                self.parameter_sequence.to_csv(sequence_file, index=False)
                
                # Save summary statistics
                summary_data = []
                for param in ['PWW', 'PWD', 'alpha', 'beta']:
                    if param in self.volatilities and param in self.reversion_rates:
                        summary_data.append({
                            'parameter': param,
                            'volatility': self.volatilities[param],
                            'reversion_rate': self.reversion_rates[param],
                            'long_term_mean': self.long_term_means.get(param, np.nan)
                        })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_csv(filepath, index=False)
        
        logger.info(f"Random walk analysis results exported to {filepath}")
    
    def plot_parameter_evolution(self, save_path: Optional[str] = None):
        """
        Plot parameter evolution over time with volatility bands.
        
        Parameters
        ----------
        save_path : str, optional
            Path to save the plot
        """
        if self.parameter_sequence is None:
            raise ValueError("Must extract parameter sequence first")
        
        params = ['PWW', 'PWD', 'alpha', 'beta']
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Random Walk Parameter Analysis\nParameter Evolution with Volatility', fontsize=16)
        
        axes = axes.flatten()
        
        for i, param in enumerate(params):
            if param not in self.parameter_sequence.columns:
                continue
            
            ax = axes[i]
            years = self.parameter_sequence['year']
            values = self.parameter_sequence[param]
            
            # Plot parameter evolution
            ax.plot(years, values, 'b-', alpha=0.7, marker='o', markersize=4, 
                   label='Parameter Values')
            
            # Plot long-term mean
            if param in self.long_term_means:
                mean_val = self.long_term_means[param]
                ax.axhline(mean_val, color='red', linestyle='--', alpha=0.8,
                          label=f'Long-term Mean = {mean_val:.4f}')
                
                # Plot volatility bands if available
                if param in self.volatilities:
                    volatility = self.volatilities[param]
                    ax.fill_between(years, mean_val - volatility, mean_val + volatility,
                                   alpha=0.2, color='red',
                                   label=f'±1σ (σ = {volatility:.4f})')
            
            # Add reversion rate to title if available
            title = f'{param} Evolution'
            if param in self.reversion_rates:
                r_val = self.reversion_rates[param]
                title += f'\nReversion Rate: {r_val:.4f}'
            
            ax.set_title(title)
            ax.set_xlabel('Year')
            ax.set_ylabel(param)
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Parameter evolution plot saved to {save_path}")
        
        plt.show()
    
    def plot_correlation_matrix(self, save_path: Optional[str] = None):
        """
        Plot correlation matrix for all parameters.
        
        Parameters
        ----------
        save_path : str, optional
            Path to save the plot
        """
        if self.parameter_sequence is None:
            raise ValueError("Must extract parameter sequence first")
        
        # Calculate full correlation matrix
        params = ['PWW', 'PWD', 'alpha', 'beta']
        available_params = [p for p in params if p in self.parameter_sequence.columns]
        
        if len(available_params) < 2:
            logger.warning("Insufficient parameters for correlation matrix")
            return
        
        corr_matrix = self.parameter_sequence[available_params].corr()
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(corr_matrix.values, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
        
        # Add colorbar
        cbar = plt.colorbar(im)
        cbar.set_label('Correlation Coefficient')
        
        # Set ticks and labels
        ax.set_xticks(range(len(available_params)))
        ax.set_yticks(range(len(available_params)))
        ax.set_xticklabels(available_params)
        ax.set_yticklabels(available_params)
        
        # Add correlation values to cells
        for i in range(len(available_params)):
            for j in range(len(available_params)):
                text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.3f}',
                               ha='center', va='center', color='black')
        
        ax.set_title('Parameter Correlation Matrix')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Correlation matrix plot saved to {save_path}")
        
        plt.show()
    
    def plot_seasonal_parameter_evolution(self, save_path: Optional[str] = None):
        """
        Plot seasonal parameter evolution to identify seasonal trends.
        
        Parameters
        ----------
        save_path : str, optional
            Path to save the plot
        """
        if not self.seasonal_sequences:
            raise ValueError("Must extract seasonal parameter sequences first")
        
        params = ['PWW', 'PWD', 'alpha', 'beta']
        seasons = list(self.seasonal_sequences.keys())
        
        fig, axes = plt.subplots(2, 2, figsize=(18, 14))
        fig.suptitle('Seasonal Random Walk Parameter Analysis\nParameter Evolution by Season', fontsize=16)
        
        axes = axes.flatten()
        colors = {'winter': 'blue', 'spring': 'green', 'summer': 'red', 'fall': 'orange'}
        
        for i, param in enumerate(params):
            ax = axes[i]
            
            for season_name in seasons:
                season_data = self.seasonal_sequences[season_name]
                
                if param not in season_data.columns or len(season_data) == 0:
                    continue
                
                years = season_data['year']
                values = season_data[param]
                
                # Plot seasonal parameter evolution
                color = colors.get(season_name, 'black')
                ax.plot(years, values, 'o-', alpha=0.7, color=color, 
                       label=f'{season_name.capitalize()}', markersize=4, linewidth=2)
                
                # Add trend line
                if len(values) > 2:
                    z = np.polyfit(years, values, 1)
                    p = np.poly1d(z)
                    ax.plot(years, p(years), '--', alpha=0.6, color=color, linewidth=1)
                    
                    # Calculate trend slope per decade
                    trend_per_decade = z[0] * 10
                    logger.info(f"{season_name} {param} trend: {trend_per_decade:+.4f} per decade")
            
            ax.set_title(f'{param} Evolution by Season')
            ax.set_xlabel('Year')
            ax.set_ylabel(param)
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Seasonal parameter evolution plot saved to {save_path}")
        
        plt.show()
    
    def export_seasonal_results(self, filepath: str, format: str = 'json'):
        """
        Export seasonal random walk analysis results to file.
        
        Parameters
        ----------
        filepath : str
            Output file path
        format : str
            Output format ('json' or 'csv')
        """
        if not self.seasonal_sequences:
            raise ValueError("Must run seasonal analysis first")
        
        if format.lower() == 'json':
            # Calculate seasonal metrics if not already done
            seasonal_volatilities = self.calculate_seasonal_volatilities()
            seasonal_reversion_rates = self.calculate_seasonal_reversion_rates()
            seasonal_means = self.calculate_seasonal_long_term_means()
            
            results = {
                'seasonal_volatilities': seasonal_volatilities,
                'seasonal_reversion_rates': seasonal_reversion_rates,
                'seasonal_long_term_means': seasonal_means,
                'seasonal_sequences': {season: df.to_dict('records') for season, df in self.seasonal_sequences.items()},
                'metadata': {
                    'window_size_years': self.window_size,
                    'seasons': self.seasons,
                    'analysis_date': datetime.now().isoformat(),
                    'method': 'seasonal_random_walk_parameter_analysis'
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
                
        elif format.lower() == 'csv':
            # Export seasonal summary
            seasonal_volatilities = self.calculate_seasonal_volatilities()
            seasonal_reversion_rates = self.calculate_seasonal_reversion_rates()
            seasonal_means = self.calculate_seasonal_long_term_means()
            
            summary_data = []
            for season in self.seasons.keys():
                for param in ['PWW', 'PWD', 'alpha', 'beta']:
                    if (season in seasonal_volatilities and param in seasonal_volatilities[season] and
                        season in seasonal_reversion_rates and param in seasonal_reversion_rates[season]):
                        
                        summary_data.append({
                            'season': season,
                            'parameter': param,
                            'volatility': seasonal_volatilities[season][param],
                            'reversion_rate': seasonal_reversion_rates[season][param],
                            'long_term_mean': seasonal_means[season].get(param, np.nan),
                            'n_windows': len(self.seasonal_sequences[season]) if season in self.seasonal_sequences else 0
                        })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_csv(filepath, index=False)
            
            # Also save individual seasonal sequences
            for season, season_data in self.seasonal_sequences.items():
                season_file = filepath.replace('.csv', f'_{season}_sequence.csv')
                season_data.to_csv(season_file, index=False)
        
        logger.info(f"Seasonal random walk analysis results exported to {filepath}")
    
def analyze_random_walk_parameters(time_series: TimeSeries, window_size: int = 2, 
                                 seasonal_analysis: bool = False) -> RandomWalkParameterAnalyzer:
    """
    Convenience function to perform complete random walk parameter analysis.
    
    Parameters
    ----------
    time_series : TimeSeries
        Time series object containing precipitation data
    window_size : int
        Size of sliding window in years (default=2 as per paper)
    seasonal_analysis : bool
        If True, perform both annual and seasonal analysis (default=False)
        
    Returns
    -------
    RandomWalkParameterAnalyzer
        Configured analyzer with complete analysis
    """
    analyzer = RandomWalkParameterAnalyzer(time_series, window_size, seasonal_analysis)
    analyzer.analyze_all_parameters()
    return analyzer


if __name__ == "__main__":
    print("Random Walk Parameter Analysis Module")
    print("Use: analyzer = analyze_random_walk_parameters(your_time_series)")
    print("For seasonal analysis: analyzer = analyze_random_walk_parameters(your_time_series, seasonal_analysis=True)")
    
    # Quick test if test data is available
    try:
        import os
        
        test_file = os.path.join("tests", "GrandJunction", "USW00023066_data.csv")
        if os.path.exists(test_file):
            print(f"\nTesting with {test_file}...")
            
            # Load and prepare data
            ts = TimeSeries()
            ts.load_and_preprocess(test_file)
            
            # Test seasonal analysis
            print("\nRunning seasonal random walk parameter analysis...")
            analyzer = analyze_random_walk_parameters(ts, seasonal_analysis=True)
            
            print(f"Analysis complete!")
            
            # Print annual results
            print(f"\nANNUAL ANALYSIS:")
            print(f"Extracted parameters for {len(analyzer.parameter_sequence)} windows")
            for param in ['PWW', 'PWD', 'alpha', 'beta']:
                if param in analyzer.volatilities:
                    print(f"  {param}: σ={analyzer.volatilities[param]:.6f}, "
                          f"r={analyzer.reversion_rates[param]:.6f}")
            
            # Print seasonal results if available
            if analyzer.seasonal_sequences:
                print(f"\nSEASONAL ANALYSIS:")
                seasonal_volatilities = analyzer.calculate_seasonal_volatilities()
                seasonal_reversion_rates = analyzer.calculate_seasonal_reversion_rates()
                
                for season in ['winter', 'spring', 'summer', 'fall']:
                    if season in seasonal_volatilities:
                        print(f"\n{season.upper()}:")
                        n_windows = len(analyzer.seasonal_sequences[season])
                        print(f"  Windows: {n_windows}")
                        for param in ['PWW', 'PWD']:  # Focus on PWW and PWD
                            if param in seasonal_volatilities[season]:
                                vol = seasonal_volatilities[season][param]
                                rev = seasonal_reversion_rates[season][param]
                                print(f"  {param}: σ={vol:.6f}, r={rev:.6f}")
        else:
            print("Test data not found - module loaded successfully")
            
    except ImportError as e:
        print(f"Dependencies not available for testing: {e}")