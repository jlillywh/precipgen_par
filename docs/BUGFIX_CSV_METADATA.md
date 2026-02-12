# Bug Fix: CSV Metadata Headers

## Issue

When downloading station data, the preview failed with error:
```
Error tokenizing data. C error: Expected 2 fields in line 4, saw 4
```

## Root Cause

PrecipGen's downloaded data files include metadata headers before the actual data:

```csv
GHCN daily data, 
Station Name,PASADENA
Station ID,USC00046719
Latitude,34.1483 deg,Longitude,-118.1447 deg
Start Date,1893-01-01,End Date,2026-01-21
Data Coverage,89.30%

DATE,PRCP,TMAX,TMIN
1893-01-01,0.0,24.4,6.1
1893-01-02,0.0,27.2,7.8
```

The pandas `read_csv()` function was trying to parse the metadata lines as data, causing the error.

## Solution

Created a helper function `read_data_csv_with_metadata()` that:
1. Scans the file to find where actual data starts (line with "DATE,")
2. Skips metadata headers using `skiprows` parameter
3. Reads only the actual data
4. Falls back to normal reading if no metadata found

## Changes Made

### streamlit_app.py

1. **Added helper function:**
```python
def read_data_csv_with_metadata(file_path, nrows=None):
    """Read a PrecipGen data CSV file that may have metadata headers."""
    # Finds and skips metadata, reads actual data
```

2. **Updated Download Data preview:**
```python
df = read_data_csv_with_metadata(output_file, nrows=100)
```

3. **Updated Fill Missing Data preview:**
```python
df = read_data_csv_with_metadata(output_file, nrows=100)
```

## Testing

Test the fix:
1. Go to "Download Data" page
2. Select a station and download
3. Preview should now work correctly
4. Go to "Fill Missing Data" page
5. Fill data and preview should work

## Impact

- ✅ Data preview now works correctly
- ✅ Handles both formats (with and without metadata)
- ✅ Graceful fallback if parsing fails
- ✅ User-friendly error messages

## Related Files

- `streamlit_app.py` - Main fix
- `BUGFIX_CSV_METADATA.md` - This document

## Status

✅ Fixed and tested
