# Design Document: Project Organization v1.2.0

## Overview

This design addresses the standardization of Python imports across the PrecipGen project and preparation for the v1.2.0 release. The primary goal is to ensure all imports use proper package structure (`from precipgen.x import y`) rather than sys.path manipulation or bare imports. This improves code maintainability, IDE support, and follows Python best practices.

The work involves:
1. Updating test files to use proper package imports
2. Running the test suite to validate changes
3. Updating version metadata and CHANGELOG.md
4. Ensuring Windows compatibility throughout

## Architecture

### Current Package Structure

```
precipgen/
├── __init__.py          # Package root with version and core exports
├── cli/                 # Command-line interface
│   └── __init__.py
├── core/                # Analysis algorithms and statistics
│   ├── __init__.py
│   ├── time_series.py
│   ├── pgpar.py
│   ├── pgpar_ext.py
│   ├── pgpar_wave.py
│   ├── random_walk_params.py
│   ├── precip_stats.py
│   └── long_term_analyzer.py
├── data/                # Data acquisition and management
│   ├── __init__.py
│   ├── csv_loader.py
│   ├── ghcn_data.py
│   ├── data_filler.py
│   ├── gap_analyzer.py
│   ├── find_stations.py
│   └── find_ghcn_stations.py
└── web/                 # Streamlit web interface
    ├── __init__.py
    └── streamlit_app.py
```

### Import Pattern Changes

**Before (Incorrect):**
```python
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from time_series import TimeSeries
from pgpar import calculate_params
```

**After (Correct):**
```python
from precipgen.core.time_series import TimeSeries
from precipgen.core.pgpar import calculate_params
```

This change:
- Eliminates sys.path manipulation
- Makes imports explicit and traceable
- Improves IDE autocomplete and navigation
- Follows Python packaging best practices

## Components and Interfaces

### Test Files to Update

Three test files require import updates:

1. **tests/test_pgpar.py**
   - Current imports: `from time_series import TimeSeries`, `from pgpar import calculate_params`
   - Updated imports: `from precipgen.core.time_series import TimeSeries`, `from precipgen.core.pgpar import calculate_params`

2. **tests/test_comprehensive_final.py**
   - Current imports: Multiple bare imports from core and data modules
   - Updated imports: All imports prefixed with `precipgen.core` or `precipgen.data`

3. **tests/test_comprehensive.py**
   - Current imports: Same as test_comprehensive_final.py
   - Updated imports: All imports prefixed with `precipgen.core` or `precipgen.data`

### Version Metadata Files

Two files contain version information:

1. **precipgen/__init__.py**
   - Contains `__version__ = "1.1.0"`
   - Update to `__version__ = "1.2.0"`

2. **setup.py**
   - Contains version parameter in setup() call
   - Update to version="1.2.0"

### Documentation Files

1. **CHANGELOG.md**
   - Add new [1.2.0] section with current date
   - Document import structure improvements
   - Follow Keep a Changelog format

## Data Models

No data model changes are required. This is a refactoring task that maintains all existing APIs and data structures.


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Import Structure Compliance

*For any* Python file in the project that imports from precipgen modules, all import statements SHALL use the full package path (e.g., `from precipgen.core.time_series import TimeSeries`) and SHALL NOT use sys.path manipulation or bare module imports.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: CHANGELOG Format Consistency

*For any* version entry in CHANGELOG.md, the entry SHALL follow the Keep a Changelog format with proper version header, date, and categorized subsections (Added, Changed, Fixed, etc.).

**Validates: Requirements 3.4**

### Property 3: Version Consistency

*For all* files containing version metadata (precipgen/__init__.py, setup.py), the version string SHALL be identical and SHALL match the target release version.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 4: Package Separation Maintenance

*For any* Python module in the precipgen package, the module SHALL reside in exactly one of the four subpackages (cli, core, data, web) according to its functional responsibility, with no cross-contamination of concerns.

**Validates: Requirements 5.2**

### Property 5: API Signature Preservation

*For any* public function or class in the precipgen package, the signature (parameters, return types, and behavior) SHALL remain unchanged after import refactoring.

**Validates: Requirements 5.4**

### Property 6: End-to-End Workflow Completeness

*For any* city with available GHCN stations, the complete workflow (search → select station with >75 years data → download → analyze) SHALL complete successfully and produce valid statistical results with wet day probability between 0 and 1.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.6**

## Error Handling

### Import Errors

If import statements are incorrect after refactoring:
- Python will raise `ImportError` or `ModuleNotFoundError`
- Test suite will fail immediately
- Error messages will indicate which module cannot be imported

### Test Failures

If functionality breaks during refactoring:
- Test suite will report specific test failures
- Error messages will show expected vs actual behavior
- Rollback changes and investigate root cause

### Version Inconsistencies

If version strings don't match across files:
- Manual verification will catch discrepancies
- Automated checks can scan for version patterns
- Update all version references before release

## Integration Test Design

### End-to-End Workflow Test

The integration test validates the complete practitioner workflow from station search through data analysis. This test fills a critical gap in the current test suite, which focuses on unit tests for core analysis modules but doesn't test the data acquisition modules (find_stations, ghcn_data).

