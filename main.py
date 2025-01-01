# main.py
from time_series import TimeSeries
from pgpar import calculate_params, calculate_window_params
import unittest

# File path
file_path = r"C:\Users\jason\OneDrive\Documents\Dev\PrecipGenPAR\tests\USW00023066_data.csv"

# Load and preprocess the CSV file
timeseries = TimeSeries()
timeseries.load_and_preprocess(file_path)
timeseries.trim(1900, 2023)

# Calculate parameters
params = calculate_params(timeseries.get_data())

print(f"params:\n {params}")

stats = calculate_window_params(timeseries.get_data(), 2)
print(stats)

# Save the parameters to a CSV file
params.to_csv('params_output.csv', index=False)

# Run all tests from the tests directory
def run_all_tests():
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    print("\nSummary of test results:")
    print(f"Ran {result.testsRun} test(s)")
    if result.wasSuccessful():
        print("All tests passed!")
    else:
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        for test, err in result.failures + result.errors:
            print(f"Test: {test}")
            print(f"Error: {err}")

if __name__ == '__main__':
    run_all_tests()
