# precipitation_gap_analyzer/gap_analyzer.py

import pandas as pd
import sys

def analyze_gaps(df, data_col_name, gap_threshold):
    """
    Analyzes a single data column within the DataFrame for missing data gaps.

    Args:
        df (pd.DataFrame): Input DataFrame with DateTimeIndex, sorted.
        data_col_name (str): The name of the data column to analyze.
        gap_threshold (int): The threshold defining short vs. long gaps.

    Returns:
        dict: A dictionary containing analysis results for the column,
              or None if analysis cannot proceed.
              Keys: 'total_days', 'min_date', 'max_date', 'total_missing_days',
                    'short_gap_count', 'long_gap_count', 'long_gaps' (DataFrame)
    """
    if df is None or df.empty:
        print(f"Error: Input DataFrame is empty or None, cannot analyze column '{data_col_name}'.", file=sys.stderr)
        return None
    if data_col_name not in df.columns:
        print(f"Error: Data column '{data_col_name}' not found in DataFrame for analysis.", file=sys.stderr)
        return None
    if not isinstance(df.index, pd.DatetimeIndex):
         print(f"Error: DataFrame index is not a DatetimeIndex for column '{data_col_name}'.", file=sys.stderr)
         return None

    print(f"\n--- Analyzing Gaps for Column: '{data_col_name}' ---")

    # 1. Determine Overall Date Range from the prepared DataFrame's index
    min_date = df.index.min()
    max_date = df.index.max()
    print(f"Data range in source: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")

    if pd.isna(min_date) or pd.isna(max_date):
         print(f"Error: Could not determine valid date range for column '{data_col_name}'.", file=sys.stderr)
         return None

    # 2. Create Complete Daily Date Range
    full_range = pd.date_range(start=min_date, end=max_date, freq='D')
    total_days_in_range = len(full_range)
    print(f"Full analysis range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({total_days_in_range} days)")


    # 3. Reindex DataFrame & Isolate Series
    # Select only the column needed *before* reindexing for efficiency
    series_original = df[data_col_name]
    series_reindexed = series_original.reindex(full_range)

    # 4. Identify Missing Values (NaN in the reindexed series)
    is_missing = series_reindexed.isna()
    total_missing_days = int(is_missing.sum()) # Cast to int
    print(f"Total missing days found: {total_missing_days}")

    if total_missing_days == 0:
        print("No missing days found.")
        return {
            'total_days': total_days_in_range,
            'min_date': min_date,
            'max_date': max_date,
            'total_missing_days': 0,
            'short_gap_count': 0,
            'long_gap_count': 0,
            'long_gaps': pd.DataFrame(columns=['start_date', 'end_date', 'duration']) # Empty DF
        }
    elif total_missing_days == total_days_in_range:
         print("Warning: All days in the range are missing.", file=sys.stderr)
         single_gap = pd.DataFrame([{
             'start_date': min_date,
             'end_date': max_date,
             'duration': total_days_in_range
             }])
         is_long = total_days_in_range > gap_threshold
         return {
            'total_days': total_days_in_range,
            'min_date': min_date,
            'max_date': max_date,
            'total_missing_days': total_missing_days,
            'short_gap_count': 0 if is_long else 1,
            'long_gap_count': 1 if is_long else 0,
            'long_gaps': single_gap if is_long else pd.DataFrame(columns=['start_date', 'end_date', 'duration'])
        }


    # 5. Identify Consecutive Gaps
    # Calculate changes and cumulative sum to identify blocks of consecutive missing days
    is_missing_int = is_missing.astype(int)
    # A block starts when diff goes from 0 to 1. A block ends when diff goes from 1 to 0 (-1).
    # We group by the cumulative sum of block starts.
    group_ids = is_missing_int.diff().fillna(0).eq(1).cumsum()

    # Filter only the missing periods and group them
    missing_periods = is_missing[is_missing] # Select only True values (where data is missing)
    grouped_gaps = missing_periods.groupby(group_ids[is_missing])

    gaps = []
    for _, period_indices in grouped_gaps:
        if not period_indices.empty:
            start = period_indices.index.min()
            end = period_indices.index.max()
            duration = len(period_indices) # Duration is simply the number of days in the gap
            gaps.append({'start_date': start, 'end_date': end, 'duration': duration})

    # 6. Categorize Gaps
    short_gaps_count = 0
    long_gaps_count = 0
    long_gaps_details = []

    for gap in gaps:
        if gap['duration'] <= gap_threshold:
            short_gaps_count += 1
        else:
            long_gaps_count += 1
            long_gaps_details.append(gap)

    print(f"Identified {short_gaps_count} short gaps (<= {gap_threshold} day(s))")
    print(f"Identified {long_gaps_count} long gaps (> {gap_threshold} day(s))")

    # Prepare results dictionary
    results = {
        'total_days': total_days_in_range,
        'min_date': min_date,
        'max_date': max_date,
        'total_missing_days': total_missing_days,
        'short_gap_count': short_gaps_count,
        'long_gap_count': long_gaps_count,
        'long_gaps': pd.DataFrame(long_gaps_details) # Convert list of dicts to DataFrame
    }

    return results

