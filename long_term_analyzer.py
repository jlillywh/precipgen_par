import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

class LongTermAnalyzer:
    def __init__(self, precipitation_data):
        """
        Initialize the LongTermAnalyzer with precipitation data.
        
        :param precipitation_data: DataFrame with 'DATE' and precipitation column
        """
        self.df = precipitation_data.copy()
        self.df['DATE'] = pd.to_datetime(self.df['DATE'])
        self.df.set_index('DATE', inplace=True)
        self.precip_column = self.df.columns[0]  # Assume the first column is precipitation
        self.annual_precip = None
        self.annual_factors = None

    def calculate_annual_precipitation(self):
        """Calculate total annual precipitation."""
        self.annual_precip = self.df.resample('YE')[self.precip_column].sum()
        return self.annual_precip

    def calculate_annual_factors(self):
        """Calculate annual precipitation factors."""
        if self.annual_precip is None:
            self.calculate_annual_precipitation()
        long_term_mean = self.annual_precip.mean()
        self.annual_factors = self.annual_precip / long_term_mean
        return self.annual_factors

    def get_basic_statistics(self):
        if self.annual_factors is None:
            self.calculate_annual_factors()
        return {
            'mean': self.annual_factors.mean(),
            'std': self.annual_factors.std(),
            'min': self.annual_factors.min(),
            'max': self.annual_factors.max(),
            'skew': stats.skew(self.annual_factors),
            'kurtosis': stats.kurtosis(self.annual_factors)
        }

    def fit_distributions(self):
        if self.annual_factors is None:
            self.calculate_annual_factors()
        
        # Fit Gamma distribution
        gamma_params = stats.gamma.fit(self.annual_factors)
        gamma_kstest = stats.kstest(self.annual_factors, 'gamma', gamma_params)

        # Fit Log-Pearson Type III distribution
        log_data = np.log(self.annual_factors)
        pearson3_params = stats.pearson3.fit(log_data)
        pearson3_kstest = stats.kstest(log_data, 'pearson3', pearson3_params)

        return {
            'gamma': {
                'params': gamma_params,
                'ks_statistic': gamma_kstest.statistic,
                'p_value': gamma_kstest.pvalue
            },
            'log_pearson3': {
                'params': pearson3_params,
                'ks_statistic': pearson3_kstest.statistic,
                'p_value': pearson3_kstest.pvalue
            }
        }

    def plot_distribution_fit(self):
        if self.annual_factors is None:
            self.calculate_annual_factors()

        dist_fits = self.fit_distributions()

        plt.figure(figsize=(12, 6))
        
        # Histogram of data
        plt.hist(self.annual_factors, bins=20, density=True, alpha=0.7, color='skyblue', label='Data')

        # Fit lines
        x = np.linspace(self.annual_factors.min(), self.annual_factors.max(), 100)
        gamma_params = dist_fits['gamma']['params']
        gamma_pdf = stats.gamma.pdf(x, *gamma_params)
        plt.plot(x, gamma_pdf, 'r-', lw=2, label=f'Gamma (p={dist_fits["gamma"]["p_value"]:.4f})')

        log_pearson_params = dist_fits['log_pearson3']['params']
        log_pearson_pdf = stats.pearson3.pdf(np.log(x), *log_pearson_params)
        plt.plot(x, log_pearson_pdf / x, 'g-', lw=2, label=f'Log-Pearson III (p={dist_fits["log_pearson3"]["p_value"]:.4f})')

        plt.title("Distribution Fitting of Annual Precipitation Factors")
        plt.xlabel("Annual Factor")
        plt.ylabel("Density")
        plt.legend()
        plt.show()

    def analyze_trend(self):
        """Analyze the trend in annual factors."""
        if self.annual_factors is None:
            self.calculate_annual_factors()
        trend = stats.linregress(range(len(self.annual_factors)), self.annual_factors)
        return {
            'slope': trend.slope,
            'intercept': trend.intercept,
            'r_value': trend.rvalue,
            'p_value': trend.pvalue,
            'std_err': trend.stderr
        }

    def calculate_autocorrelation(self, max_lag=3):
        """Calculate autocorrelation of annual factors."""
        if self.annual_factors is None:
            self.calculate_annual_factors()
        return {f'lag_{i}': self.annual_factors.autocorr(lag=i) for i in range(1, max_lag+1)}

    def analyze_spells(self):
        """Analyze dry and wet spells."""
        if self.annual_factors is None:
            self.calculate_annual_factors()
        is_dry = self.annual_factors < 1.0
        dry_spells = (is_dry != is_dry.shift()).cumsum()[is_dry]
        wet_spells = (is_dry != is_dry.shift()).cumsum()[~is_dry]
        
        return {
            'dry_spell_lengths': dry_spells.value_counts().sort_index().to_dict(),
            'wet_spell_lengths': wet_spells.value_counts().sort_index().to_dict(),
            'max_dry_spell': dry_spells.value_counts().index.max(),
            'max_wet_spell': wet_spells.value_counts().index.max()
        }

    def get_extreme_values(self, lower_percentile=10, upper_percentile=90):
        """Get extreme values of annual factors."""
        if self.annual_factors is None:
            self.calculate_annual_factors()
        return {
            'lower_extreme': self.annual_factors.quantile(lower_percentile/100),
            'upper_extreme': self.annual_factors.quantile(upper_percentile/100)
        }

    def run_full_analysis(self):
        """Run all analyses and return a comprehensive report."""
        return {
            'basic_statistics': self.get_basic_statistics(),
            'normality_test': self.test_normality(),
            'trend_analysis': self.analyze_trend(),
            'autocorrelation': self.calculate_autocorrelation(),
            'spell_analysis': self.analyze_spells(),
            'extreme_values': self.get_extreme_values(),
            'historical_factors': self.calculate_annual_factors().to_dict()
        }

# Usage example:
# df = pd.read_csv('your_precipitation_data.csv')
# analyzer = LongTermAnalyzer(df)
# full_analysis = analyzer.run_full_analysis()
# print(full_analysis)

# Or use individual methods:
# annual_factors = analyzer.calculate_annual_factors()
# autocorrelation = analyzer.calculate_autocorrelation()
# spell_analysis = analyzer.analyze_spells()