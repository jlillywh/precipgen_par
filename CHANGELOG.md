# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-22

### Added
- Initial release of PrecipGenPAR parameter generator
- Core functionality for calculating precipitation parameters from time series data
- Support for Markov chain parameters (pww, pwd) and gamma distribution parameters (alpha, beta)
- TimeSeries class for loading and preprocessing precipitation data
- Comprehensive test suite with unit tests
- CLI interface via main.py
- Support for windowed parameter calculations
- Documentation and README with usage examples

### Features
- Load precipitation data from CSV files
- Calculate monthly precipitation parameters
- Trim time series data to specified date ranges
- Generate window-based parameter statistics
- Export results to CSV format
- Robust error handling and logging
- Comprehensive test coverage

### Dependencies
- pandas >= 1.5.0
- numpy >= 1.21.0
- scipy >= 1.9.0
- requests >= 2.28.0
