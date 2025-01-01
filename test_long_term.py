import pandas as pd
from parse_ghcn import parse_ghcn_data
from long_term_analyzer import LongTermAnalyzer
import matplotlib.pyplot as plt

def main():
    # File path
    file_path = r"C:\Users\jason\OneDrive\Documents\Dev\PrecipGenPAR\tests\3703955_SaltLakeCity.csv"

    # Read the CSV file
    with open(file_path, 'r') as file:
        raw_data = file.read()

    # Parse the GHCN data
    df = parse_ghcn_data(raw_data)

    if df is not None:
        # Initialize the LongTermAnalyzer with the parsed data
        analyzer = LongTermAnalyzer(df)

        # Run the full analysis
        analysis_results = analyzer.run_full_analysis()

        # Print the results
        print("Salt Lake City Precipitation Analysis Results:")
        print("=============================================")
        print(f"Basic Statistics: {analysis_results['basic_statistics']}")
        print(f"Trend Analysis: {analysis_results['trend_analysis']}")
        print(f"Autocorrelation: {analysis_results['autocorrelation']}")
        print(f"Spell Analysis: {analysis_results['spell_analysis']}")
        print(f"Extreme Values: {analysis_results['extreme_values']}")

        # Plot the distribution fit
        analyzer.plot_distribution_fit()
        plt.title("Salt Lake City Annual Precipitation Factors Distribution")
        plt.savefig("SaltLakeCity_distribution_fit.png")
        print("Distribution fit plot saved as 'SaltLakeCity_distribution_fit.png'")

        # Plot annual precipitation over time
        annual_precip = analyzer.calculate_annual_precipitation()
        plt.figure(figsize=(12, 6))
        annual_precip.plot()
        plt.title("Salt Lake City Annual Precipitation")
        plt.xlabel("Year")
        plt.ylabel("Precipitation")
        plt.savefig("SaltLakeCity_annual_precipitation.png")
        print("Annual precipitation plot saved as 'SaltLakeCity_annual_precipitation.png'")

    else:
        print("Failed to parse the GHCN data. Please check the file and try again.")

if __name__ == "__main__":
    main()