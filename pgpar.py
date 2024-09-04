import pandas as pd
import numpy as np
from scipy import stats
import warnings
pd.set_option('future.no_silent_downcasting', True)

class PrecipGenPAR:
    def __init__(self, df):
        # Ensure the input is a pandas DataFrame with 'DATE' and 'PRCP' columns
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        # The DataFrame must contain 'DATE' and 'PRCP' columns
        # 'DATE' should be in a format that can be converted to datetime
        # 'PRCP' should contain precipitation values
        self.df = df.copy()
        self.df['DATE'] = pd.to_datetime(self.df['DATE'])
        self.df.set_index('DATE', inplace=True)
        
        self.value_col = 'PRCP'
        self.params = pd.DataFrame(index=range(12))
        self.obs_stats = pd.DataFrame()

    def get_obs_stats(self):
        # Resample to monthly data
        monthly_data = self.df.resample('ME').sum()
        
        print("Monthly data columns:")
        print(monthly_data.columns)

        # Calculate statistics
        monthly_stats = monthly_data.groupby(monthly_data.index.strftime('%B')).agg(['min', 'max', 'mean'])
        
        print("Monthly stats columns after aggregation:")
        print(monthly_stats.columns)

        # Flatten the multi-level column names
        monthly_stats.columns = [f'{col[0]}_{col[1]}' for col in monthly_stats.columns]
        
        print("Monthly stats columns after flattening:")
        print(monthly_stats.columns)

        # Reset the index to turn the month names into a column
        monthly_stats.reset_index(inplace=True)
        
        print("Monthly stats columns after resetting index:")
        print(monthly_stats.columns)

        # Rename 'index' to 'Month'
        monthly_stats.rename(columns={'index': 'Month'}, inplace=True)

        # Ensure columns are in the correct order
        cols_to_use = ['Month', 'PRCP_min', 'PRCP_max', 'PRCP_mean']
        monthly_stats = monthly_stats[cols_to_use]
        
        print("Monthly stats columns after selecting PRCP columns:")
        print(monthly_stats.columns)

        # Sort the months in the correct order
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']
        monthly_stats['Month'] = pd.Categorical(monthly_stats['Month'], categories=month_order, ordered=True)
        monthly_stats = monthly_stats.sort_values('Month')
        
        # Replace month names with numbers 1-12
        monthly_stats['Month'] = range(1, len(monthly_stats) + 1)
        
        # Rename columns to match expected output
        monthly_stats.rename(columns={'PRCP_min': 'min', 'PRCP_max': 'max', 'PRCP_mean': 'mean'}, inplace=True)
        
        print("Final monthly stats columns:")
        print(monthly_stats.columns)

        # Calculate the longest runs
        longest_dry_run = self.longest_run_of_dry_days()
        longest_wet_run = self.longest_run_of_wet_days()

        # Print the results
        print(f"Longest run of dry days: {longest_dry_run}")
        print(f"Longest run of wet days: {longest_wet_run}")
        
        return monthly_stats
            
    def calculate_monthly_totals(self):
        monthly_totals = self.df.resample('ME').sum()
        monthly_totals.index = monthly_totals.index.strftime('%B')
        monthly_totals = monthly_totals.groupby(monthly_totals.index).mean()
        monthly_totals = monthly_totals.reindex(pd.Index(pd.date_range(start='2000-01-01', periods=12, freq='ME').strftime('%B')))
        monthly_totals.index.name = 'Month'
        return monthly_totals
    
    def calculate_monthly_distribution(self):
        monthly_totals = self.calculate_monthly_totals()[self.value_col]
        distribution = monthly_totals.groupby(monthly_totals.index).apply(lambda x: x.value_counts(normalize=True))
        distribution = distribution.reset_index()
        distribution.columns = ['Month', 'Total', 'Probability']
        return distribution

    def calculate_mean_daily(self):
        mean_daily = []
        for month in range(1, 13):
            monthly_data = self.df[self.df.index.month == month]
            wet_days = monthly_data[monthly_data[self.value_col] > 0.0]
            if not wet_days.empty:
                mean = wet_days[self.value_col].mean()
            else:
                mean = 0
            mean_daily.append(mean)
            #print(f"Month {month}: Mean = {mean}")
        self.params['Mean'] = pd.Series(mean_daily)

    def calculate_sd_daily(self):
        sd_daily = []
        for month in range(1, 13):
            monthly_data = self.df[self.df.index.month == month]
            wet_days = monthly_data[monthly_data[self.value_col] > 0.0]
            if not wet_days.empty:
                # Fit a gamma distribution to the wet day precipitation data
                shape, _, scale = stats.gamma.fit(wet_days[self.value_col], floc=0)
                # Calculate the standard deviation of the fitted gamma distribution
                sd = np.sqrt(shape * (scale ** 2))
            else:
                sd = 0
            sd_daily.append(sd)
        self.params['SD'] = pd.Series(sd_daily)

    def longest_run_of_dry_days(self):
        """
        Calculate the longest run of consecutive dry days (precipitation = 0).
        
        Returns:
            int: The length of the longest run of dry days.
        """
        # Identify dry days
        self.df['is_dry'] = self.df[self.value_col] == 0
        
        # Group by consecutive dry days
        self.df['dry_group'] = (self.df['is_dry'] != self.df['is_dry'].shift()).cumsum()
        
        # Calculate the length of each dry run
        dry_runs = self.df[self.df['is_dry']].groupby('dry_group').size()
        
        # Find the maximum length of dry runs
        max_dry_run = dry_runs.max() if not dry_runs.empty else 0
        
        return max_dry_run
    
    def longest_run_of_wet_days(self):
        """
        Calculate the longest run of consecutive wet days (precipitation > 0).
        
        Returns:
            int: The length of the longest run of wet days.
        """
        # Identify wet days
        self.df['is_wet'] = self.df[self.value_col] > 0
        
        # Group by consecutive wet days
        self.df['wet_group'] = (self.df['is_wet'] != self.df['is_wet'].shift()).cumsum()
        
        # Calculate the length of each wet run
        wet_runs = self.df[self.df['is_wet']].groupby('wet_group').size()
        
        # Find the maximum length of wet runs
        max_wet_run = wet_runs.max() if not wet_runs.empty else 0
        
        return max_wet_run

    def calculate_wet_dry_days(self):
        self.df['is_wet'] = self.df[self.value_col] > 0
        self.df['is_dry'] = self.df[self.value_col] == 0
        
        # Use a different approach to shift and fill values
        self.df['prev_day_wet'] = self.df['is_wet'].shift()
        self.df['prev_day_dry'] = self.df['is_dry'].shift()
        
        # Fill NaN values with False and ensure boolean type
        self.df['prev_day_wet'] = self.df['prev_day_wet'].fillna(False).astype(bool)
        self.df['prev_day_dry'] = self.df['prev_day_dry'].fillna(False).astype(bool)
        
    def calculate_probabilities(self):
        self.calculate_wet_dry_days()
        pww = []
        pwd = []
        for month in range(1, 13):
            monthly_data = self.df[self.df.index.month == month]
            wet_follows_wet = monthly_data[monthly_data['is_wet'] & monthly_data['prev_day_wet']].shape[0]
            wet_follows_dry = monthly_data[monthly_data['is_wet'] & monthly_data['prev_day_dry']].shape[0]
            total_wet_days = monthly_data[monthly_data['is_wet']].shape[0]
            total_dry_days = monthly_data[monthly_data['is_dry']].shape[0]
            
            if total_wet_days > 0:
                pww_value = wet_follows_wet / total_wet_days
            else:
                pww_value = 0
            
            if total_dry_days > 0:
                pwd_value = wet_follows_dry / total_dry_days
            else:
                pwd_value = 0
            
            pww.append(pww_value)
            pwd.append(pwd_value)
            #print(f"Month {month}: PWW = {pww_value}, PWD = {pwd_value}")
        
        self.params['PWW'] = pd.Series(pww)
        self.params['PWD'] = pd.Series(pwd)

    def calculate_parameters(self, data):
        params = pd.DataFrame(index=range(12), columns=['Mean', 'SD', 'PWW', 'PWD'])
        
        # Create a boolean series for wet days across the entire dataset
        is_wet_all = (data[self.value_col] > 0).astype(int)
        
        for month in range(1, 13):
            try:
                monthly_data = data[data.index.month == month]
                wet_days = monthly_data[monthly_data[self.value_col] > 0]
                
                if len(wet_days) > 0:
                    mean = wet_days[self.value_col].mean()
                    params.loc[month-1, 'Mean'] = mean
                    
                    if len(wet_days) > 1:
                        std = wet_days[self.value_col].std()
                        if std > 1e-8:  # Check if there's some variation
                            try:
                                with warnings.catch_warnings():
                                    warnings.filterwarnings('ignore')
                                    shape, _, scale = stats.gamma.fit(wet_days[self.value_col], floc=0)
                                params.loc[month-1, 'SD'] = np.sqrt(shape * (scale ** 2))
                            except ValueError:
                                # If gamma fitting fails, use sample standard deviation
                                params.loc[month-1, 'SD'] = std
                        else:
                            # If values are very similar, estimate SD as a small fraction of the mean
                            params.loc[month-1, 'SD'] = mean * 0.01  # You can adjust this factor as needed
                    else:
                        # If only one wet day, set SD to a small value
                        params.loc[month-1, 'SD'] = mean * 0.01  # Again, adjust as needed
                else:
                    # No wet days
                    params.loc[month-1, 'Mean'] = params.loc[month-1, 'SD'] = 0
            
                # Calculate PWW and PWD using is_wet_all
                is_wet_month = is_wet_all[data.index.month == month]

                # Get the last day of the previous month
                if month == 1:
                    prev_month = is_wet_all[data.index.month == 12]
                else:
                    prev_month = is_wet_all[data.index.month == month-1]

                if len(prev_month) > 0:
                    prev_month_last_day = prev_month.iloc[-1]
                else:
                    print(f"Warning: No data found for the previous month of month {month} in year {data.index.year[0]}")
                    if len(is_wet_month) > 0:
                        prev_month_last_day = is_wet_month.iloc[0]
                        print(f"Using the first day of the current month ({month}) as the previous day")
                    else:
                        print(f"Warning: No data found for the current month {month} in year {data.index.year[0]}")
                        prev_month_last_day = 0  # or another appropriate default value
                
                # Calculate transitions
                transitions = pd.concat([pd.Series([prev_month_last_day], index=[is_wet_month.index[0] - pd.Timedelta(days=1)]), is_wet_month])
                
                wet_to_wet = ((transitions == 1) & (transitions.shift() == 1)).sum()
                wet_to_dry = ((transitions == 0) & (transitions.shift() == 1)).sum()
                dry_to_wet = ((transitions == 1) & (transitions.shift() == 0)).sum()
                dry_to_dry = ((transitions == 0) & (transitions.shift() == 0)).sum()
                
                # Calculate probabilities
                params.loc[month-1, 'PWW'] = wet_to_wet / (wet_to_wet + wet_to_dry) if (wet_to_wet + wet_to_dry) > 0 else 0
                params.loc[month-1, 'PWD'] = dry_to_wet / (dry_to_wet + dry_to_dry) if (dry_to_wet + dry_to_dry) > 0 else 0
            except Exception as e:
                print(f"Error processing month {month} in year {data.index.year[0]}: {str(e)}")
                print(f"Data for this month: {monthly_data}")

        # Add a 'Month' column that starts from 1
        params['Month'] = range(1, 13)
        
        # Reorder columns to put 'Month' first
        params = params[['Month', 'Mean', 'SD', 'PWW', 'PWD']]

        return params

    def get_parameters(self, n_years=5):
        # Calculate annual precipitation using 'YE' instead of 'Y'
        annual_precip = self.df.resample('YE')[self.value_col].sum()
        
        # Identify dry and wet years
        sorted_years = annual_precip.sort_values()
        dry_years = sorted_years.head(n_years).index.year
        wet_years = sorted_years.tail(n_years).index.year
        
        # Calculate parameters for each group
        dry_params = self.calculate_parameters(self.df[self.df.index.year.isin(dry_years)])
        wet_params = self.calculate_parameters(self.df[self.df.index.year.isin(wet_years)])
        all_params = self.calculate_parameters(self.df)  # Parameters for all years
        
        # Format the parameter DataFrames to match the CSV format
        def format_params(params):
            params = params.round(6)  # Round to 6 decimal places
            return params
        
        dry_params = format_params(dry_params)
        wet_params = format_params(wet_params)
        all_params = format_params(all_params)
        
        return {
            'dry': dry_params,
            'wet': wet_params,
            'all': all_params
        }
    
    def calculate_yearly_pww_pwd(self):
        yearly_params = []
        for i, year in enumerate(self.df.index.year.unique()):
            if i < 2:  # Only print for the first two years
                print(f"Processing year: {year}")
                year_data = self.df[self.df.index.year == year]
                print(f"Data points in year: {len(year_data)}")
                params = self.calculate_parameters(year_data)
                print(f"Parameters for year {year}:")
                print(params)
                print("-" * 50)
            else:
                params = self.calculate_parameters(self.df[self.df.index.year == year])
            yearly_params.append(params)
        return pd.concat(yearly_params, keys=self.df.index.year.unique(), names=['Year', 'Month'])

    def calculate_pww_pwd_correlation(self):
        yearly_params = self.calculate_yearly_pww_pwd()
        correlations = []
        
        for year in yearly_params.index.get_level_values('Year').unique():
            try:
                year_params = yearly_params.loc[year]
                correlation = year_params['PWW'].corr(year_params['PWD'])
                correlations.append(correlation)
            except Exception as e:
                print(f"Error calculating correlation for year {year}: {str(e)}")
                print(f"Year parameters: {year_params}")
        
        return np.mean(correlations)
    
    def calculate_pww_mean_correlation(self):
        yearly_params = self.calculate_yearly_pww_pwd()
        correlations = []
        
        for year in yearly_params.index.get_level_values('Year').unique():
            year_params = yearly_params.loc[year]
            correlation = year_params['PWW'].corr(year_params['Mean'])
            correlations.append(correlation)
        
        return np.mean(correlations)

    def calculate_autocorrelation_ann_precip(self):
        annual_totals = self.df.resample('YE')[self.value_col].sum().values
        
        def autocorr(x, lag):
            return np.corrcoef(np.array([x[:-lag], x[lag:]]))[0,1]
        
        max_lag = min(10, len(annual_totals) // 2)  # Use up to 10 years or half the data length
        autocorrelations = [autocorr(annual_totals, lag) for lag in range(1, max_lag + 1)]
        
        optimal_lag = np.argmax(np.abs(autocorrelations)) + 1
        autocorrelation = autocorrelations[optimal_lag - 1]
        
        return autocorrelation, optimal_lag