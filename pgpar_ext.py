import pandas as pd
import numpy as np
from scipy.stats import gamma, norm
from pgpar import calculate_params  # Importing calculate_params from pg_par

def calculate_ext_params(precip_ts, window_years=3, output_path=None):
    """
    Calculate gamma distribution parameters for pww, pwd, alpha, and beta 
    over time-shifted windows in the precipitation time series.

    Parameters:
    timeseries : TimeSeries
        Historical daily time series with 'DATE' as index and 'PRCP' as column.
    window_years : int, optional
        Number of years per segment for parameter calculation, default is 3.
    output_path : str, optional
        Base path for output files. If provided, saves parameter samples to CSV files.

    Returns:
    shape_table, scale_table : pd.DataFrame
        Two DataFrames containing shape and scale parameters for gamma distributions 
        for each month and each parameter (pww, pwd, alpha, beta).
    """
    # Initialize storage for samples for each month and parameter
    samples = {param: {month: [] for month in range(1, 13)} for param in ['PWW', 'PWD', 'ALPHA', 'BETA']}

    # Set up the initial window parameters
    start_date = pd.Timestamp(f"{precip_ts.index[0].year}-01-01")
    dataset_end_date = precip_ts.index[-1]
    end_date = pd.Timestamp(f"{start_date.year + window_years - 1}-12-31")

    # Perform calculations for each window
    while end_date <= dataset_end_date:
        # Find the end date of the window, subtract 1 day to avoid advancing to start of the next year
        end_date = pd.Timestamp(f"{start_date.year + window_years - 1}-12-31")
        # Create a copy of a trimmed window of the time series
        window_timeseries = precip_ts[start_date:end_date]
        # Calculate and store parameters for the current 3-year window
        params = calculate_params(window_timeseries)
        
        # Collect parameters by month
        for param, monthly_values in params.items():
            for month, value in monthly_values.items():
                samples[param][month].append(value)

        # Shift the window forward by one year
        start_date = pd.Timestamp(f"{start_date.year + 1}-01-01")
    # Convert samples dictionary to DataFrame for easier CSV export
    samples_df = {param: pd.DataFrame(monthly_values) for param, monthly_values in samples.items()}
    
    # Write each parameter's samples to a separate CSV file if output path provided
    if output_path:
        from pathlib import Path
        base_path = Path(output_path)
        base_name = base_path.stem
        base_dir = base_path.parent
        
        for param, df in samples_df.items():
            output_file = base_dir / f"{base_name}_{param}_samples.csv"
            df.to_csv(output_file, index_label='Month')
    
    # Fit gamma distributions for each month and each parameter
    ext_params = fit_normal_distributions(samples)
    
    return ext_params

def fit_gamma_distributions(all_samples):
    # Initialize storage for gamma distribution fitting results for shape and scale separately
    shape_params = {param: [] for param in ['PWW', 'PWD', 'ALPHA', 'BETA']}
    scale_params = {param: [] for param in ['PWW', 'PWD', 'ALPHA', 'BETA']}

    # Fit gamma distributions for each month and each parameter
    for param in ['PWW', 'PWD', 'ALPHA', 'BETA']:
        for month in range(1, 13):  # Month 1-12
            samples = all_samples[param][month]

            if len(samples) > 0:  # Fit gamma if we have at least one sample
                shape, loc, scale = gamma.fit(samples, floc=0)
                shape_params[param].append(shape)
                scale_params[param].append(scale)
            else:
                shape_params[param].append(0)  # Zero if no data
                scale_params[param].append(0)

    # Convert dictionaries to DataFrames, indexed by month (1-12)
    shape_df = pd.DataFrame(shape_params, index=range(1, 13))
    scale_df = pd.DataFrame(scale_params, index=range(1, 13))
    
    return shape_df, scale_df

def fit_normal_distributions(all_samples):
    # Initialize storage for normal distribution fitting results for mean and std dev separately
    mean_params = {param: [] for param in ['PWW', 'PWD', 'ALPHA', 'BETA']}
    std_params = {param: [] for param in ['PWW', 'PWD', 'ALPHA', 'BETA']}

    # Fit normal distributions for each month and each parameter
    for param in ['PWW', 'PWD', 'ALPHA', 'BETA']:
        for month in range(1, 13):  # Month 1-12
            samples = all_samples[param][month]

            if len(samples) > 0:  # Fit normal if we have at least one sample
                mean, std = norm.fit(samples)
                mean_params[param].append(mean)
                std_params[param].append(std)
            else:
                mean_params[param].append(0)  # Zero if no data
                std_params[param].append(0)

    # Convert dictionaries to DataFrames, indexed by month (1-12)
    mean_df = pd.DataFrame(mean_params, index=range(1, 13))
    std_df = pd.DataFrame(std_params, index=range(1, 13))
    
    return mean_df, std_df
