import pandas as pd
import numpy as np
from scipy.stats import linregress

def calculate_params(precip_ts):
    """
    Calculate pww, pwd, alpha, and beta parameters for each month from a historical precipitation time series.
    
    Parameters:
    precip_ts : pd.DataFrame
        Time series DataFrame with 'DATE' as the index and 'PRCP' as the precipitation column.
        
    Returns:
    params : pd.DataFrame
        DataFrame of calculated parameters for each month.
    """
    
    # Initialize counters and arrays for monthly statistics
    sum_precip = np.zeros(12)
    sum_log_precip = np.zeros(12)
    wet_day_count = np.zeros(12)
    nww, nwd, ndw, ndd = np.zeros(12), np.zeros(12), np.zeros(12), np.zeros(12)

    wet_yesterday = False  # Track if the previous day was wet

    # Iterate over the time series to calculate Pww, Pwd, etc.
    for t in range(1, len(precip_ts)):
        current_date = precip_ts.index[t]
        month = current_date.month - 1  # Zero-based index for months
        precipitation = precip_ts.loc[current_date, 'PRCP']

        wet_today = precipitation > 0.0

        if wet_today:
            wet_day_count[month] += 1
            sum_precip[month] += precipitation
            sum_log_precip[month] += np.log(precipitation)

        # Track transitions between wet and dry days
        if wet_yesterday and wet_today:
            nww[month] += 1
        elif wet_today and not wet_yesterday:
            nwd[month] += 1
        elif not wet_today and wet_yesterday:
            ndw[month] += 1
        else:
            ndd[month] += 1

        wet_yesterday = wet_today

    # Initialize parameters
    pww, pwd, alpha, beta, rbar, rlbar, y, anum, adom = (
        np.zeros(12) for _ in range(9)
    )

    for m in range(12):
        # Calculate probabilities Pww and Pwd
        if wet_day_count[m] >= 3:  # Only if there is enough data
         
            # Use intermediate variables as per original code
            xnww, xxnw, xnwd, xnd, xnw = nww[m], nww[m] + ndw[m], nwd[m], ndd[m] + nwd[m], wet_day_count[m]

            pww[m] = xnww / xxnw if xxnw > 0 else 0.0
            pwd[m] = xnwd / xnd if xnd > 0 else 0.0
            
            # Monthly mean precipitation and mean log-precipitation
            rbar[m] = sum_precip[m] / xnw if xnw > 0 else 0.0
            rlbar[m] = sum_log_precip[m] / xnw if xnw > 0 else 0.0
            
            # Alpha and Beta calculation with y, anum, and adom
            if rbar[m] > 0:
                y[m] = np.log(rbar[m]) - rlbar[m]
            else:
                y[m] = 0.0

            anum[m] = 8.898919 + 9.05995 * y[m] + 0.9775373 * y[m] * y[m]
            adom[m] = y[m] * (17.79728 + 11.968477 * y[m] + y[m] * y[m])
            alpha[m] = min(0 if adom[m] <= 0 else anum[m] / adom[m], 0.998)
            beta[m] = rbar[m] / alpha[m] if alpha[m] > 0 else 0.0

    # Ensure all parameters are positive, and set defaults if necessary
    pww = np.where(pww <= 0, 0.001, pww)
    pwd = np.where(pwd <= 0, 0.001, pwd)
    alpha = np.where(alpha <= 0, 0.001, alpha)
    beta = np.where(beta <= 0, 0.001, beta)

    # Compile the parameters into a DataFrame for output
    params = pd.DataFrame({
        'PWW': pww, 'PWD': pwd, 'ALPHA': alpha, 'BETA': beta
    }, index=range(1, 13))

    return params

# Helper function to calculate reversion rate from a list of samples
def calc_reversion_rate(samples):
    """
    Estimate the AR(1) coefficient b from X_{t+1} = a + b*X_t +eps
    and define reversion rate = 1 - b
    """

    if len(samples) < 2:
        return np.nan
    x_t = samples[:-1]
    x_t1 = samples[1:]
    slope, intercept, r_value, p_value, std_err = linregress(x_t, x_t1)
    return 1 - slope # simple definition of "mean reversion" speed

