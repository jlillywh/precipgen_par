import pandas as pd
import numpy as np
from scipy.stats import linregress
import logging
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def gather_daily_stats(precip_series: pd.Series, wet_yesterday: bool) -> tuple[int, float, float, int, int, int, int, bool]:
    """
    Gather daily statistics for the given precipitation data.

    Parameters:
    ----------
    precip_series : pd.Series
        A pandas Series containing daily precipitation values for a specific month.
        The index should represent dates.

    Returns:
    -------
    Tuple[int, float, float, int, int, int, int]
        A tuple of statistics required for parameter computation:
        (wet_day_count, sum_precip, sum_log_precip, nww, nwd, ndw, ndd)

        - wet_day_count: Number of wet days (> 0.0 precipitation).
        - sum_precip: Total precipitation during the period.
        - sum_log_precip: Sum of log(precipitation) for wet days.
        - nww: Number of transitions from wet day to wet day.
        - nwd: Number of transitions from wet day to dry day.
        - ndw: Number of transitions from dry day to wet day.
        - ndd: Number of transitions from dry day to dry day.
        - wet_yesterday: The state of "wetness" on the last day of this month.

    Notes:
    -----
    - Unit dimensions are not important as long as they are consistent.
    - Assumes the Series is sorted by date.
    """
    # Initialize counters and accumulators
    wet_day_count = 0
    sum_precip = 0.0
    sum_log_precip = 0.0
    nww = nwd = ndw = ndd = 0

     # Iterate through all days
    for precipitation in precip_series:
        wet_today = precipitation > 0.0

        if wet_today:
            wet_day_count += 1
            sum_precip += precipitation
            sum_log_precip += np.log(precipitation)

        # Transition counters
        if wet_yesterday and wet_today:
            nww += 1
        elif wet_today and not wet_yesterday:
            nwd += 1
        elif not wet_today and wet_yesterday:
            ndw += 1
        else:
            ndd += 1

        # Update "yesterday" for the next iteration
        wet_yesterday = wet_today

    return wet_day_count, sum_precip, sum_log_precip, nww, nwd, ndw, ndd, wet_yesterday

def compute_4params(
    wet_count: int, 
    sum_precip: float, 
    sum_log_precip: float, 
    nww: int, 
    nwd: int, 
    ndw: int, 
    ndd: int
) -> tuple[float, float, float, float]:
    """
    Convert gathered stats into pww, pwd, alpha, and beta.

    Parameters:
    ----------
    wet_count : int
        Total number of wet days.
    sum_precip : float
        Total precipitation over wet days.
    sum_log_precip : float
        Sum of the logarithm of precipitation values for wet days.
    nww : int
        Number of transitions from wet to wet.
    nwd : int
        Number of transitions from wet to dry.
    ndw : int
        Number of transitions from dry to wet.
    ndd : int
        Number of transitions from dry to dry.

    Returns:
    -------
    Tuple[float, float, float, float]
        The four parameters: (pww, pwd, alpha, beta).
        - pww: Probability of wet day following a wet day.
        - pwd: Probability of wet day following a dry day.
        - alpha: Shape parameter for gamma distribution of precipitation.
        - beta: Scale parameter for gamma distribution of precipitation.

    Notes:
    -----
    - Ensures all returned parameters are non-zero and positive to avoid issues with downstream calculations.
    """
    # --- Conditional Handling for Low Wet-Day Count ---
    if wet_count < 3:
        pww = 0.00
        pwd = 0.00
        alpha = 0.001
        beta = 0.001
        return pww, pwd, alpha, beta
    
    # --- Calculate Transition Probabilities ---
    ww_plus_dw = nww + ndw  # Total transitions from wet
    wd_plus_dd = nwd + ndd  # Total transitions from dry
    pww = nww / ww_plus_dw if ww_plus_dw else 0.0
    pwd = nwd / wd_plus_dd if wd_plus_dd else 0.0

    # --- Calculate Means ---
    if wet_count > 0:
        rbar = sum_precip / wet_count  # Mean precipitation
        rlbar = sum_log_precip / wet_count  # Mean log precipitation
    else:
        rbar = rlbar = 0.0

    # --- Compute Alpha and Beta ---
    if rbar > 0:
        log_term = np.log(rbar) - rlbar
        anum = 8.898919 + 9.05995 * log_term + 0.9775373 * (log_term**2)
        adom = log_term * (17.79728 + 11.968477 * log_term + (log_term**2))
        alpha = min(anum / adom, 0.998) if adom > 0 else 0.001
        beta = rbar / alpha if alpha > 0 else 0.001
    else:
        alpha = beta = 0.001

    return pww, pwd, alpha, beta

