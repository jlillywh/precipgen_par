# precip_stats.py
import pandas as pd

def mean_monthly_totals(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the average monthly totals for daily precipitation.

    This function sums the daily precipitation for each month to get monthly totals
    and then averages these monthly totals across all years.

    Parameters:
    ----------
    data : pd.DataFrame
        A DataFrame with 'DATE' as the index and 'VALUE' as the precipitation column.

    Returns:
    -------
    pd.DataFrame
        A DataFrame with two columns:
        - 'Month': 1 (January), 2 (February), ..., 12 (December)
        - 'Average Monthly Total': The average precipitation total for each month across all years.
    """
    # Step 1: Group by year and month, and sum daily values to get monthly totals
    monthly_totals = data.groupby([data.index.year, data.index.month])['VALUE'].sum()

    # Step 2: Group by month and calculate the mean of monthly totals across all years
    average_monthly_totals = monthly_totals.groupby(level=1).mean()

    # Step 3: Convert the result to a DataFrame
    result_df = average_monthly_totals.reset_index()
    result_df.columns = ['Month', 'Average Monthly Total']

    return result_df