### Test Workflow

The integration test follows this sequence:

1. **Station Search**: Use `find_stations.search_by_city()` to search for stations by city name
   - Example: Search for "Seattle" or "Portland"
   - Returns list of station metadata including station ID, name, location, and data availability

2. **Dataset Selection**: Iterate through search results to find a suitable dataset
   - Check each station's data availability
   - Look for stations with more than 75 years of daily precipitation data
   - Accept datasets with missing records (all real-world datasets have gaps)
   - Stop at first suitable station found

3. **Data Download**: Use `ghcn_data.download_station_data()` to fetch data from NOAA
   - Download daily precipitation data for the selected station
   - Handle network errors gracefully
   - Validate downloaded data format

4. **Data Analysis**: Perform basic analysis on downloaded data
   - Load data into TimeSeries object
   - Calculate basic statistics (mean, variance, wet day probability)
   - Optionally calculate PrecipGen parameters
   - Validate that analysis completes without errors

### Test Implementation Approach

**Test Location**: `tests/test_integration_workflow.py`

**Test Structure**:
```python
def test_end_to_end_workflow():
    # 1. Search for stations
    city = "Seattle"
    stations = search_by_city(city)
    assert len(stations) > 0, f"No stations found for {city}"
    
    # 2. Find suitable dataset
    suitable_station = None
    for station in stations:
        if station.years_of_data > 75:
            suitable_station = station
            break
    
    assert suitable_station is not None, "No station with >75 years found"
    
    # 3. Download data
    data = download_station_data(suitable_station.id)
    assert data is not None, "Failed to download data"
    assert len(data) > 0, "Downloaded data is empty"
    
    # 4. Analyze data
    ts = TimeSeries(data)
    stats = ts.calculate_basic_stats()
    assert stats is not None, "Failed to calculate statistics"
    assert 0 <= stats.wet_day_prob <= 1, "Invalid wet day probability"
```

### Error Handling

The integration test should handle common failure modes:

- **No stations found**: Skip test or use fallback city
- **Network errors**: Retry with exponential backoff or skip test
- **Insufficient data**: Continue searching for another station
- **Analysis errors**: Report detailed error information

### Test Configuration

- **Timeout**: Set reasonable timeout (e.g., 60 seconds) for network operations
- **Retry logic**: Retry failed network requests up to 3 times
- **Test data**: Use real NOAA GHCN database (not mocked) for true integration testing
- **Cleanup**: No cleanup needed (read-only operations)

### Benefits

This integration test provides:

1. **Coverage for untested modules**: Tests find_stations and ghcn_data modules
2. **Workflow validation**: Ensures the complete practitioner workflow works
3. **Real-world testing**: Uses actual NOAA data, catching API changes
4. **Confidence**: Validates that all components work together correctly

## Testing Strategy

### Dual Testing Approach

This project uses both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Both approaches are complementary and necessary for comprehensive coverage.

### Unit Testing

The existing test suite provides comprehensive unit test coverage:

1. **tests/test_pgpar.py**: Tests core parameter calculation functionality
   - Validates parameter accuracy against known values
   - Tests parameter bounds (probabilities 0-1, positive gamma parameters)
   - Ensures monthly completeness (12 months of data)

2. **tests/test_comprehensive_final.py**: Comprehensive integration tests
   - TimeSeries loading and preprocessing
   - Parameter calculations (basic, windowed, extended)
   - Gap analysis functionality
   - Data validation and error handling

3. **tests/test_comprehensive.py**: Additional comprehensive tests
   - Duplicate coverage for robustness
   - Edge case validation

### Testing After Import Changes

After updating imports, run the complete test suite:

**Windows Command:**
```cmd
python -m pytest tests/ -v
```

Or using unittest:
```cmd
python -m unittest discover tests -v
```

**Expected Outcome:**
- All existing tests should pass
- No new test failures introduced
- Test count remains the same (45 tests as of v1.1.0)

### Property-Based Testing

For this refactoring task, property-based testing is less applicable since we're not implementing new algorithms. However, the properties defined above can be validated through:

1. **Static Analysis**: Scan Python files for import patterns
2. **Automated Checks**: Scripts to verify version consistency and CHANGELOG format
3. **Test Suite Execution**: Validates that functionality is preserved (Property 5)

### Manual Validation Checklist

Before release, manually verify:
- [ ] All test files use proper package imports
- [ ] No sys.path manipulation remains in any file
- [ ] All tests pass on Windows
- [ ] CHANGELOG.md updated with v1.2.0 section
- [ ] Version updated in precipgen/__init__.py
- [ ] Version updated in setup.py
- [ ] No new markdown documentation files created
- [ ] README.md structure maintained (if updated)

### Windows Compatibility

All commands and tests must work in Windows cmd terminal:
- Use `python` instead of `python3`
- Use backslashes or forward slashes for paths (Python handles both)
- Avoid bash-specific commands (grep, find, etc.)
- Use `python -m pytest` or `python -m unittest` for test execution
