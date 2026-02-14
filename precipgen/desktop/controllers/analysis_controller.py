"""
Analysis controller for statistical operations and parameter calculations.

This module coordinates statistical analysis operations including basic descriptive
statistics, Markov chain parameter calculation, and seasonal trend analysis.
Integrates with precipgen.core and precipgen.data modules for calculations.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date
import pandas as pd
import numpy as np
from scipy import stats

from precipgen.desktop.models.app_state import AppState
from precipgen.core import calculate_params, LongTermAnalyzer
from precipgen.core.precip_stats import PrecipValidator
from precipgen.core.random_walk_params import analyze_random_walk_parameters
from precipgen.core.time_series import TimeSeries
from precipgen.data.gap_analyzer import analyze_gaps
from precipgen.desktop.utils.csv_writer import write_csv_file


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class BasicAnalysisResults:
    """Results from basic descriptive statistics analysis."""
    station_file: str
    date_range: Tuple[date, date]
    years_on_record: int
    gap_analysis: Dict[str, Any]  # coverage_pct, missing_days, short_gaps, long_gaps
    annual_totals: pd.Series  # Index: year, Values: total precipitation
    mean_annual: float
    std_annual: float
    best_fit_distribution: str
    monthly_stats: pd.DataFrame  # Columns: month, mean, std
    peak_1day: float
    max_consecutive_dry: float
    max_consecutive_wet: float


@dataclass
class MarkovParameters:
    """Markov chain parameters for PrecipGen simulator."""
    station_file: str
    source_station: str
    date_range: Tuple[date, date]
    calculation_date: datetime
    monthly_params: pd.DataFrame  # Columns: month, Pww, Pwd, alpha, beta (12 rows)


@dataclass
class TrendAnalysisResults:
    """Seasonal trend analysis results."""
    station_file: str
    start_year: int
    end_year: int
    seasonal_trends: pd.DataFrame  # Columns: parameter, season, reversion_rate, volatility, trend_slope
    trend_data: Dict[str, pd.DataFrame]  # Keys: 'Pww', 'Pwd', 'alpha', 'beta'
                                         # Values: DataFrame with [year, Winter, Spring, Summer, Fall]


@dataclass
class Result:
    """
    Generic result type for operations that can fail.
    
    Attributes:
        success: True if operation succeeded, False otherwise
        value: Result value if successful, None otherwise
        error: Error message if failed, None otherwise
    """
    success: bool
    value: Optional[Any] = None
    error: Optional[str] = None


class AnalysisController:
    """
    Coordinates statistical analysis and parameter calculations.
    
    Handles all analysis operations including basic descriptive statistics,
    Markov chain parameter calculation, and seasonal trend analysis.
    Integrates with existing precipgen.core and precipgen.data modules.
    
    Attributes:
        app_state: Runtime application state
    """
    
    def __init__(self, app_state: AppState):
        """
        Initialize AnalysisController.
        
        Args:
            app_state: AppState instance for runtime state management
        """
        self.app_state = app_state
    
    def calculate_basic_stats(self, station_file: str) -> Result:
        """
        Calculate descriptive statistics for precipitation time series.
        
        Computes comprehensive statistics including date range, gap analysis,
        annual precipitation statistics, monthly statistics, and extreme values.
        
        Args:
            station_file: Name of the CSV file in the working directory
            
        Returns:
            Result object containing:
            - success: True if calculation succeeded
            - value: BasicAnalysisResults object if successful
            - error: Error message if failed
        """
        try:
            logger.info(f"Calculating basic statistics for {station_file}")
            
            # Load data from working directory
            data = self._load_station_data(station_file)
            if data is None:
                return Result(
                    success=False,
                    error=f"Failed to load data from {station_file}"
                )
            
            # Validate data has required columns
            if 'DATE' not in data.columns or 'PRCP' not in data.columns:
                return Result(
                    success=False,
                    error="Data must have DATE and PRCP columns"
                )
            
            # Ensure DATE is datetime and set as index
            data['DATE'] = pd.to_datetime(data['DATE'])
            data_indexed = data.set_index('DATE').sort_index()
            
            # Get date range
            start_date = data_indexed.index.min().date()
            end_date = data_indexed.index.max().date()
            years_on_record = end_date.year - start_date.year + 1
            
            logger.info(f"Date range: {start_date} to {end_date} ({years_on_record} years)")
            
            # Perform gap analysis
            gap_results = analyze_gaps(data_indexed, 'PRCP', gap_threshold=7)
            if gap_results is None:
                gap_analysis = {
                    'coverage_pct': 0.0,
                    'missing_days': 0,
                    'short_gaps': 0,
                    'long_gaps': 0
                }
            else:
                coverage_pct = ((gap_results['total_days'] - gap_results['total_missing_days']) / 
                               gap_results['total_days'] * 100)
                gap_analysis = {
                    'coverage_pct': round(coverage_pct, 1),
                    'missing_days': gap_results['total_missing_days'],
                    'short_gaps': gap_results['short_gap_count'],
                    'long_gaps': gap_results['long_gap_count']
                }
            
            logger.info(f"Gap analysis: {gap_analysis['coverage_pct']}% coverage")
            
            # Calculate annual totals
            annual_totals = data_indexed['PRCP'].resample('YE').sum()
            annual_totals.index = annual_totals.index.year
            
            # Calculate annual statistics
            mean_annual = float(annual_totals.mean())
            std_annual = float(annual_totals.std())
            
            logger.info(f"Annual precipitation: mean={mean_annual:.1f}mm, std={std_annual:.1f}mm")
            
            # Determine best-fit distribution
            best_fit_dist = self._determine_best_fit_distribution(annual_totals)
            
            # Calculate monthly statistics
            monthly_stats = self._calculate_monthly_stats(data_indexed)
            
            # Calculate extreme values
            peak_1day = float(data_indexed['PRCP'].max())
            
            # Calculate consecutive dry/wet days using PrecipValidator
            validator = PrecipValidator(data.copy())
            max_consecutive_dry = float(validator.longest_run_of_dry_days())
            max_consecutive_wet = float(validator.longest_run_of_wet_days())
            
            logger.info(f"Extremes: peak_1day={peak_1day:.1f}mm, "
                       f"max_dry={max_consecutive_dry:.0f} days, "
                       f"max_wet={max_consecutive_wet:.0f} days")
            
            # Create results object
            results = BasicAnalysisResults(
                station_file=station_file,
                date_range=(start_date, end_date),
                years_on_record=years_on_record,
                gap_analysis=gap_analysis,
                annual_totals=annual_totals,
                mean_annual=mean_annual,
                std_annual=std_annual,
                best_fit_distribution=best_fit_dist,
                monthly_stats=monthly_stats,
                peak_1day=peak_1day,
                max_consecutive_dry=max_consecutive_dry,
                max_consecutive_wet=max_consecutive_wet
            )
            
            # Update app state
            self.app_state.set_basic_analysis_results(results)
            
            logger.info("Basic statistics calculated successfully")
            
            return Result(
                success=True,
                value=results,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error calculating basic statistics: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Basic Statistics Calculation Error\n\n"
                      f"Failed to calculate statistics for {station_file}.\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Suggestions:\n"
                      f"• Verify the file exists in the working directory\n"
                      f"• Check that the file has valid DATE and PRCP columns\n"
                      f"• Ensure the data has sufficient coverage"
            )
    
    def calculate_markov_parameters(self, station_file: str) -> Result:
        """
        Calculate Markov chain parameters for PrecipGen simulator.
        
        Computes monthly transition probabilities (Pww, Pwd) and gamma
        distribution parameters (alpha, beta) using precipgen.core module.
        
        Args:
            station_file: Name of the CSV file in the working directory
            
        Returns:
            Result object containing:
            - success: True if calculation succeeded
            - value: MarkovParameters object if successful
            - error: Error message if failed
        """
        try:
            logger.info(f"Calculating Markov parameters for {station_file}")
            
            # Load data from working directory
            data = self._load_station_data(station_file)
            if data is None:
                return Result(
                    success=False,
                    error=f"Failed to load data from {station_file}"
                )
            
            # Validate data
            if 'DATE' not in data.columns or 'PRCP' not in data.columns:
                return Result(
                    success=False,
                    error="Data must have DATE and PRCP columns"
                )
            
            # Prepare data for calculation
            data['DATE'] = pd.to_datetime(data['DATE'])
            data_indexed = data.set_index('DATE').sort_index()
            
            # Calculate parameters using precipgen.core
            params_df = calculate_params(data_indexed)
            
            if params_df is None or params_df.empty:
                return Result(
                    success=False,
                    error="Parameter calculation returned no results"
                )
            
            # Validate parameter ranges
            validation_result = self._validate_parameter_ranges(params_df)
            if not validation_result[0]:
                logger.warning(f"Parameter validation warning: {validation_result[1]}")
            
            # Format for PrecipGen simulator (12 rows, one per month)
            # calculate_params returns DataFrame with index as month (1-12)
            # and columns: PWW, PWD, ALPHA, BETA
            monthly_params = pd.DataFrame({
                'month': range(1, 13),
                'Pww': params_df['PWW'].values,
                'Pwd': params_df['PWD'].values,
                'alpha': params_df['ALPHA'].values,
                'beta': params_df['BETA'].values
            })
            
            # Get metadata
            start_date = data_indexed.index.min().date()
            end_date = data_indexed.index.max().date()
            station_id = Path(station_file).stem  # Extract station ID from filename
            
            logger.info(f"Markov parameters calculated for {station_id}")
            
            # Create results object
            results = MarkovParameters(
                station_file=station_file,
                source_station=station_id,
                date_range=(start_date, end_date),
                calculation_date=datetime.now(),
                monthly_params=monthly_params
            )
            
            # Update app state
            self.app_state.set_markov_parameters(results)
            
            logger.info("Markov parameters calculated successfully")
            
            return Result(
                success=True,
                value=results,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error calculating Markov parameters: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Markov Parameter Calculation Error\n\n"
                      f"Failed to calculate parameters for {station_file}.\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Suggestions:\n"
                      f"• Verify the file has sufficient data (at least 1 year)\n"
                      f"• Check that the data has adequate coverage\n"
                      f"• Ensure precipitation values are valid"
            )
    
    def calculate_seasonal_trends(
        self,
        station_file: str,
        start_year: int,
        end_year: int
    ) -> Result:
        """
        Calculate seasonal trends in Markov parameters.
        
        Analyzes how Markov parameters change over time by season, computing
        reversion rates, volatilities, and trend slopes for each parameter
        and season combination.
        
        Args:
            station_file: Name of the CSV file in the working directory
            start_year: Start year for analysis period
            end_year: End year for analysis period
            
        Returns:
            Result object containing:
            - success: True if calculation succeeded
            - value: TrendAnalysisResults object if successful
            - error: Error message if failed
        """
        try:
            logger.info(f"Calculating seasonal trends for {station_file} "
                       f"({start_year}-{end_year})")
            
            # Load data from working directory
            data = self._load_station_data(station_file)
            if data is None:
                return Result(
                    success=False,
                    error=f"Failed to load data from {station_file}"
                )
            
            # Validate data
            if 'DATE' not in data.columns or 'PRCP' not in data.columns:
                return Result(
                    success=False,
                    error="Data must have DATE and PRCP columns"
                )
            
            # Prepare data
            data['DATE'] = pd.to_datetime(data['DATE'])
            data_indexed = data.set_index('DATE').sort_index()
            
            # Filter to specified year range
            data_filtered = data_indexed[
                (data_indexed.index.year >= start_year) &
                (data_indexed.index.year <= end_year)
            ]
            
            if data_filtered.empty:
                return Result(
                    success=False,
                    error=f"No data available for year range {start_year}-{end_year}"
                )
            
            logger.info(f"Filtered data: {len(data_filtered)} days")
            
            # Calculate seasonal trends
            seasonal_trends, trend_data = self._calculate_seasonal_parameter_trends(
                data_filtered,
                start_year,
                end_year
            )
            
            # Create results object
            results = TrendAnalysisResults(
                station_file=station_file,
                start_year=start_year,
                end_year=end_year,
                seasonal_trends=seasonal_trends,
                trend_data=trend_data
            )
            
            # Update app state
            self.app_state.set_trend_analysis_results(results)
            
            logger.info("Seasonal trends calculated successfully")
            
            return Result(
                success=True,
                value=results,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error calculating seasonal trends: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Seasonal Trend Calculation Error\n\n"
                      f"Failed to calculate trends for {station_file}.\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Suggestions:\n"
                      f"• Verify the year range is within the data range\n"
                      f"• Ensure sufficient data exists for trend analysis\n"
                      f"• Check that start_year < end_year"
            )
    
    def export_basic_stats(
        self,
        results: BasicAnalysisResults,
        output_path: Path
    ) -> Result:
        """
        Save basic analysis results to CSV.
        
        Args:
            results: BasicAnalysisResults object to export
            output_path: Path where CSV should be saved
            
        Returns:
            Result object with success status and saved file path
        """
        try:
            logger.info(f"Exporting basic statistics to {output_path}")
            
            # Create output data as list of rows
            data_rows = []
            data_rows.append(["Station", results.station_file])
            data_rows.append(["Start Date", str(results.date_range[0])])
            data_rows.append(["End Date", str(results.date_range[1])])
            data_rows.append(["Years on Record", str(results.years_on_record)])
            data_rows.append(["Data Coverage (%)", f"{results.gap_analysis['coverage_pct']:.1f}"])
            data_rows.append(["Missing Days", str(results.gap_analysis['missing_days'])])
            data_rows.append(["Mean Annual Precipitation (mm)", f"{results.mean_annual:.1f}"])
            data_rows.append(["Std Dev Annual Precipitation (mm)", f"{results.std_annual:.1f}"])
            data_rows.append(["Best Fit Distribution", results.best_fit_distribution])
            data_rows.append(["Peak 1-Day Rainfall (mm)", f"{results.peak_1day:.1f}"])
            data_rows.append(["Max Consecutive Dry Days (avg)", f"{results.max_consecutive_dry:.1f}"])
            data_rows.append(["Max Consecutive Wet Days (avg)", f"{results.max_consecutive_wet:.1f}"])
            data_rows.append(["", ""])  # Empty row separator
            data_rows.append(["Monthly Statistics", ""])
            data_rows.append(["Month", "Mean (mm)", "Std Dev (mm)"])
            
            # Add monthly statistics
            for _, row in results.monthly_stats.iterrows():
                data_rows.append([str(row['month']), f"{row['mean']:.1f}", f"{row['std']:.1f}"])
            
            # Write using standardized CSV writer
            write_csv_file(output_path, data_rows, headers=["Metric", "Value"])
            
            logger.info(f"Basic statistics exported successfully to {output_path}")
            
            return Result(
                success=True,
                value=output_path,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error exporting basic statistics: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Export Error\n\n"
                      f"Failed to save results to {output_path}.\n\n"
                      f"Details: {str(e)}"
            )
    
    def export_markov_parameters(
        self,
        params: MarkovParameters,
        output_path: Path
    ) -> Result:
        """
        Save Markov parameters in PrecipGen simulator format.
        
        Args:
            params: MarkovParameters object to export
            output_path: Path where CSV should be saved
            
        Returns:
            Result object with success status and saved file path
        """
        try:
            logger.info(f"Exporting Markov parameters to {output_path}")
            
            # Save in PrecipGen simulator format using standardized CSV writer
            write_csv_file(output_path, params.monthly_params)
            
            logger.info(f"Markov parameters exported successfully to {output_path}")
            
            return Result(
                success=True,
                value=output_path,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error exporting Markov parameters: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Export Error\n\n"
                      f"Failed to save parameters to {output_path}.\n\n"
                      f"Details: {str(e)}"
            )
    
    def export_trend_analysis(
        self,
        trends: TrendAnalysisResults,
        output_path: Path
    ) -> Result:
        """
        Save seasonal trend analysis results to CSV.
        
        Args:
            trends: TrendAnalysisResults object to export
            output_path: Path where CSV should be saved
            
        Returns:
            Result object with success status and saved file path
        """
        try:
            logger.info(f"Exporting trend analysis to {output_path}")
            
            # Save seasonal trends DataFrame using standardized CSV writer
            write_csv_file(output_path, trends.seasonal_trends)
            
            logger.info(f"Trend analysis exported successfully to {output_path}")
            
            return Result(
                success=True,
                value=output_path,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error exporting trend analysis: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Export Error\n\n"
                      f"Failed to save trends to {output_path}.\n\n"
                      f"Details: {str(e)}"
            )
    
    # Private helper methods
    
    def _load_station_data(self, station_file: str) -> Optional[pd.DataFrame]:
        """
        Load station data from working directory.
        
        Handles GHCN format files with metadata rows by detecting the DATE column
        header and skipping metadata rows above it.
        
        Args:
            station_file: Name of the CSV file
            
        Returns:
            DataFrame with precipitation data, or None if load fails
        """
        try:
            if not self.app_state.has_project_folder():
                logger.error("No project folder set")
                return None
            
            file_path = self.app_state.project_folder / station_file
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            # Detect GHCN format by checking the first few lines for DATE column header
            with open(file_path, 'r', encoding='utf-8') as f:
                first_lines = [f.readline().strip() for _ in range(10)]
            
            # Look for DATE column header to determine skip rows
            skip_rows = 0
            for i, line in enumerate(first_lines):
                if 'DATE' in line.upper() and ('PRCP' in line.upper() or 'TMAX' in line.upper()):
                    skip_rows = i
                    break
            
            # Load the CSV with appropriate skip rows
            if skip_rows > 0:
                logger.info(f"Detected GHCN format, skipping {skip_rows} metadata lines")
                data = pd.read_csv(file_path, skiprows=skip_rows, header=0)
            else:
                # Check if first line looks like headers
                if 'DATE' in first_lines[0].upper() and 'PRCP' in first_lines[0].upper():
                    data = pd.read_csv(file_path, header=0)
                else:
                    # Fallback: assume GHCN format with 6 metadata lines
                    logger.warning("Could not detect header line, assuming GHCN format with 6 metadata lines")
                    data = pd.read_csv(file_path, skiprows=6, header=0)
            
            logger.info(f"Loaded {len(data)} rows from {station_file}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading station data: {e}", exc_info=True)
            return None
    
    def _determine_best_fit_distribution(self, annual_totals: pd.Series) -> str:
        """
        Determine best-fit distribution for annual precipitation.
        
        Tests Gamma and Log-Pearson Type III distributions using
        Kolmogorov-Smirnov test.
        
        Args:
            annual_totals: Series of annual precipitation totals
            
        Returns:
            Name of best-fit distribution
        """
        try:
            # Fit Gamma distribution
            gamma_params = stats.gamma.fit(annual_totals)
            gamma_kstest = stats.kstest(annual_totals, 'gamma', gamma_params)
            
            # Fit Log-Pearson Type III distribution
            log_data = np.log(annual_totals)
            pearson3_params = stats.pearson3.fit(log_data)
            pearson3_kstest = stats.kstest(log_data, 'pearson3', pearson3_params)
            
            # Select distribution with higher p-value (better fit)
            if gamma_kstest.pvalue > pearson3_kstest.pvalue:
                return f"Gamma (p={gamma_kstest.pvalue:.4f})"
            else:
                return f"Log-Pearson III (p={pearson3_kstest.pvalue:.4f})"
                
        except Exception as e:
            logger.warning(f"Error determining best-fit distribution: {e}")
            return "Unknown"
    
    def _calculate_monthly_stats(self, data_indexed: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate monthly mean and standard deviation.
        
        Args:
            data_indexed: DataFrame with DatetimeIndex and PRCP column
            
        Returns:
            DataFrame with columns: month, mean, std
        """
        # Group by month and calculate statistics
        monthly_groups = data_indexed.groupby(data_indexed.index.month)['PRCP']
        
        monthly_stats = pd.DataFrame({
            'month': range(1, 13),
            'mean': [monthly_groups.get_group(m).mean() if m in monthly_groups.groups else 0.0 
                    for m in range(1, 13)],
            'std': [monthly_groups.get_group(m).std() if m in monthly_groups.groups else 0.0 
                   for m in range(1, 13)]
        })
        
        return monthly_stats
    
    def _validate_parameter_ranges(
        self,
        params_df: pd.DataFrame
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that calculated parameters are within reasonable ranges.
        
        Args:
            params_df: DataFrame with calculated parameters
            
        Returns:
            Tuple of (is_valid, warning_message)
        """
        warnings = []
        
        # Check alpha values
        if (params_df['ALPHA'] <= 0).any():
            warnings.append("Some alpha values are <= 0")
        if (params_df['ALPHA'] > 5.0).any():
            warnings.append("Some alpha values exceed typical range (0.1-5.0)")
        
        # Check beta values
        if (params_df['BETA'] <= 0).any():
            warnings.append("Some beta values are <= 0")
        if (params_df['BETA'] > 5.0).any():
            warnings.append("Some beta values exceed typical range (0.1-5.0)")
        
        # Check probability values
        if (params_df['PWW'] < 0).any() or (params_df['PWW'] > 1).any():
            warnings.append("Some P(W|W) values are outside [0,1]")
        if (params_df['PWD'] < 0).any() or (params_df['PWD'] > 1).any():
            warnings.append("Some P(W|D) values are outside [0,1]")
        
        if warnings:
            return False, "; ".join(warnings)
        
        return True, None
    
    def _calculate_seasonal_parameter_trends(
        self,
        data: pd.DataFrame,
        start_year: int,
        end_year: int
    ) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Calculate seasonal trends for Markov parameters.
        
        Computes parameters for each year and season, then calculates
        trend slopes, reversion rates, and volatilities.
        
        Args:
            data: DataFrame with DatetimeIndex and PRCP column
            start_year: Start year for analysis
            end_year: End year for analysis
            
        Returns:
            Tuple of (seasonal_trends DataFrame, trend_data dict)
        """
        # Define seasons
        seasons = {
            'Winter': [12, 1, 2],
            'Spring': [3, 4, 5],
            'Summer': [6, 7, 8],
            'Fall': [9, 10, 11]
        }
        
        # Calculate parameters for each year and season
        years = range(start_year, end_year + 1)
        param_names = ['Pww', 'Pwd', 'alpha', 'beta']
        
        # Initialize storage for trend data
        trend_data = {param: pd.DataFrame(index=years, columns=seasons.keys()) 
                     for param in param_names}
        
        # Calculate parameters for each year and season
        for year in years:
            year_data = data[data.index.year == year]
            
            if len(year_data) < 30:  # Skip years with insufficient data
                continue
            
            for season_name, months in seasons.items():
                season_data = year_data[year_data.index.month.isin(months)]
                
                if len(season_data) < 10:  # Skip seasons with insufficient data
                    continue
                
                try:
                    # Calculate parameters for this season
                    params = calculate_params(season_data)
                    
                    if params is not None and not params.empty:
                        # Average across months in the season
                        trend_data['Pww'].loc[year, season_name] = params['PWW'].mean()
                        trend_data['Pwd'].loc[year, season_name] = params['PWD'].mean()
                        trend_data['alpha'].loc[year, season_name] = params['ALPHA'].mean()
                        trend_data['beta'].loc[year, season_name] = params['BETA'].mean()
                        
                except Exception as e:
                    logger.warning(f"Error calculating parameters for {year} {season_name}: {e}")
                    continue
        
        # Calculate trends for each parameter and season
        seasonal_trends_list = []
        
        for param_name in param_names:
            param_df = trend_data[param_name]
            
            for season_name in seasons.keys():
                season_values = param_df[season_name].dropna()
                
                if len(season_values) < 3:  # Need at least 3 points for trend
                    continue
                
                # Calculate trend slope using linear regression
                x = np.array(season_values.index)
                y = season_values.values.astype(float)
                
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                # Calculate volatility (standard deviation of residuals)
                predicted = slope * x + intercept
                residuals = y - predicted
                volatility = float(np.std(residuals))
                
                # Calculate reversion rate (simplified as inverse of autocorrelation lag-1)
                if len(season_values) > 1:
                    autocorr = season_values.autocorr(lag=1)
                    reversion_rate = float(1.0 - autocorr) if not np.isnan(autocorr) else 0.0
                else:
                    reversion_rate = 0.0
                
                seasonal_trends_list.append({
                    'parameter': param_name,
                    'season': season_name,
                    'reversion_rate': reversion_rate,
                    'volatility': volatility,
                    'trend_slope': float(slope)
                })
        
        seasonal_trends = pd.DataFrame(seasonal_trends_list)
        
        return seasonal_trends, trend_data
