# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
