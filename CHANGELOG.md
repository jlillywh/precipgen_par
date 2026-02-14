# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-02-13

### Changed
- Replaced radio button station selector with dropdown in Search panel for cleaner UI
- Search results now show station year ranges in dropdown format (GHCNXXX - Name (start-end))
- Limited search results display to 100 stations maximum, ordered by station ID
- Separated data download from parameter calculation (download-only workflow)
- Enhanced error messages with actionable troubleshooting guidance
- Improved CSV parsing with automatic GHCN metadata row detection

### Fixed
- Fixed GHCN CSV parsing errors with metadata rows at file start
- Removed artificial 0.998 cap on gamma distribution alpha parameter for statistically correct precipitation modeling

## [1.2.3] - 2026-02-13

### Fixed
- Removed artificial 0.998 cap on gamma distribution alpha parameter for statistically correct precipitation modeling

## [1.2.2] - 2026-02-12

### Fixed
- Fixed blank parameters display after CSV upload by ensuring precipitation data is stored in app state
- Fixed threading issue where parameter calculations triggered UI updates from background threads
- Fixed DataFrame boolean evaluation error in data quality display
- Compacted parameters table layout with reduced padding and font sizes for better screen fit

### Changed
- Moved `set_historical_params()` calls to main thread to ensure safe observer notifications
- Updated `calculate_historical_parameters()` to return params without setting app state (caller responsibility)
- Added comprehensive debug logging to parameters panel for troubleshooting

## [1.2.1] - 2026-02-12

### Added
- Desktop GUI application with tkinter interface
- Executable packaging support with PyInstaller
- Code signing scripts and documentation for Windows executables
- Comprehensive packaging and deployment documentation
- Calibration verification tests and manual testing scripts
- Logging configuration module for better debugging

### Changed
- Enhanced project structure with desktop application components
- Improved build and deployment workflows
- Updated documentation with executable testing and certificate guides

## [1.2.0] - 2026-02-12

### Changed
- Standardized all Python imports to use proper package structure (`from precipgen.x import y`)
- Updated test files to use full package paths instead of sys.path manipulation
- Improved code maintainability and IDE support through explicit import statements
- Enhanced project organization following Python packaging best practices

## [1.1.0] - 2026-02-11

### Changed
- Cleaned up README.md: removed emojis, made pythonic and efficient
- Merged CLI_README.md into main README.md for consolidated documentation
- Updated QUICK_REFERENCE.md with accurate command syntax and examples
- Replaced all Unicode emoji characters in cli.py with ASCII alternatives for Windows compatibility
- Improved documentation organization and clarity

### Fixed
- Fixed Unicode encoding errors in cli.py that caused crashes on Windows systems
- Corrected command references in documentation (removed non-existent `random-walk` command)
- Fixed help command output on Windows (UnicodeEncodeError resolved)

### Removed
- Removed 24 temporary and duplicate files for cleaner project structure:
  - CLI_README.md (merged into README.md)
  - Demo files: demo_pgpar_wave.py, demo_data_filling.py
  - Test files from root: test_*.py (6 files)
  - Duplicate versions: pgpar_new.py, time_series_fixed.py
  - Markdown summaries: DATA_FILLING_SUMMARY.md, PROJECT_AWARE_OUTPUT_SUMMARY.md, WAVE_ANALYSIS_IMPLEMENTATION.md
  - Development notes: TODO.txt
  - Log files: ghcn_stations.log
  - Corrupted test files: tests/test_comprehensive_fixed.py and .broken version
  - Empty folder: GHCNpy/
  - Standalone scripts: wave_functions.py

### Improved
- All 45 tests passing after cleanup
- Better cross-platform compatibility (Windows, Mac, Linux)
- More maintainable codebase with reduced file count
- Clearer, more professional documentation

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