def params(precip_ts: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate parameters for each month from the time series data,
    preserving the state of wet_yesterday across months and years.

    Parameters:
    ----------
    precip_ts : pd.DataFrame
        A DataFrame with 'DATE' as the index and 'VALUE' as the column.

    Returns:
    -------
    pd.DataFrame
        A 12x4 DataFrame of [pww, pwd, alpha, beta].
        Index = 1..12 for months.
    """
    # Initialize lists to store results for each month
    monthly_stats = {month: {'wet_day_count': 0, 'sum_precip': 0.0, 'sum_log_precip': 0.0, 'nww': 0, 'nwd': 0, 'ndw': 0, 'ndd': 0} for month in range(1, 13)}
    wet_yesterday = False  # Initial state

    # Iterate through the time series chronologically
    for date, precipitation in precip_ts['VALUE'].items():
        month = date.month
        wet_today = precipitation > 0.0

        # Update stats for the current month
        if wet_today:
            monthly_stats[month]['wet_day_count'] += 1
            monthly_stats[month]['sum_precip'] += precipitation
            monthly_stats[month]['sum_log_precip'] += np.log(precipitation)

        # Transition counters
        if wet_yesterday and wet_today:
            monthly_stats[month]['nww'] += 1
        elif wet_today and not wet_yesterday:
            monthly_stats[month]['nwd'] += 1
        elif not wet_today and wet_yesterday:
            monthly_stats[month]['ndw'] += 1
        else:
            monthly_stats[month]['ndd'] += 1

        # Update "wet_yesterday" for the next day
        wet_yesterday = wet_today

    # Compute parameters for each month
    pww_list, pwd_list, alpha_list, beta_list = [], [], [], []
    for month in range(1, 13):
        stats = monthly_stats[month]
        pww_, pwd_, alpha_, beta_ = compute_4params(
            stats['wet_day_count'],
            stats['sum_precip'],
            stats['sum_log_precip'],
            stats['nww'],
            stats['nwd'],
            stats['ndw'],
            stats['ndd']
        )
        pww_list.append(pww_)
        pwd_list.append(pwd_)
        alpha_list.append(alpha_)
        beta_list.append(beta_)

    # Compile results into a DataFrame
    df = pd.DataFrame({
        'PWW': pww_list,
        'PWD': pwd_list,
        'ALPHA': alpha_list,
        'BETA': beta_list
    }, index=range(1, 13))

    return df

def params_samples(precip_ts: pd.DataFrame, n_years: int = 1) -> pd.DataFrame:
    """
    Slide an n_years window over the time series. For each window,
    compute the 4 parameters (PWW, PWD, ALPHA, BETA).

    Parameters:
    ----------
    precip_ts : pd.DataFrame
        A DataFrame with 'DATE' as the index and 'VALUE' as the column.
        The DataFrame should be sorted by date.

    n_years : int, optional
        Number of years to include in each sliding window. Default is 1.

    Returns:
    -------
    pd.DataFrame
        A DataFrame with one row per window:
        ['YR', 'PWW', 'PWD', 'ALPHA', 'BETA']

        - YR : int
          The starting year of the window.
        - PWW : float
          Probability of wet day following a wet day.
        - PWD : float
          Probability of wet day following a dry day.
        - ALPHA : float
          Shape parameter for gamma distribution of precipitation.
        - BETA : float
          Scale parameter for gamma distribution of precipitation.

    Notes:
    -----
    - Skips windows with insufficient data (e.g., less than 2 valid days).
    - Preserves the wet_yesterday state across sliding windows.
    - Assumes the DataFrame is continuous and indexed by 'DATE'.
    """
    results = []  # List to store results for each sliding window
    wet_yesterday = False  # Initial state before the first window

    # Determine the range of years in the dataset
    start_year = precip_ts.index.year.min()
    end_year   = precip_ts.index.year.max()

    # Iterate through each sliding window
    for y in range(start_year, end_year - n_years + 1):
        # Define the start and end of the window
        start_date = f"{y}-01-01"
        end_date   = f"{y + n_years - 1}-12-31"  # Inclusive end date
        window_df  = precip_ts.loc[start_date:end_date]

        # Skip windows with insufficient data
        if len(window_df) < 2:
            print(f"Skipping window {start_date} to {end_date} due to insufficient data.")
            continue

        # Gather statistics and compute the parameters
        stats = gather_daily_stats(window_df['VALUE'], wet_yesterday) 
        wet_day_count, sum_precip, sum_log_precip, nww, nwd, ndw, ndd, wet_yesterday = stats

        # Compute the parameters
        pww_, pwd_, alpha_, beta_ = compute_4params(
            wet_day_count, sum_precip, sum_log_precip, nww, nwd, ndw, ndd
        )

        # Append the results for the current window
        results.append([y, pww_, pwd_, alpha_, beta_])

    # Convert results to a DataFrame
    df = pd.DataFrame(results, columns=['yr','PWW','PWD','ALPHA','BETA'])
    return df

def reversion(params_df: pd.DataFrame) -> pd.DataFrame:
    """
    Reversion Rate (1 - AR(1) slope):
    - Measures how quickly a time series returns to its long-term average.
    - High reversion rate (close to 1): The system quickly "forgets" past values.
    - Low reversion rate (close to 0): The system is highly persistent and depends strongly on past conditions.

    For more details, refer to:
    - Wilks, D. S. (2011). Statistical Methods in the Atmospheric Sciences (3rd Edition).
    - Online: https://en.wikipedia.org/wiki/Autoregressive_model

    Parameters:
    ----------
    params_df : pd.DataFrame
        A DataFrame with columns = [PWW, PWD, ALPHA, BETA].

    Returns:
    -------
    pd.DataFrame
        A DataFrame where columns are parameter names and values are the reversion rates.
    """
    rev_df = pd.DataFrame(columns=['PWW', 'PWD', 'ALPHA', 'BETA'], index=[0])

    for col in rev_df.columns:
        series = params_df[col].values

        # Skip if there are fewer than 2 samples
        if len(series) < 2:
            rev_df.at[0, col] = np.nan
            continue

        # Calculate AR(1) slope using linear regression
        x_t = series[:-1]  # Current time step
        x_t1 = series[1:]  # Next time step
        slope, intercept, r_value, p_value, std_err = linregress(x_t, x_t1)

        # Reversion rate is (1 - slope)
        rev_df.at[0, col] = 1 - slope

    return rev_df

def volatility(params_df: pd.DataFrame) -> pd.DataFrame:
    """
    Volatility:
    - Measures the variability or spread of a time series (calculated as the standard deviation).
    - High volatility: The parameter varies widely over time (e.g., more inconsistent precipitation patterns).
    - Low volatility: The parameter is more stable and consistent over time.

    This provides insights into how predictable or unpredictable a parameter is.

    For more details, refer to:
    - Wilks, D. S. (2011). Statistical Methods in the Atmospheric Sciences (3rd Edition).
    - Online: https://en.wikipedia.org/wiki/Standard_deviation

    Parameters:
    ----------
    params_df : pd.DataFrame
        A DataFrame with columns = [PWW, PWD, ALPHA, BETA].

    Returns:
    -------
    pd.DataFrame
        A DataFrame where columns are parameter names and values are the volatilities.
    """
    vol_df = pd.DataFrame(columns=['PWW', 'PWD', 'ALPHA', 'BETA'], index=[0])

    for col in vol_df.columns:
        series = params_df[col].values
        vol_df.at[0, col] = np.std(series) if len(series) > 1 else np.nan

    return vol_df