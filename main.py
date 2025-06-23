# main.py
from time_series import TimeSeries
from pgpar import calculate_params, calculate_window_params
import unittest
import os

def run_all_tests():
    """Run all unit tests in the tests directory."""
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


def main():
    """Main function for command-line usage."""
    # File path - using relative path for portability
    # You can modify this path or pass it as a command-line argument
    file_path = os.path.join("tests", "GrandJunction", "USW00023066_data.csv")

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        print("Please ensure the data file exists or update the file_path variable.")
        return 1

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
    print("Parameters saved to params_output.csv")

    # Run all tests from the tests directory
    print("\nRunning tests...")
    run_all_tests()
    return 0


if __name__ == '__main__':
    exit(main())
