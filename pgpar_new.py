import pandas as pd
import numpy as np

class PrecipGenPAR:
    def __init__(self, df):
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        self.df = df
        self.value_col = 'PRCP'
        self.params = pd.DataFrame(index=range(1, 13), columns=['Mean', 'SD', 'GammaMean'])

    def calculate_gamma_mean(self, precip_depths):
        # Filter out zero precipitation values (dry days)
        wet_days = precip_depths[precip_depths > 0]
        
        # Calculate XNW (number of wet days)
        XNW = len(wet_days)
        
        # Calculate SUM (sum of precipitation depths over the period)
        SUM = np.sum(wet_days)
        # Output the value
        print(f"SUM: {SUM}")
        
        # Calculate RBAR (average precipitation depth)
        RBAR = SUM / XNW
        
        # Calculate SUML (sum of the logarithms of the precipitation depths)
        SUML = np.sum(np.log(wet_days))
        
        # Calculate RLBAR (logarithmic average precipitation depth)
        RLBAR = SUML / XNW
        
        # Calculate Y (difference in logarithmic means)
        Y = np.log(RBAR) - RLBAR

        
        # Calculate ANUM (numerator for alpha calculation)
        ANUM = 8.898919 + 9.05995 * Y + 0.9775373 * Y * Y
        
        # Calculate ADOM (denominator for alpha calculation)
        ADOM = Y * (17.79728 + 11.968477 * Y + Y * Y)
        
        # Calculate ALPHA (shape parameter)
        ALPHA = min(ANUM / ADOM, 0.998)
        
        # Calculate BETA (scale parameter)
        BETA = RBAR / ALPHA
        
        # Calculate lambda (rate parameter)
        lambda_ = 1 / BETA
        
        # Calculate Mean of the Gamma distribution
        GammaMean = ALPHA / lambda_
        
        return GammaMean

    def calculate_monthly_stats(self):
        # Filter out rows where PRCP is zero
        filtered_df = self.df[self.df[self.value_col] != 0]
        
        # Group by month
        grouped = filtered_df.groupby(filtered_df.index.month)
        
        # Aggregate the grouped data and reset the index
        monthly_stats = grouped[self.value_col].agg(['mean', 'std']).reset_index()
        monthly_stats.rename(columns={'index': 'Month', 'mean': 'Mean', 'std': 'SD'}, inplace=True)
        
        # Calculate gamma mean for each month
        gamma_means = grouped[self.value_col].apply(self.calculate_gamma_mean).reset_index(drop=True)
        monthly_stats['GammaMean'] = gamma_means
        
        return monthly_stats