# main.py
from time_series import TimeSeries
from pgpar import params, params_samples, volatility, reversion
from precip_stats import mean_monthly_totals
import os

# File path to the input CSV
file_path = r"C:\Users\jason\OneDrive\Documents\Dev\PrecipGenPAR\tests\USW00023066_data1.csv"

# Ensure the file exists before processing
if not os.path.exists(file_path):
    raise FileNotFoundError(f"The file '{file_path}' does not exist. Please check the path.")

# Step 1: Load and preprocess the time series
print("Loading and preprocessing the time series...")
precip_ts = TimeSeries()
precip_ts.load_and_preprocess(file_path)

# Step 2: Trim the data to complete years (optional, ensures clean data)
print("Trimming data to complete years...")
precip_ts.trim(1900, 2023)

# DEBUG: Print monthly mean totals
print("Calculating monthly mean totals...")
print(mean_monthly_totals(precip_ts.get_data()))

# Step 3: Calculate monthly parameters (12x4 DataFrame)
print("Calculating monthly parameters...")
monthly_params = params(precip_ts.get_data())
print("Monthly Parameters:\n", monthly_params)

# Step 4: Calculate annual parameters (e.g., 123x4 for 123 years of data)
print("Calculating annual parameters...")
annual_params_df = params_samples(precip_ts.get_data(), n_years=3)
print("Annual Parameters:\n", annual_params_df)

# Step 5: Compute volatility and reversion from annual parameters
print("Calculating volatility and reversion rates...")
volatility_dict = volatility(annual_params_df[['PWW', 'PWD', 'ALPHA', 'BETA']])
reversion_dict = reversion(annual_params_df[['PWW', 'PWD', 'ALPHA', 'BETA']])

# Step 6: Display results
print("\nVolatility:\n", volatility_dict)
print("\nReversion Rates:\n", reversion_dict)
