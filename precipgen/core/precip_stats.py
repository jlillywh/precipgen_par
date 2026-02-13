import pandas as pd
import numpy as np

class PrecipValidator:
    def __init__(self, df):
        self.df = df.copy()
        self.df['DATE'] = pd.to_datetime(self.df['DATE'])
        self.df.set_index('DATE', inplace=True)
        self.value_col = 'PRCP'

    def get_obs_stats(self):
        monthly_data = self.df.resample('ME').sum()
        monthly_stats = monthly_data.groupby(monthly_data.index.strftime('%B')).agg(['min', 'max', 'mean'])
        monthly_stats.columns = [f'{col[0]}_{col[1]}' for col in monthly_stats.columns]
        monthly_stats.reset_index(inplace=True)
        monthly_stats.rename(columns={'index': 'Month'}, inplace=True)
        
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']
        monthly_stats['Month'] = pd.Categorical(monthly_stats['Month'], categories=month_order, ordered=True)
        monthly_stats = monthly_stats.sort_values('Month')
        monthly_stats['Month'] = range(1, len(monthly_stats) + 1)
        monthly_stats.rename(columns={'PRCP_min': 'min', 'PRCP_max': 'max', 'PRCP_mean': 'mean'}, inplace=True)
        
        return monthly_stats[['Month', 'min', 'max', 'mean']]

    def longest_run_of_dry_days(self):
        self.df['is_dry'] = self.df[self.value_col] == 0
        self.df['dry_group'] = (self.df['is_dry'] != self.df['is_dry'].shift()).cumsum()
        dry_runs = self.df[self.df['is_dry']].groupby('dry_group').size()
        return dry_runs.max() if not dry_runs.empty else 0
    
    def longest_run_of_wet_days(self):
        self.df['is_wet'] = self.df[self.value_col] > 0
        self.df['wet_group'] = (self.df['is_wet'] != self.df['is_wet'].shift()).cumsum()
        wet_runs = self.df[self.df['is_wet']].groupby('wet_group').size()
        return wet_runs.max() if not wet_runs.empty else 0
    
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

    def calculate_autocorrelation_ann_precip(self):
        annual_totals = self.df.resample('YE')[self.value_col].sum().values
        
        def autocorr(x, lag):
            return np.corrcoef(np.array([x[:-lag], x[lag:]]))[0,1]
        
        max_lag = min(10, len(annual_totals) // 2)
        autocorrelations = [autocorr(annual_totals, lag) for lag in range(1, max_lag + 1)]
        
        optimal_lag = np.argmax(np.abs(autocorrelations)) + 1
        autocorrelation = autocorrelations[optimal_lag - 1]
        
        return autocorrelation, optimal_lag