def calculate_window_params(precip_ts, n_years=2):
    """
    Slide an N-year window (where N = 1, 2, 3, or 4, etc.) over the entire time series,
    computing (pww, pwd, alpha, beta) for each window. Shift by 1 year each time, stopping
    when there aren't N full years left in the data.

    Parameters
    ----------
    precip_ts : pd.DataFrame
        A DataFrame with:
          - A DatetimeIndex (e.g., named 'DATE')
          - A column 'PRCP' for daily precipitation
    n_years : int
        The number of years in each sliding window. Default is 2.

    Returns
    -------
    pd.DataFrame
        Columns: [year_start, pww, pwd, alpha, beta]
        Each row corresponds to one N-year window.
    """

    pww_samples = []
    pwd_samples = []
    alpha_samples = []
    beta_samples = []

    # Figure out the earliest and latest years in the data
    start_year = precip_ts.index.year.min()
    end_year = precip_ts.index.year.max()

    # We'll do an N-year window: from y (inclusive) to y + n_years (exclusive) 
    # in terms of calendar years. 
    # Example: if y = 1900 and n_years=2, we cover 1900-01-01 up to but not including 1902-01-01.

    # Stop when the start year + n_years would exceed the end of your data.
    # So we iterate until `end_year - n_years + 1`.
    # Initialize counters for aggregated statistics
    for year in range(start_year, end_year - n_years + 1):
        # Window start (inclusive): y-01-01
        # Window end (exclusive): (y + n_years)-01-01
        win_start_date = f"{year}-01-01"
        win_end_date = f"{year + n_years}-01-01"

        # Slice out just the N-year chuch of time series
        window_df = precip_ts.loc[win_start_date:win_end_date]

        # If there's no data in the window, break out of the loop
        if window_df.empty:
            break

        # Initialize counters
        sum_precip = 0.0
        sum_log_precip = 0.0
        wet_day_count = 0
        nww, nwd, ndw, ndd = 0, 0, 0, 0

        wet_yesterday = False  # Track if the previous day was wet

        # Iterate over the time series to calculate aggregated statistics
        for t in range(1, len(window_df)):
            precipitation = window_df['PRCP'].iloc[t]
            wet_today = precipitation > 0.0

            # Count if wet days and sum up precipitation
            if wet_today:
                wet_day_count += 1
                sum_precip += precipitation
                sum_log_precip += np.log(precipitation)

            # Track transitions between wet and dry days
            if wet_yesterday and wet_today:
                nww += 1
            elif wet_today and not wet_yesterday:
                nwd += 1
            elif not wet_today and wet_yesterday:
                ndw += 1
            else:
                ndd += 1

            wet_yesterday = wet_today

        # Compute the overall pww and pwd
        # If denominator is zero, set to 0.001 to avoid division by zero

        ww_plus_dw = nww + ndw
        wd_plus_dd = nwd + ndd

        if ww_plus_dw > 0:
            pww = nww / ww_plus_dw
        else:
            pww = 0.001
        if wd_plus_dd > 0:
            pwd = nwd / wd_plus_dd
        else:
            pwd = 0.001

        # Calculate rbar and rlbar from aggregated sums
        # Make sure we have at least some wet days to avoid division by zero
        if wet_day_count > 0:
            rbar = sum_precip / wet_day_count
            rlbar = sum_log_precip / wet_day_count
        else:
            # In case there are no wet days, set some defaults
            rbar, rlbar = 0.0, 0.0

        # Calculate alpha and beta
        if rbar > 0:
            log_term = np.log(rbar) - rlbar
        else:
            log_term = 0.0

        anum = 8.898919 + 9.05995 * log_term + 0.9775373 * (log_term**2)
        adom = log_term * (17.79728 + 11.968477 * log_term + (log_term**2))

        if adom > 0:
            alpha = min(anum / adom, 0.998)
        else:
            alpha = 0.001

        if alpha > 0:
            beta = rbar / alpha
        else:
            beta = 0.001

        # Ensure all are zero or positive
        if pww <= 0: pww = 0.001
        if pwd <= 0: pwd = 0.001
        if alpha <= 0: alpha = 0.001
        if beta <= 0: beta = 0.001

        # Append samples to the list
        pww_samples.append(pww)
        pwd_samples.append(pwd)
        alpha_samples.append(alpha)
        beta_samples.append(beta)
    
    pww_array = np.array(pww_samples)
    pwd_array = np.array(pwd_samples)
    alpha_array = np.array(alpha_samples)
    beta_array = np.array(beta_samples)

    # Compute volatility (std. dev.)
    pww_vol = pww_array.std() if len(pww_array) > 1 else np.nan
    pwd_vol = pwd_array.std() if len(pwd_array) > 1 else np.nan
    alpha_vol = alpha_array.std() if len(alpha_array) > 1 else np.nan
    beta_vol = beta_array.std() if len(beta_array) > 1 else np.nan

    # Compute reversion rate
    pww_rev = calc_reversion_rate(pww_array)
    pwd_rev = calc_reversion_rate(pwd_array)
    alpha_rev = calc_reversion_rate(alpha_array)
    beta_rev = calc_reversion_rate(beta_array)

    # Return just these 8 values (no need to see the raw samples)
    volatilities = [pww_vol, pwd_vol, alpha_vol, beta_vol]
    reversion_rates = [pww_rev, pwd_rev, alpha_rev, beta_rev]
    return volatilities, reversion_rates