def analyze_yearly_gaps(df, data_col_name, significant_threshold=90):
    """
    Analyze missing data patterns by year, focusing on years with significant gaps.
    
    Args:
        df (pd.DataFrame): Input DataFrame with DateTimeIndex, sorted.
        data_col_name (str): The name of the data column to analyze.
        significant_threshold (int): Threshold for flagging years with significant gaps (default: 90 days)
    
    Returns:
        dict: Dictionary with yearly analysis including:
            - years_with_significant_gaps: Years with >threshold missing days
            - summary_statistics: Overall statistics about yearly gaps
    """
    if df is None or df.empty:
        print(f"Error: Input DataFrame is empty or None, cannot analyze yearly patterns for '{data_col_name}'.", file=sys.stderr)
        return None
    if data_col_name not in df.columns:
        print(f"Error: Data column '{data_col_name}' not found in DataFrame for yearly analysis.", file=sys.stderr)
        return None
    if not isinstance(df.index, pd.DatetimeIndex):
        print(f"Error: DataFrame index is not a DatetimeIndex for yearly analysis of '{data_col_name}'.", file=sys.stderr)
        return None

    print(f"\n--- Analyzing Yearly Gap Patterns for Column: '{data_col_name}' ---")

    # Prepare data with year column
    df_copy = df.copy()
    df_copy['year'] = df_copy.index.year
    
    # Calculate missing days per year
    missing_by_year = df_copy.groupby('year')[data_col_name].apply(lambda x: x.isna().sum()).to_dict()
    
    # Calculate maximum consecutive missing days per year
    max_consecutive_by_year = {}
    
    for year in missing_by_year.keys():
        year_data = df_copy[df_copy['year'] == year]
        if len(year_data) == 0:
            max_consecutive_by_year[year] = 0
            continue
            
        # Find maximum consecutive missing days in this year
        missing_mask = year_data[data_col_name].isna()
        max_consecutive = 0
        current_consecutive = 0
        
        for is_missing in missing_mask:
            if is_missing:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        max_consecutive_by_year[year] = max_consecutive
    
    # Filter to years with >significant_threshold missing days
    significant_years = {
        year: {
            'total_missing_days': missing_days,
            'max_consecutive_missing': max_consecutive_by_year.get(year, 0),
            'total_days_in_year': len(df_copy[df_copy['year'] == year]),
            'percent_missing': round(missing_days / len(df_copy[df_copy['year'] == year]) * 100, 1)
        }
        for year, missing_days in missing_by_year.items()
        if missing_days > significant_threshold
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
        'years_with_no_gaps': sum(1 for count in all_missing_counts if count == 0),
        'significant_threshold': significant_threshold
    }
    
    print(f"Years analyzed: {summary_stats['total_years_analyzed']}")
    print(f"Years with >{significant_threshold} missing days: {summary_stats['years_with_significant_gaps']}")
    print(f"Average missing days per year: {summary_stats['avg_missing_days_per_year']}")
    print(f"Maximum missing days in any year: {summary_stats['max_missing_days_any_year']}")
    print(f"Maximum consecutive missing days: {summary_stats['max_consecutive_missing_any_year']}")
    
    return {
        'summary_statistics': summary_stats,
        'years_with_significant_gaps': dict(sorted(significant_years.items())),
        'notes': [
            f"Only years with >{significant_threshold} missing days are flagged as 'significant'",
            "Years with extensive gaps may not be suitable for statistical modeling",
            "Consider the impact of filled data on downstream precipitation statistics"
        ]
    }

