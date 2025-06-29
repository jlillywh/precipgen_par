#!/usr/bin/env python3
"""
Data Filling Module for PrecipGen PAR

This module implements a simplified, realistic approach for filling missing precipitation data
using smart interpolation that respects precipitation characteristics.

Method implemented:
- Smart precipitation interpolation that considers gap length
- Single day gaps: Simple averaging
- Short gaps (2-3 days): Reduced linear interpolation  
- Longer gaps (4+ days): Mostly zeros with occasional wet days
- Reflects the reality that most days have no precipitation

IMPORTANT LIMITATIONS FOR STATISTICAL MODELING:
This deterministic approach is designed for conservative gap filling and may not be suitable
for downstream statistical analysis or stochastic modeling without consideration of:

1. BIAS IN STATISTICAL PARAMETERS: The conservative interpolation approach may bias
   key precipitation statistics used by PrecipGen:
   - Gamma distribution shape/scale parameters may be underestimated
   - Wet day frequencies may be artificially reduced for long gaps
   - Precipitation depth distributions may be skewed toward lower values

2. RECOMMENDED USAGE:
   - Phase I: Use for basic data completion and conservative analysis
   - Phase II: Consider stochastic gap filling using PrecipGen itself for data 
     that will be used to train/validate PrecipGen models
   - For statistical analysis: Flag filled periods and consider uncertainty

3. FUTURE ENHANCEMENT:
   - Implement stochastic gap filling that preserves statistical properties
   - Use PrecipGen's own algorithms for filling gaps in training data
   - Add uncertainty quantification for filled values

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
    Smart precipitation data filling using meteorologically-aware interpolation.
    
    Uses different strategies based on gap length to create realistic precipitation patterns:
    - Single day: Simple averaging between neighbors
    - Short gaps (2-3 days): Reduced linear interpolation (biased toward zero)
    - Longer gaps (4+ days): Mostly zero with occasional wet days
    
    This approach avoids the unrealistic "constant drizzle" problem of pure linear
    interpolation while remaining simple and reliable.
    
    ⚠️  IMPORTANT WARNING FOR PRECIPGEN USERS:
    This deterministic gap-filling method will bias precipitation statistics used
    by PrecipGen for stochastic modeling, including:
    - Gamma distribution parameters (alpha, beta) for wet day precipitation depths
    - Wet day frequency and transition probabilities
    - Extreme precipitation statistics
    
    For PrecipGen model training, consider using stochastic gap filling (Phase II)
    to preserve statistical properties needed for accurate simulation.
    """
    
    def __init__(self, 
                 max_fill_gap_days: int = 365):
        """
        Initialize the data filler with configurable parameters.
        
        Args:
            max_fill_gap_days: Maximum gap size to attempt filling (default: 365 days)
        """
        self.max_fill_gap_days = max_fill_gap_days
        
        # Track filling statistics
        self.fill_stats = {
            'linear_interpolation': 0,
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
    
    def _analyze_yearly_gaps(self, df: pd.DataFrame, date_col: str, precip_col: str, gaps: List[Dict]) -> Dict:
        """
        Analyze missing data patterns by year, focusing on years with significant gaps.
        
        Returns:
            Dictionary with yearly analysis including:
            - years_with_significant_gaps: Years with >90 missing days
            - summary_statistics: Overall statistics about yearly gaps
        """
        # Convert date column to datetime if it's not already
        df_copy = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_copy[date_col]):
            df_copy[date_col] = pd.to_datetime(df_copy[date_col])
        
        # Add year column
        df_copy['year'] = df_copy[date_col].dt.year
        
        # Calculate missing days per year
        missing_by_year = df_copy.groupby('year')[precip_col].apply(lambda x: x.isna().sum()).to_dict()
        
        # Calculate maximum consecutive missing days per year
        max_consecutive_by_year = {}
        
        for year in missing_by_year.keys():
            year_data = df_copy[df_copy['year'] == year]
            if len(year_data) == 0:
                max_consecutive_by_year[year] = 0
                continue
                
            # Find maximum consecutive missing days in this year
            missing_mask = year_data[precip_col].isna()
            max_consecutive = 0
            current_consecutive = 0
            
            for is_missing in missing_mask:
                if is_missing:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
            
            max_consecutive_by_year[year] = max_consecutive
        
        # Filter to years with >90 missing days
        significant_years = {
            year: {
                'total_missing_days': missing_days,
                'max_consecutive_missing': max_consecutive_by_year.get(year, 0),
                'total_days_in_year': len(df_copy[df_copy['year'] == year]),
                'percent_missing': round(missing_days / len(df_copy[df_copy['year'] == year]) * 100, 1)
            }
            for year, missing_days in missing_by_year.items()
            if missing_days > 90
        }
        
        # Calculate summary statistics
        all_missing_counts = list(missing_by_year.values())
        all_consecutive_counts = list(max_consecutive_by_year.values())
        
        summary_stats = {
            'total_years_analyzed': len(missing_by_year),
            'years_with_significant_gaps': len(significant_years),
            'avg_missing_days_per_year': round(sum(all_missing_counts) / len(all_missing_counts), 1) if all_missing_counts else 0,
            'max_missing_days_any_year': max(all_missing_counts) if all_missing_counts else 0,
            'max_consecutive_missing_any_year': max(all_consecutive_counts) if all_consecutive_counts else 0,
            'years_with_no_gaps': sum(1 for count in all_missing_counts if count == 0)
        }
        
        return {
            'summary_statistics': summary_stats,
            'years_with_significant_gaps': dict(sorted(significant_years.items())),
            'notes': [
                "Only years with >90 missing days are listed as 'significant'",
                "Years with extensive gaps may not be suitable for statistical modeling",
                "Consider the impact of filled data on downstream precipitation statistics"
            ]
        }
    
    def _fill_gap(self, df: pd.DataFrame, gap: Dict, date_col: str, precip_col: str):
        """Fill a single gap using linear interpolation only."""
        gap_length = gap['length']
        
        if gap_length > self.max_fill_gap_days:
            logger.warning(f"Gap of {gap_length} days exceeds maximum fill length ({self.max_fill_gap_days})")
            self.fill_stats['unfilled_gaps'] += 1
            return
        
        # Use linear interpolation for all gaps
        success = self._linear_interpolation(df, gap, date_col, precip_col)
        if success:
            self.fill_stats['linear_interpolation'] += 1
            self.fill_stats['total_days_filled'] += gap_length
            logger.info(f"Filled {gap_length}-day gap from {gap['start_date'].date()} to {gap['end_date'].date()} using linear interpolation")
        else:
            self.fill_stats['unfilled_gaps'] += 1
            logger.warning(f"Could not fill gap from {gap['start_date'].date()} to {gap['end_date'].date()} - no valid neighboring values")
    
    def _linear_interpolation(self, df: pd.DataFrame, gap: Dict, date_col: str, precip_col: str) -> bool:
        """Fill gaps using smart interpolation for precipitation data."""
        start_idx = gap['start_idx']
        end_idx = gap['end_idx']
        
        # Find the nearest valid data points before and after the gap
        before_val = None
        after_val = None
        before_idx = None
        after_idx = None
        
        # Search backwards for valid data
        for i in range(start_idx - 1, -1, -1):
            if not pd.isna(df.iloc[i][precip_col]):
                before_val = df.iloc[i][precip_col]
                before_idx = i
                break
        
        # Search forwards for valid data
        for i in range(end_idx + 1, len(df)):
            if not pd.isna(df.iloc[i][precip_col]):
                after_val = df.iloc[i][precip_col]
                after_idx = i
                break
        
        # Need both before and after values for interpolation
        if before_val is None or after_val is None:
            logger.debug(f"Cannot interpolate gap from {gap['start_date'].date()} - missing neighboring values")
            return False
        
        gap_length = end_idx - start_idx + 1
        
        # Smart precipitation interpolation logic
        if gap_length == 1:
            # Single day gap - use simple average
            interpolated_value = (before_val + after_val) / 2
            interpolated_value = max(0, interpolated_value)
            df.iloc[start_idx, df.columns.get_loc(precip_col)] = interpolated_value
            
        elif gap_length <= 3:
            # Short gaps (2-3 days) - use linear interpolation but bias toward zero
            total_span = after_idx - before_idx
            for i in range(gap_length):
                position = start_idx + i
                ratio = (position - before_idx) / total_span
                interpolated_value = before_val + ratio * (after_val - before_val)
                
                # Bias toward zero for precipitation (more realistic)
                # If both neighbors are small, reduce the interpolated values
                neighbor_avg = (before_val + after_val) / 2
                if neighbor_avg < 5.0:  # If average is less than 5mm
                    interpolated_value *= 0.3  # Reduce to 30% of linear value
                elif neighbor_avg < 15.0:  # If average is less than 15mm
                    interpolated_value *= 0.6  # Reduce to 60% of linear value
                
                interpolated_value = max(0, interpolated_value)
                df.iloc[position, df.columns.get_loc(precip_col)] = interpolated_value
                
        else:
            # Longer gaps (4+ days) - use mostly zeros with occasional non-zero days
            # This reflects the reality that most days have no precipitation
            
            # Calculate a "budget" of total precipitation to distribute
            total_precip_budget = (before_val + after_val) / 2 * 0.4  # Conservative estimate
            
            # Most days get zero, but distribute some precipitation across a few days
            values = [0.0] * gap_length
            
            if total_precip_budget > 1.0:  # Only if there's meaningful precipitation to distribute
                # Pick 1-2 days to have non-zero precipitation
                import random
                random.seed(42)  # For reproducible results
                
                if gap_length <= 7:
                    # For 4-7 day gaps, maybe 1 wet day
                    wet_days = 1
                else:
                    # For longer gaps, maybe 1-2 wet days
                    wet_days = min(2, gap_length // 4)
                
                # Randomly select which days get precipitation
                wet_indices = random.sample(range(gap_length), wet_days)
                precip_per_day = total_precip_budget / wet_days
                
                for idx in wet_indices:
                    values[idx] = precip_per_day
            
            # Apply the values
            for i, val in enumerate(values):
                df.iloc[start_idx + i, df.columns.get_loc(precip_col)] = max(0, val)
        
        logger.debug(f"Smart interpolation: filled {gap_length} days using precipitation-aware method")
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
            date_matches = df[df[date_col] == current_date].index
            if len(date_matches) == 0:
                logger.warning(f"No matching date found for {current_date}. Skipping this date.")
                continue
            
            date_idx = date_matches[0]
            df.iloc[date_idx, df.columns.get_loc(precip_col)] = climatological_value
        
        logger.info(f"Climatological fill: filled gap from {start_date.date()} to {end_date.date()}")
        return True
    
    def _analogous_year_fill(self, df: pd.DataFrame, gap: Dict, date_col: str, precip_col: str) -> bool:
        """Fill gaps using analogous year method."""
        gap_year = gap['start_date'].year
        gap_start_doy = gap['start_date'].dayofyear
        gap_end_doy = gap['end_date'].dayofyear
        
        # Validate input data
        if df.empty:
            logger.error("DataFrame is empty, cannot perform analogous year fill")
            return False
        
        if date_col not in df.columns or precip_col not in df.columns:
            logger.error(f"Required columns '{date_col}' or '{precip_col}' not found in DataFrame")
            return False
        
        # Find candidate years with complete data for this period AND good overall data quality
        candidate_years = []
        available_years = df[date_col].dt.year.unique()
        
        logger.info(f"Looking for analogous years for gap {gap['start_date'].date()} to {gap['end_date'].date()} (year {gap_year})")
        logger.info(f"Available years in dataset: {sorted(available_years)}")
        
        # First, assess data quality for all available years
        year_quality_scores = {}
        for year in available_years:
            if year == gap_year:
                continue
            # Calculate data completeness for the entire year
            year_data = df[df[date_col].dt.year == year]
            total_days = len(year_data)
            missing_days = year_data[precip_col].isna().sum()
            completeness = (total_days - missing_days) / total_days if total_days > 0 else 0
            
            # Only consider years with good overall data quality (>= 80% complete)
            if completeness >= 0.8:
                year_quality_scores[year] = completeness
                logger.debug(f"Year {year}: {completeness:.1%} complete ({total_days - missing_days}/{total_days} days)")
            else:
                logger.debug(f"Year {year}: {completeness:.1%} complete - EXCLUDED for poor quality")
        
        logger.info(f"Found {len(year_quality_scores)} years with good data quality (>=80% complete)")
        
        # Now check if these quality years have complete data for the specific gap period
        for year in sorted(year_quality_scores.keys(), key=lambda y: year_quality_scores[y], reverse=True):
            # Check if this year has complete data for the gap period
            year_start = datetime(year, 1, 1)
            gap_start_analog = year_start + timedelta(days=gap_start_doy - 1)
            gap_end_analog = year_start + timedelta(days=gap_end_doy - 1)
            
            # Handle year boundary crossing for day of year
            try:
                year_gap_data = df[
                    (df[date_col] >= gap_start_analog) & 
                    (df[date_col] <= gap_end_analog)
                ][precip_col]
                
                # Check if we have complete data for this specific period
                if year_gap_data.notna().all() and len(year_gap_data) == gap['length']:
                    candidate_years.append(year)
                    logger.debug(f"Year {year}: Has complete data for gap period ({len(year_gap_data)} days)")
                else:
                    missing_in_period = year_gap_data.isna().sum()
                    logger.debug(f"Year {year}: Missing {missing_in_period} days in gap period - EXCLUDED")
                    
            except Exception as e:
                logger.debug(f"Year {year}: Error checking gap period - {e}")
                continue
        
        logger.info(f"Found {len(candidate_years)} candidate years with both good overall quality and complete gap period data: {candidate_years}")
        
        # If no high-quality candidates found, try with progressively lower standards
        if not candidate_years:
            logger.warning(f"No high-quality candidate years found. Trying with relaxed standards...")
            
            # More aggressive fallback - try with much lower standards
            for min_completeness in [0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]:  # Very aggressive progression
                logger.info(f"Trying with minimum {min_completeness:.0%} data completeness...")
                
                for year in available_years:
                    if year == gap_year:
                        continue
                        
                    # Calculate data completeness for the entire year
                    year_data = df[df[date_col].dt.year == year]
                    total_days = len(year_data)
                    missing_days = year_data[precip_col].isna().sum()
                    completeness = (total_days - missing_days) / total_days if total_days > 0 else 0
                    
                    if completeness >= min_completeness:
                        # For low quality data, just check if we have SOME data for the gap period
                        year_start = datetime(year, 1, 1)
                        gap_start_analog = year_start + timedelta(days=gap_start_doy - 1)
                        gap_end_analog = year_start + timedelta(days=gap_end_doy - 1)
                        
                        try:
                            year_gap_data = df[
                                (df[date_col] >= gap_start_analog) & 
                                (df[date_col] <= gap_end_analog)
                            ][precip_col]
                            
                            # For very relaxed standards, just require more than 50% data in the gap period
                            if min_completeness <= 0.3:
                                required_data_fraction = 0.5  # At least 50% of gap period has data
                            else:
                                required_data_fraction = 0.8  # 80% for moderate relaxation
                            
                            available_data_fraction = year_gap_data.notna().sum() / len(year_gap_data) if len(year_gap_data) > 0 else 0
                            
                            if available_data_fraction >= required_data_fraction:
                                candidate_years.append(year)
                                logger.debug(f"Year {year}: Added with {completeness:.1%} completeness and {available_data_fraction:.1%} gap period coverage")
                                
                        except Exception as e:
                            continue
                
                if candidate_years:
                    logger.info(f"Found {len(candidate_years)} candidate years with {min_completeness:.0%} completeness: {candidate_years}")
                    break
            
            # Final desperate attempt - find ANY year with ANY data in the gap period
            if not candidate_years:
                logger.warning("Attempting final desperate search for any usable year...")
                for year in available_years:
                    if year == gap_year:
                        continue
                    
                    year_data = df[df[date_col].dt.year == year]
                    if len(year_data) == 0:
                        continue
                    
                    # Check if this year has ANY precipitation data (not necessarily in the gap period)
                    if year_data[precip_col].notna().any():
                        candidate_years.append(year)
                        logger.debug(f"Year {year}: Added as last resort (has some precipitation data)")
                
                if candidate_years:
                    logger.warning(f"Found {len(candidate_years)} years as last resort candidates: {candidate_years}")
                else:
                    logger.error("No years found with any usable precipitation data!")
        
        if not candidate_years:
            logger.warning(f"No suitable candidate years found even with relaxed standards")
            return False
        
        logger.info(f"Found {len(candidate_years)} total candidate years: {candidate_years}")
        
        # Progressive similarity checking - try with increasingly relaxed standards
        similarity_attempts = [
            (0.8, "very high"),
            (0.7, "high"), 
            (0.6, "good"),
            (0.5, "moderate"),
            (0.4, "low"),
            (0.3, "very low"),
            (0.2, "minimal"),
            (0.1, "any")
        ]
        
        best_year = None
        for similarity_threshold, description in similarity_attempts:
            logger.info(f"Trying {description} similarity threshold: {similarity_threshold}")
            
            # Try each candidate year to see if it meets this similarity threshold
            for candidate_year in candidate_years:
                try:
                    logger.debug(f"Calculating similarity for year {candidate_year}")
                    similarity_score = self._calculate_single_year_similarity(
                        df, gap_year, candidate_year, date_col, precip_col
                    )
                    
                    if similarity_score >= similarity_threshold:
                        logger.info(f"Found suitable year {candidate_year} with similarity {similarity_score:.3f} (threshold: {similarity_threshold})")
                        best_year = candidate_year
                        break
                        
                    logger.debug(f"Year {candidate_year}: similarity {similarity_score:.3f} below threshold {similarity_threshold}")
                    
                except Exception as e:
                    logger.debug(f"Error calculating similarity for year {candidate_year}: {e}")
                    continue
            
            if best_year is not None:
                break
        
        # If still no year found, just pick the first candidate (desperate fallback)
        if best_year is None:
            if candidate_years and len(candidate_years) > 0:
                best_year = candidate_years[0]
                logger.warning(f"No year met similarity criteria. Using {best_year} as last resort.")
            else:
                logger.error(f"No candidate years available for gap filling")
                return False
        
        logger.info(f"Selected year {best_year} as most similar to {gap_year}")
        logger.debug(f"Data date range: {df[date_col].min()} to {df[date_col].max()}")
        logger.debug(f"Gap to fill: {gap['start_date']} to {gap['start_date'] + timedelta(days=gap['length']-1)}")
        
        # Copy data from best analogous year
        year_start = datetime(best_year, 1, 1)
        filled_count = 0
        
        for i in range(gap['length']):
            gap_date = gap['start_date'] + timedelta(days=i)
            analog_date = year_start + timedelta(days=gap_date.dayofyear - 1)
            
            logger.debug(f"Trying to fill {gap_date} using data from {analog_date}")
            
            # Find analog value with error checking
            analog_matches = df[df[date_col] == analog_date][precip_col]
            if analog_matches.empty:
                logger.debug(f"No exact match for {analog_date}, trying nearby dates...")
                # If no exact match, try nearby dates
                analog_value = None
                for offset in [-1, 1, -2, 2]:
                    alt_date = analog_date + timedelta(days=offset)
                    alt_matches = df[df[date_col] == alt_date][precip_col].dropna()
                    if not alt_matches.empty:
                        analog_value = alt_matches.iloc[0]
                        logger.debug(f"Found nearby data at {alt_date}: {analog_value}")
                        break
                
                if analog_value is None:
                    # If still no match, use fallback value
                    logger.debug(f"No analog data found for {analog_date}, using 0.0 as fallback")
                    analog_value = 0.0  # Default to 0 if no data available
            else:
                # Check if we have valid analog data (not NaN)
                valid_analog_data = analog_matches.dropna()
                if not valid_analog_data.empty:
                    analog_value = valid_analog_data.iloc[0]
                    logger.debug(f"Found analog data at {analog_date}: {analog_value}")
                else:
                    logger.debug(f"Analog data at {analog_date} is NaN, using 0.0 as fallback")
                    analog_value = 0.0
            
            # Find gap index with error checking
            gap_matches = df[df[date_col] == gap_date].index
            if len(gap_matches) == 0:
                logger.warning(f"No matching date found for gap date {gap_date}. Skipping.")
                continue  # Skip if no matching gap date found
            
            gap_idx = gap_matches[0]
            
            # Make sure we have a valid analog value
            if pd.isna(analog_value):
                logger.debug(f"Analog value is NaN for {gap_date}, using 0.0")
                analog_value = 0.0
                
            df.iloc[gap_idx, df.columns.get_loc(precip_col)] = analog_value
            filled_count += 1
        
        logger.info(f"Analogous year fill: filled {filled_count}/{gap['length']} days from gap {gap['start_date'].date()} using year {best_year}")
        return True
    
    def _calculate_single_year_similarity(self, df: pd.DataFrame, target_year: int, candidate_year: int, 
                                        date_col: str, precip_col: str) -> float:
        """Calculate similarity between target year and a single candidate year."""
        try:
            # Get precipitation data for both years
            target_data = df[df[date_col].dt.year == target_year][precip_col].dropna()
            candidate_data = df[df[date_col].dt.year == candidate_year][precip_col].dropna()
            
            # Need some minimum data to calculate similarity
            if len(target_data) < 30 or len(candidate_data) < 30:
                logger.debug(f"Insufficient data for similarity calculation: target={len(target_data)}, candidate={len(candidate_data)}")
                return 0.0
            
            # Calculate basic precipitation statistics for comparison
            target_stats = {
                'mean': target_data.mean(),
                'std': target_data.std(),
                'wet_days': (target_data > 0).sum() / len(target_data),
                'max': target_data.max(),
                'q75': target_data.quantile(0.75),
                'q25': target_data.quantile(0.25)
            }
            
            candidate_stats = {
                'mean': candidate_data.mean(),
                'std': candidate_data.std(),
                'wet_days': (candidate_data > 0).sum() / len(candidate_data),
                'max': candidate_data.max(),
                'q75': candidate_data.quantile(0.75),
                'q25': candidate_data.quantile(0.25)
            }
            
            # Calculate normalized differences (0 = identical, 1 = completely different)
            similarities = []
            
            # Mean precipitation similarity
            if target_stats['mean'] > 0 and candidate_stats['mean'] > 0:
                mean_diff = abs(target_stats['mean'] - candidate_stats['mean']) / max(target_stats['mean'], candidate_stats['mean'])
                similarities.append(1 - min(mean_diff, 1.0))
            
            # Wet day frequency similarity
            wet_day_diff = abs(target_stats['wet_days'] - candidate_stats['wet_days'])
            similarities.append(1 - min(wet_day_diff, 1.0))
            
            # Standard deviation similarity (variability)
            if target_stats['std'] > 0 and candidate_stats['std'] > 0:
                std_diff = abs(target_stats['std'] - candidate_stats['std']) / max(target_stats['std'], candidate_stats['std'])
                similarities.append(1 - min(std_diff, 1.0))
            
            # Overall similarity is the average of individual similarities
            overall_similarity = sum(similarities) / len(similarities) if similarities else 0.0
            
            logger.debug(f"Year {candidate_year} vs {target_year}: similarity = {overall_similarity:.3f}")
            return overall_similarity
            
        except Exception as e:
            logger.debug(f"Error calculating similarity between years {target_year} and {candidate_year}: {e}")
            return 0.0

    def _find_most_similar_year(self, df: pd.DataFrame, gap_year: int, 
                               candidate_years: List[int], date_col: str, precip_col: str) -> Optional[int]:
        """Find the most meteorologically similar year for gap filling."""
        
        # Compare seasonal patterns and monthly totals
        best_year = None
        best_score = -1
        
        for candidate_year in candidate_years:
            # Calculate meteorological similarity
            meteorological_similarity = self._calculate_year_similarity(
                df, gap_year, candidate_year, date_col, precip_col
            )
            
            # Calculate temporal proximity bonus (closer years get slight preference)
            time_distance = abs(gap_year - candidate_year)
            max_time_distance = max([abs(gap_year - y) for y in candidate_years]) if len(candidate_years) > 1 else 1
            temporal_bonus = 0.1 * (1 - time_distance / max_time_distance) if max_time_distance > 0 else 0
            
            # Calculate data quality bonus
            year_data = df[df[date_col].dt.year == candidate_year]
            completeness = (len(year_data) - year_data[precip_col].isna().sum()) / len(year_data)
            quality_bonus = 0.1 * completeness  # Up to 10% bonus for complete data
            
            # Combined score
            combined_score = meteorological_similarity + temporal_bonus + quality_bonus
            
            logger.debug(f"Year {candidate_year}: met_sim={meteorological_similarity:.3f}, "
                        f"temp_bonus={temporal_bonus:.3f}, qual_bonus={quality_bonus:.3f}, "
                        f"total={combined_score:.3f}")
            
            if combined_score > best_score and meteorological_similarity >= self.min_similarity_threshold:
                best_score = combined_score
                best_year = candidate_year
        
        if best_year:
            logger.info(f"Selected year {best_year} as most similar to {gap_year} (score: {best_score:.3f})")
        
        return best_year
    
    def _calculate_year_similarity(self, df: pd.DataFrame, year1: int, year2: int,
                                  date_col: str, precip_col: str) -> float:
        """Calculate similarity between two years based on seasonal patterns."""
        
        try:
            # Get data for both years, only including non-null values
            year1_data = df[(df[date_col].dt.year == year1) & df[precip_col].notna()].copy()
            year2_data = df[(df[date_col].dt.year == year2) & df[precip_col].notna()].copy()
            
            if len(year1_data) == 0 or len(year2_data) == 0:
                logger.warning(f"No valid data found for year comparison: {year1} vs {year2}")
                return 0
            
            # Calculate data availability for both years
            year1_completeness = len(year1_data) / 365  # Approximate
            year2_completeness = len(year2_data) / 365
            
            # Require both years to have reasonable data coverage
            if year1_completeness < 0.7 or year2_completeness < 0.7:
                logger.debug(f"Insufficient data coverage for comparison: {year1} ({year1_completeness:.1%}) vs {year2} ({year2_completeness:.1%})")
                return 0
            
            # Calculate monthly totals for both years
            year1_monthly = year1_data.groupby(year1_data[date_col].dt.month)[precip_col].sum()
            year2_monthly = year2_data.groupby(year2_data[date_col].dt.month)[precip_col].sum()
            
            # Find common months with data
            common_months = set(year1_monthly.index) & set(year2_monthly.index)
            if len(common_months) < 8:  # Need at least 8 months for comparison
                logger.debug(f"Insufficient common months for year comparison: {year1} vs {year2} ({len(common_months)} months)")
                return 0
            
            monthly1 = [year1_monthly[month] for month in sorted(common_months)]
            monthly2 = [year2_monthly[month] for month in sorted(common_months)]
            
            # Calculate multiple similarity measures
            
            # 1. Correlation of monthly totals
            if len(monthly1) < 3:
                logger.debug(f"Insufficient data points for correlation: {len(monthly1)}")
                return 0
            
            # Check for sufficient variance
            if np.std(monthly1) < 0.01 or np.std(monthly2) < 0.01:
                logger.debug(f"Insufficient variance in monthly data for year comparison: {year1} vs {year2}")
                return 0
            
            correlation, p_value = stats.pearsonr(monthly1, monthly2)
            
            # 2. Similarity in annual total (normalized)
            total1 = sum(monthly1)
            total2 = sum(monthly2)
            if total1 + total2 > 0:
                total_similarity = 1 - abs(total1 - total2) / (total1 + total2)
            else:
                total_similarity = 1  # Both are zero
            
            # 3. Seasonal pattern similarity (wet/dry season ratio)
            try:
                # Define wet season (typically May-Oct) and dry season (Nov-Apr)
                wet_months = [5, 6, 7, 8, 9, 10]
                dry_months = [11, 12, 1, 2, 3, 4]
                
                wet1 = sum([year1_monthly.get(m, 0) for m in wet_months if m in year1_monthly.index])
                dry1 = sum([year1_monthly.get(m, 0) for m in dry_months if m in year1_monthly.index])
                wet2 = sum([year2_monthly.get(m, 0) for m in wet_months if m in year2_monthly.index])
                dry2 = sum([year2_monthly.get(m, 0) for m in dry_months if m in year2_monthly.index])
                
                ratio1 = wet1 / (dry1 + 1)  # Add 1 to avoid division by zero
                ratio2 = wet2 / (dry2 + 1)
                
                if ratio1 + ratio2 > 0:
                    seasonal_similarity = 1 - abs(ratio1 - ratio2) / (ratio1 + ratio2 + 0.1)
                else:
                    seasonal_similarity = 1
                    
            except Exception as e:
                logger.debug(f"Error calculating seasonal similarity: {e}")
                seasonal_similarity = 0.5  # Default moderate similarity
            
            # Combine similarities with weights
            if p_value < 0.05:  # Statistically significant correlation
                correlation_weight = 0.6
                total_weight = 0.25
                seasonal_weight = 0.15
            else:  # Not significant correlation, rely more on totals and patterns
                correlation_weight = 0.3
                total_weight = 0.4
                seasonal_weight = 0.3
                correlation = max(0, correlation)  # Don't penalize for insignificant correlation
            
            combined_similarity = (
                correlation_weight * max(0, correlation) +
                total_weight * total_similarity +
                seasonal_weight * seasonal_similarity
            )
            
            logger.debug(f"Year similarity {year1} vs {year2}: "
                        f"corr={correlation:.3f}(p={p_value:.3f}), "
                        f"total_sim={total_similarity:.3f}, "
                        f"seasonal_sim={seasonal_similarity:.3f}, "
                        f"combined={combined_similarity:.3f}")
            
            return combined_similarity
            
        except Exception as e:
            logger.error(f"Error calculating year similarity between {year1} and {year2}: {str(e)}")
            return 0
    
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
        
        # Analyze missing data by year
        yearly_analysis = self._analyze_yearly_gaps(df, date_col, precip_col, gaps)
        
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
            'yearly_analysis': yearly_analysis,
            'validation_results': validation,
            'data_quality': {
                'mean_precipitation': float(df[precip_col].mean()),
                'std_precipitation': float(df[precip_col].std()),
                'min_precipitation': float(df[precip_col].min()),
                'max_precipitation': float(df[precip_col].max()),
                'zero_precipitation_days': int((df[precip_col] == 0).sum())
            },
            'recommendations': self._generate_recommendations(validation, gaps, yearly_analysis)
        }
        
        return report
    
    def _generate_recommendations(self, validation: Dict, gaps: List[Dict], yearly_analysis: Dict) -> List[str]:
        """Generate recommendations based on filling results."""
        recommendations = []
        
        if not validation['quality_good']:
            recommendations.append("Review filled data quality - statistical properties may have changed significantly")
        
        if validation['filled_data_negative'] > 0:
            recommendations.append("Some filled values are negative - review interpolation method")
        
        if validation['filled_data_extreme'] > 0:
            recommendations.append("Some filled values appear extreme - consider additional quality control")
        
        long_gaps = [gap for gap in gaps if gap['length'] > 30]
        if long_gaps:
            recommendations.append(f"Found {len(long_gaps)} very long gaps (>30 days) - filled values may be less reliable for these")
        
        if self.fill_stats['unfilled_gaps'] > 0:
            recommendations.append("Some gaps could not be filled - these were at the beginning/end of the dataset or exceeded the maximum gap size")
        
        # Add yearly analysis recommendations
        significant_years = yearly_analysis.get('years_with_significant_gaps', {})
        if significant_years:
            recommendations.append(f"⚠️  {len(significant_years)} years have >90 missing days - exercise caution when using these years for statistical modeling")
            
            # Highlight worst years
            worst_years = [(year, data['percent_missing']) for year, data in significant_years.items()]
            worst_years.sort(key=lambda x: x[1], reverse=True)
            
            if worst_years:
                top_3_worst = worst_years[:3]
                years_list = [f"{year} ({pct}% missing)" for year, pct in top_3_worst]
                recommendations.append(f"Years with highest missing data: {', '.join(years_list)}")
        
        # Add positive feedback for successful filling
        total_filled = sum(gap['length'] for gap in gaps if gap['length'] <= self.max_fill_gap_days)
        if total_filled > 0 and self.fill_stats['unfilled_gaps'] == 0:
            recommendations.append("✅ Data filling completed successfully using smart interpolation")
        
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
