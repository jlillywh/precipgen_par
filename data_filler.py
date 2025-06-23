#!/usr/bin/env python3
"""
Data Filling Module for PrecipGen PAR

This module implements professional-grade methods for filling missing precipitation data
following best practices used by hydrologists and meteorologists.

Methods implemented:
1. Linear interpolation for short gaps (1-2 days)
2. Climatological normal substitution for medium gaps (3-7 days)
3. Analogous year method for longer gaps (8+ days)
4. Statistical validation and quality control

Author: PrecipGen PAR Team
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
import warnings
from scipy import stats
from scipy.interpolate import interp1d
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrecipitationDataFiller:
    """
    Professional precipitation data filling using meteorological best practices.
    
    Implements multiple filling strategies based on gap length and data availability:
    - Linear interpolation: 1-2 day gaps
    - Climatological normal: 3-7 day gaps  
    - Analogous year method: 8+ day gaps
    - Statistical validation throughout
    """
    
    def __init__(self, 
                 min_similarity_threshold: float = 0.7,
                 max_fill_gap_days: int = 30,
                 seasonal_window_days: int = 15,
                 min_years_for_climatology: int = 10):
        """
        Initialize the data filler with configurable parameters.
        
        Args:
            min_similarity_threshold: Minimum correlation for analogous year selection
            max_fill_gap_days: Maximum gap size to attempt filling
            seasonal_window_days: Days around target date for climatological normal
            min_years_for_climatology: Minimum years needed for reliable climatology
        """
        self.min_similarity_threshold = min_similarity_threshold
        self.max_fill_gap_days = max_fill_gap_days
        self.seasonal_window_days = seasonal_window_days
        self.min_years_for_climatology = min_years_for_climatology
        
        # Track filling statistics
        self.fill_stats = {
            'linear_interpolation': 0,
            'climatological_normal': 0,
            'analogous_year': 0,
            'unfilled_gaps': 0,
            'total_days_filled': 0
        }
        
    def fill_missing_data(self, 
                         df: pd.DataFrame,
                         date_col: str = 'DATE',
                         precip_col: str = 'PRCP',
                         output_file: Optional[str] = None,
                         create_report: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        Main method to fill missing precipitation data.
        
        Args:
            df: DataFrame with precipitation data
            date_col: Name of date column
            precip_col: Name of precipitation column
            output_file: Optional output file path
            create_report: Whether to create detailed filling report
            
        Returns:
            Tuple of (filled_dataframe, filling_report)
        """
        logger.info("Starting precipitation data filling process")
        
        # Prepare data
        df_filled = df.copy()
        df_filled[date_col] = pd.to_datetime(df_filled[date_col])
        df_filled = df_filled.sort_values(date_col).reset_index(drop=True)
        
        # Identify missing data
        missing_mask = df_filled[precip_col].isna()
        original_missing_count = missing_mask.sum()
        
        if original_missing_count == 0:
            logger.info("No missing data found")
            return df_filled, {'status': 'no_missing_data'}
        
        logger.info(f"Found {original_missing_count} missing values")
        
        # Find gap sequences
        gaps = self._identify_gaps(df_filled, date_col, precip_col)
        logger.info(f"Identified {len(gaps)} gap sequences")
        
        # Fill gaps using appropriate methods
        for gap in gaps:
            self._fill_gap(df_filled, gap, date_col, precip_col)
        
        # Validate filled data
        validation_results = self._validate_filled_data(df, df_filled, precip_col)
        
        # Create filling report
        report = self._create_filling_report(
            original_missing_count, gaps, validation_results, df_filled, date_col, precip_col
        ) if create_report else {}
        
        # Save output file
        if output_file:
            df_filled.to_csv(output_file, index=False)
            logger.info(f"Filled data saved to {output_file}")
            
            if create_report:
                report_file = output_file.replace('.csv', '_filling_report.json')
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                logger.info(f"Filling report saved to {report_file}")
        
        return df_filled, report
    
    def _identify_gaps(self, df: pd.DataFrame, date_col: str, precip_col: str) -> List[Dict]:
        """Identify sequences of missing data."""
        gaps = []
        missing_mask = df[precip_col].isna()
        
        in_gap = False
        gap_start = None
        
        for idx, is_missing in enumerate(missing_mask):
            if is_missing and not in_gap:
                # Start of new gap
                in_gap = True
                gap_start = idx
            elif not is_missing and in_gap:
                # End of gap
                in_gap = False
                gaps.append({
                    'start_idx': gap_start,
                    'end_idx': idx - 1,
                    'length': idx - gap_start,
                    'start_date': df.iloc[gap_start][date_col],
                    'end_date': df.iloc[idx - 1][date_col]
                })
        
        # Handle gap extending to end of data
        if in_gap:
            gaps.append({
                'start_idx': gap_start,
                'end_idx': len(df) - 1,
                'length': len(df) - gap_start,
                'start_date': df.iloc[gap_start][date_col],
                'end_date': df.iloc[-1][date_col]
            })
        
        return gaps
    
    def _fill_gap(self, df: pd.DataFrame, gap: Dict, date_col: str, precip_col: str):
        """Fill a single gap using appropriate method based on gap length."""
        gap_length = gap['length']
        
        if gap_length > self.max_fill_gap_days:
            logger.warning(f"Gap of {gap_length} days exceeds maximum fill length ({self.max_fill_gap_days})")
            self.fill_stats['unfilled_gaps'] += 1
            return
        
        if gap_length <= 2:
            # Linear interpolation for short gaps
            success = self._linear_interpolation(df, gap, date_col, precip_col)
            if success:
                self.fill_stats['linear_interpolation'] += 1
                self.fill_stats['total_days_filled'] += gap_length
        elif gap_length <= 7:
            # Climatological normal for medium gaps
            success = self._climatological_fill(df, gap, date_col, precip_col)
            if success:
                self.fill_stats['climatological_normal'] += 1
                self.fill_stats['total_days_filled'] += gap_length
            else:
                # Fallback to analogous year
                success = self._analogous_year_fill(df, gap, date_col, precip_col)
                if success:
                    self.fill_stats['analogous_year'] += 1
                    self.fill_stats['total_days_filled'] += gap_length
        else:
            # Analogous year method for long gaps
            success = self._analogous_year_fill(df, gap, date_col, precip_col)
            if success:
                self.fill_stats['analogous_year'] += 1
                self.fill_stats['total_days_filled'] += gap_length
        
        if not success:
            self.fill_stats['unfilled_gaps'] += 1
            logger.warning(f"Could not fill gap from {gap['start_date']} to {gap['end_date']}")
    
    def _linear_interpolation(self, df: pd.DataFrame, gap: Dict, date_col: str, precip_col: str) -> bool:
        """Fill short gaps using linear interpolation."""
        start_idx = gap['start_idx']
        end_idx = gap['end_idx']
        
        # Need data points before and after gap
        if start_idx == 0 or end_idx == len(df) - 1:
            return False
        
        before_val = df.iloc[start_idx - 1][precip_col]
        after_val = df.iloc[end_idx + 1][precip_col]
        
        if pd.isna(before_val) or pd.isna(after_val):
            return False
        
        # Linear interpolation
        gap_length = end_idx - start_idx + 1
        interpolated_values = np.linspace(before_val, after_val, gap_length + 2)[1:-1]
        
        # Special handling for precipitation: ensure non-negative values
        interpolated_values = np.maximum(0, interpolated_values)
        
        # Apply interpolated values
        for i, val in enumerate(interpolated_values):
            df.iloc[start_idx + i, df.columns.get_loc(precip_col)] = val
        
        logger.info(f"Linear interpolation: filled {gap_length} days from {gap['start_date'].date()}")
        return True
    
    def _climatological_fill(self, df: pd.DataFrame, gap: Dict, date_col: str, precip_col: str) -> bool:
        """Fill gaps using climatological normal values."""
        start_date = gap['start_date']
        end_date = gap['end_date']
        
        # Calculate climatological normals for each day in the gap
        for current_date in pd.date_range(start_date, end_date):
            day_of_year = current_date.dayofyear
            
            # Find all years with data around this day of year
            climatology_data = []
            
            for year in df[date_col].dt.year.unique():
                if year == current_date.year:
                    continue  # Skip the year with missing data
                
                # Get data from seasonal window around this day of year
                year_start = datetime(year, 1, 1)
                target_date = year_start + timedelta(days=day_of_year - 1)
                
                start_window = target_date - timedelta(days=self.seasonal_window_days)
                end_window = target_date + timedelta(days=self.seasonal_window_days)
                
                window_data = df[
                    (df[date_col] >= start_window) & 
                    (df[date_col] <= end_window) &
                    df[precip_col].notna()
                ][precip_col]
                
                climatology_data.extend(window_data.tolist())
            
            if len(climatology_data) < self.min_years_for_climatology:
                return False
            
            # Use median for robustness (common practice in meteorology)
            climatological_value = np.median(climatology_data)
            
            # Find index for this date
            date_idx = df[df[date_col] == current_date].index[0]
            df.iloc[date_idx, df.columns.get_loc(precip_col)] = climatological_value
        
        logger.info(f"Climatological fill: filled gap from {start_date.date()} to {end_date.date()}")
        return True
    
    def _analogous_year_fill(self, df: pd.DataFrame, gap: Dict, date_col: str, precip_col: str) -> bool:
        """Fill gaps using analogous year method."""
        gap_year = gap['start_date'].year
        gap_start_doy = gap['start_date'].dayofyear
        gap_end_doy = gap['end_date'].dayofyear
        
        # Find candidate years with complete data for this period
        candidate_years = []
        available_years = df[date_col].dt.year.unique()
        
        for year in available_years:
            if year == gap_year:
                continue
            
            # Check if this year has complete data for the gap period
            year_start = datetime(year, 1, 1)
            gap_start_analog = year_start + timedelta(days=gap_start_doy - 1)
            gap_end_analog = year_start + timedelta(days=gap_end_doy - 1)
            
            year_gap_data = df[
                (df[date_col] >= gap_start_analog) & 
                (df[date_col] <= gap_end_analog)
            ][precip_col]
            
            if year_gap_data.notna().all() and len(year_gap_data) == gap['length']:
                candidate_years.append(year)
        
        if not candidate_years:
            return False
          # Calculate similarity scores for candidate years
        best_year = self._find_most_similar_year(
            df, gap_year, candidate_years, date_col, precip_col
        )
        
        if best_year is None:
            return False
        
        # Copy data from best analogous year
        year_start = datetime(best_year, 1, 1)
        
        for i in range(gap['length']):
            gap_date = gap['start_date'] + timedelta(days=i)
            analog_date = year_start + timedelta(days=gap_date.dayofyear - 1)
            
            # Find analog value with error checking
            analog_matches = df[df[date_col] == analog_date][precip_col]
            if analog_matches.empty:
                # If no exact match, try nearby dates
                for offset in [-1, 1, -2, 2]:
                    alt_date = analog_date + timedelta(days=offset)
                    alt_matches = df[df[date_col] == alt_date][precip_col]
                    if not alt_matches.empty:
                        analog_value = alt_matches.iloc[0]
                        break
                else:
                    # If still no match, use climatological average for this day of year
                    analog_value = 0.0  # Default to 0 if no data available
            else:
                analog_value = analog_matches.iloc[0]
            
            # Find gap index with error checking
            gap_matches = df[df[date_col] == gap_date].index
            if gap_matches.empty:
                continue  # Skip if no matching gap date found
            
            gap_idx = gap_matches[0]
            df.iloc[gap_idx, df.columns.get_loc(precip_col)] = analog_value
        
        logger.info(f"Analogous year fill: filled gap from {gap['start_date'].date()} using year {best_year}")
        return True
    
    def _find_most_similar_year(self, df: pd.DataFrame, gap_year: int, 
                               candidate_years: List[int], date_col: str, precip_col: str) -> Optional[int]:
        """Find the most meteorologically similar year for gap filling."""
        
        # Compare seasonal patterns and monthly totals
        best_year = None
        best_similarity = -1
        
        for candidate_year in candidate_years:
            similarity = self._calculate_year_similarity(
                df, gap_year, candidate_year, date_col, precip_col
            )
            
            if similarity > best_similarity and similarity >= self.min_similarity_threshold:
                best_similarity = similarity
                best_year = candidate_year
        
        return best_year
    
    def _calculate_year_similarity(self, df: pd.DataFrame, year1: int, year2: int,
                                  date_col: str, precip_col: str) -> float:
        """Calculate similarity between two years based on seasonal patterns."""
        
        # Get monthly totals for both years
        year1_data = df[df[date_col].dt.year == year1].copy()
        year2_data = df[df[date_col].dt.year == year2].copy()
        
        if len(year1_data) == 0 or len(year2_data) == 0:
            return 0
        
        # Calculate monthly totals
        year1_monthly = year1_data.groupby(year1_data[date_col].dt.month)[precip_col].sum()
        year2_monthly = year2_data.groupby(year2_data[date_col].dt.month)[precip_col].sum()
        
        # Ensure both years have data for the same months
        common_months = set(year1_monthly.index) & set(year2_monthly.index)
        if len(common_months) < 6:  # Need at least 6 months for comparison
            return 0
        
        monthly1 = [year1_monthly[month] for month in sorted(common_months)]
        monthly2 = [year2_monthly[month] for month in sorted(common_months)]
        
        # Calculate correlation
        if len(monthly1) < 2:
            return 0
        
        correlation, p_value = stats.pearsonr(monthly1, monthly2)
        
        # Return correlation if statistically significant, otherwise 0
        return correlation if p_value < 0.05 else 0
    
    def _validate_filled_data(self, original_df: pd.DataFrame, filled_df: pd.DataFrame, 
                             precip_col: str) -> Dict:
        """Validate the quality of filled data."""
        
        # Basic statistics comparison
        orig_stats = original_df[precip_col].describe()
        filled_stats = filled_df[precip_col].describe()
        
        # Check for preservation of statistical properties
        validation = {
            'mean_change': abs(filled_stats['mean'] - orig_stats['mean']) / orig_stats['mean'],
            'std_change': abs(filled_stats['std'] - orig_stats['std']) / orig_stats['std'],
            'filled_data_negative': (filled_df[precip_col] < 0).sum(),
            'filled_data_extreme': (filled_df[precip_col] > orig_stats['mean'] + 4 * orig_stats['std']).sum()
        }
        
        # Quality flags
        validation['quality_good'] = (
            validation['mean_change'] < 0.1 and 
            validation['std_change'] < 0.2 and
            validation['filled_data_negative'] == 0
        )
        
        return validation
    
    def _create_filling_report(self, original_missing: int, gaps: List[Dict], 
                              validation: Dict, df: pd.DataFrame, date_col: str, precip_col: str) -> Dict:
        """Create comprehensive filling report."""
        
        final_missing = df[precip_col].isna().sum()
        
        report = {
            'summary': {
                'original_missing_values': original_missing,
                'final_missing_values': final_missing,
                'values_filled': original_missing - final_missing,
                'fill_success_rate': (original_missing - final_missing) / original_missing * 100,
                'total_gaps_identified': len(gaps),
                'gaps_filled': len(gaps) - self.fill_stats['unfilled_gaps']
            },
            'methods_used': self.fill_stats.copy(),
            'gap_details': [
                {
                    'start_date': gap['start_date'].strftime('%Y-%m-%d'),
                    'end_date': gap['end_date'].strftime('%Y-%m-%d'),
                    'length_days': gap['length']
                }
                for gap in gaps
            ],
            'validation_results': validation,
            'data_quality': {
                'mean_precipitation': float(df[precip_col].mean()),
                'std_precipitation': float(df[precip_col].std()),
                'min_precipitation': float(df[precip_col].min()),
                'max_precipitation': float(df[precip_col].max()),
                'zero_precipitation_days': int((df[precip_col] == 0).sum())
            },
            'recommendations': self._generate_recommendations(validation, gaps)
        }
        
        return report
    
    def _generate_recommendations(self, validation: Dict, gaps: List[Dict]) -> List[str]:
        """Generate recommendations based on filling results."""
        recommendations = []
        
        if not validation['quality_good']:
            recommendations.append("Review filled data quality - statistical properties may have changed significantly")
        
        if validation['filled_data_negative'] > 0:
            recommendations.append("Some filled values are negative - review interpolation method")
        
        if validation['filled_data_extreme'] > 0:
            recommendations.append("Some filled values appear extreme - consider additional quality control")
        
        long_gaps = [gap for gap in gaps if gap['length'] > 7]
        if long_gaps:
            recommendations.append(f"Found {len(long_gaps)} long gaps (>7 days) - consider finding additional nearby stations")
        
        if self.fill_stats['unfilled_gaps'] > 0:
            recommendations.append("Some gaps could not be filled - may need manual review or additional data sources")
        
        if not recommendations:
            recommendations.append("Data filling completed successfully with good quality metrics")
        
        return recommendations