if __name__ == '__main__':
    # Example usage requires a prepared DataFrame (like one from data_loader)
    print("\n--- Testing Gap Analyzer ---")

    # Create a more complex sample DataFrame for testing gaps
    dates = pd.date_range(start='2023-01-01', end='2023-01-20', freq='D')
    data = {
        'Value': [1, 2, pd.NA, pd.NA, 5, 6, 7, pd.NA, 9, 10,
                  pd.NA, pd.NA, pd.NA, 14, 15, pd.NA, 17, 18, pd.NA, pd.NA]
    }
    test_df = pd.DataFrame(data, index=dates)
    test_df.index.name = 'DATE'
    print("Test DataFrame:")
    print(test_df)
    print("-" * 20)

    # Test case 1: gap_threshold = 1 (single missing day is short)
    print("\nAnalyzing with gap_threshold = 1")
    results_1 = analyze_gaps(test_df.copy(), 'Value', gap_threshold=1)
    if results_1:
        print("\nAnalysis Results (Threshold=1):")
        for key, value in results_1.items():
            if key != 'long_gaps':
                print(f"  {key}: {value}")
            else:
                print(f"  {key}:")
                print(value.to_string(index=False)) # Nicer print for DF

    print("-" * 20)

    # Test case 2: gap_threshold = 2 (1 or 2 missing days are short)
    print("\nAnalyzing with gap_threshold = 2")
    results_2 = analyze_gaps(test_df.copy(), 'Value', gap_threshold=2)
    if results_2:
        print("\nAnalysis Results (Threshold=2):")
        for key, value in results_2.items():
            if key != 'long_gaps':
                print(f"  {key}: {value}")
            else:
                print(f"  {key}:")
                print(value.to_string(index=False)) # Nicer print for DF

    # Test case 3: All missing
    print("-" * 20)
    print("\nAnalyzing All Missing Data")
    all_missing_df = pd.DataFrame({'Value': [pd.NA]*5}, index=pd.date_range('2023-02-01', periods=5, freq='D'))
    all_missing_df.index.name='DATE'
    results_3 = analyze_gaps(all_missing_df, 'Value', gap_threshold=1)
    if results_3:
        print("\nAnalysis Results (All Missing, Threshold=1):")
        for key, value in results_3.items():
            if key != 'long_gaps':
                print(f"  {key}: {value}")
            else:
                print(f"  {key}:")
                print(value.to_string(index=False))


     # Test case 4: No missing
    print("-" * 20)
    print("\nAnalyzing No Missing Data")
    no_missing_df = pd.DataFrame({'Value': range(5)}, index=pd.date_range('2023-03-01', periods=5, freq='D'))
    no_missing_df.index.name='DATE'
    results_4 = analyze_gaps(no_missing_df, 'Value', gap_threshold=1)
    if results_4:
        print("\nAnalysis Results (No Missing, Threshold=1):")
        for key, value in results_4.items():
            if key != 'long_gaps':
                print(f"  {key}: {value}")
            else:
                print(f"  {key}:")
                print(value.to_string(index=False))

    print("-" * 20)

    # Yearly analysis test
    print("\n--- Yearly Gap Analysis Test ---")
    yearly_results = analyze_yearly_gaps(test_df, 'Value', significant_threshold=2)
    if yearly_results:
        print("\nYearly Analysis Results:")
        for year, stats in yearly_results['years_with_significant_gaps'].items():
            print(f"Year {year}: {stats}")
        print("\nSummary Statistics:")
        for key, value in yearly_results['summary_statistics'].items():
            print(f"  {key}: {value}")