def fill_precipitation_data(input_file: str, 
                           output_file: str,
                           date_col: str = 'DATE',
                           precip_col: str = 'PRCP',
                           **kwargs) -> Dict:
    """
    Convenience function to fill precipitation data from CSV file.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        date_col: Name of date column
        precip_col: Name of precipitation column
        **kwargs: Additional parameters for PrecipitationDataFiller
        
    Returns:
        Dictionary with filling report
    """
    
    try:
        # Read data with robust CSV parsing
        df = None
        
        try:
            # Method 1: Try standard CSV reading
            df = pd.read_csv(input_file)
            logger.info(f"✅ Successfully read CSV with standard method")
        except Exception as e1:
            logger.info(f"Standard CSV reading failed: {e1}")
            
            try:
                # Method 2: Try reading as GHCN format (skip metadata headers)
                # GHCN files have 6 lines of metadata, then empty line, then data
                df = pd.read_csv(input_file, skiprows=7)
                logger.info(f"✅ Successfully read CSV skipping GHCN metadata headers")
            except Exception as e2:
                logger.info(f"GHCN format reading failed: {e2}")
                
                try:
                    # Method 3: Try detecting delimiter and headers automatically
                    with open(input_file, 'r') as f:
                        lines = f.readlines()
                    
                    # Find the actual data start by looking for DATE column
                    data_start_row = 0
                    for i, line in enumerate(lines):
                        if 'DATE' in line and ('PRCP' in line or 'Precipitation' in line):
                            data_start_row = i
                            break
                    
                    if data_start_row > 0:
                        df = pd.read_csv(input_file, skiprows=data_start_row)
                        logger.info(f"✅ Successfully read CSV starting from row {data_start_row}")
                    else:
                        # Try without headers
                        df = pd.read_csv(input_file, header=None)
                        logger.info(f"✅ Successfully read CSV without headers")
                        
                except Exception as e3:
                    raise Exception(f"Could not read CSV file. Tried multiple methods:\n"
                                  f"1. Standard reading: {e1}\n"
                                  f"2. GHCN format: {e2}\n"
                                  f"3. Auto-detection: {e3}")
        
        if df is None or df.empty:
            raise Exception("Failed to read the CSV file or file is empty")
        
        logger.info(f"📊 Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
        logger.info(f"📋 Columns: {list(df.columns)}")
        
        # Check if we have the required columns
        available_cols = df.columns.tolist()
        
        # Try to find date column if default doesn't exist
        if date_col not in available_cols:
            date_candidates = ['DATE', 'Date', 'date', 'TIME', 'DATETIME', 'DateTime']
            for candidate in date_candidates:
                if candidate in available_cols:
                    date_col = candidate
                    logger.info(f"🔍 Using '{candidate}' as date column")
                    break
            else:
                raise Exception(f"Date column '{date_col}' not found. Available columns: {available_cols}")
        
        # Try to find precipitation column if default doesn't exist
        if precip_col not in available_cols:
            precip_candidates = ['PRCP', 'PRECIPITATION', 'Precipitation', 'precipitation', 'RAIN', 'Rain']
            for candidate in precip_candidates:
                if candidate in available_cols:
                    precip_col = candidate
                    logger.info(f"🔍 Using '{candidate}' as precipitation column")
                    break
            else:
                raise Exception(f"Precipitation column '{precip_col}' not found. Available columns: {available_cols}")
        
        # Initialize filler
        filler = PrecipitationDataFiller(**kwargs)
        
        # Fill data
        filled_df, report = filler.fill_missing_data(
            df, date_col=date_col, precip_col=precip_col, output_file=output_file
        )
        
        return report
        
    except Exception as e:
        # Enhanced error reporting
        error_msg = f"Error in fill_precipitation_data: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
