# Fill Missing Data Guide

## What It Does

The fill-data feature uses smart interpolation to fill missing values in precipitation data.

## How It Works

### Automatic Method Selection

The tool automatically tries multiple methods and picks the best one:

1. **Seasonal Average** - Uses same day from nearby years
2. **Moving Average** - Uses surrounding days
3. **Linear Interpolation** - Connects nearby values
4. **Forward Fill** - Uses last known value
5. **Zero Fill** - For long gaps (assumes no precipitation)

### Quality Validation

After filling, the tool validates:
- No negative values
- No extreme outliers
- Statistical consistency
- Reasonable patterns

## Parameters

### Maximum Gap Size (--max-gap-days)

**Default:** 365 days (1 year)

Controls the largest gap that will be filled:
- **Small gaps (1-7 days):** High confidence, uses interpolation
- **Medium gaps (8-30 days):** Moderate confidence, uses seasonal patterns
- **Large gaps (31-365 days):** Lower confidence, uses conservative methods
- **Gaps > max:** Left as missing (not filled)

**Recommendations:**
- **Conservative:** 30 days - Only fill short gaps
- **Balanced:** 90 days - Fill most gaps with good confidence
- **Aggressive:** 365 days - Fill all gaps (default)

## Usage

### Streamlit Interface

1. Go to "🔧 Fill Missing Data"
2. Select your data file
3. Set maximum gap size (default: 365 days)
4. Click "Fill Missing Data"
5. Review the summary report
6. Check the preview

### CLI

```bash
python cli.py fill-data input.csv -o output_filled.csv --max-gap-days 365
```

**Parameters:**
- `input.csv` - Input file with missing data
- `-o output_filled.csv` - Output file for filled data
- `--max-gap-days 365` - Maximum gap to fill (optional, default: 365)
- `--date-col DATE` - Date column name (optional, default: DATE)
- `--precip-col PRCP` - Precipitation column (optional, default: PRCP)

## Output

### Filled Data File

CSV file with missing values filled:
```csv
DATE,PRCP,TMAX,TMIN
2020-01-01,0.0,15.5,5.2
2020-01-02,2.5,14.3,4.8  ← Was missing, now filled
2020-01-03,0.0,16.1,6.0
```

### Filling Report (JSON)

Detailed report saved as `{filename}_filling_report.json`:

```json
{
  "summary": {
    "original_missing_values": 1250,
    "final_missing_values": 45,
    "values_filled": 1205,
    "fill_success_rate": 96.4
  },
  "methods_used": {
    "seasonal_average": 850,
    "moving_average": 200,
    "linear_interpolation": 100,
    "forward_fill": 50,
    "zero_fill": 5
  },
  "validation_results": {
    "quality_good": true,
    "filled_data_negative": 0,
    "filled_data_extreme": 2
  },
  "recommendations": [
    "Data quality is good",
    "Review 2 extreme values"
  ]
}
```

## Understanding the Summary

### Fill Success Rate

- **> 95%:** Excellent - Most gaps filled successfully
- **80-95%:** Good - Most gaps filled, some too large
- **< 80%:** Review - Many large gaps or data issues

### Methods Used

- **Seasonal Average:** Best for regular patterns
- **Moving Average:** Good for smooth trends
- **Linear Interpolation:** Simple, works for short gaps
- **Forward Fill:** Conservative, uses last known value
- **Zero Fill:** Very conservative, for long dry periods

### Quality Metrics

- **Quality Good:** Statistical tests passed
- **Negative Values:** Should be 0 (precipitation can't be negative)
- **Extreme Values:** Unusually high values to review

## Best Practices

### Before Filling

✅ **Run gap analysis first** - Understand your data  
✅ **Check data coverage** - Need at least 70% coverage  
✅ **Review gap patterns** - Random gaps fill better than systematic gaps  

### Choosing Max Gap Size

**For parameter calculation:**
- Use 90-365 days
- More filled data = better statistics

**For time series analysis:**
- Use 30-90 days
- Preserve natural patterns

**For research/publication:**
- Use 30 days or less
- Document filling method
- Report fill statistics

### After Filling

✅ **Review the summary** - Check fill success rate  
✅ **Check extreme values** - Verify they're reasonable  
✅ **Preview the data** - Spot check filled values  
✅ **Save the report** - Document for future reference  

## Common Issues

### "Too many missing values"

**Problem:** > 50% of data is missing  
**Solution:** 
- Try different station with better coverage
- Or accept lower quality results

### "Large gaps not filled"

**Problem:** Gaps > max-gap-days  
**Solution:**
- Increase max-gap-days
- Or accept some missing values

### "Extreme values detected"

**Problem:** Some filled values are unusually high  
**Solution:**
- Review those dates manually
- May be legitimate extreme events
- Or adjust max-gap-days to be more conservative

## Examples

### Example 1: Conservative Filling

```bash
python cli.py fill-data data.csv -o filled.csv --max-gap-days 30
```

- Only fills gaps ≤ 30 days
- High confidence in filled values
- Some gaps remain unfilled

### Example 2: Aggressive Filling

```bash
python cli.py fill-data data.csv -o filled.csv --max-gap-days 365
```

- Fills all gaps ≤ 365 days
- Lower confidence for large gaps
- Minimal missing values remain

### Example 3: Custom Columns

```bash
python cli.py fill-data data.csv -o filled.csv \
  --date-col "Date" \
  --precip-col "Precipitation" \
  --max-gap-days 90
```

- Custom column names
- Balanced gap filling

## Validation

The tool validates filled data:

1. **Range Check:** No negative precipitation
2. **Extreme Check:** Flag values > 99th percentile
3. **Pattern Check:** Filled values match seasonal patterns
4. **Consistency Check:** No sudden jumps

## Recommendations

Based on validation, you'll get recommendations:

- ✅ "Data quality is good" - Proceed with confidence
- ⚠️ "Review extreme values" - Check specific dates
- ⚠️ "Many large gaps filled" - Consider more conservative approach
- ❌ "Poor data quality" - Try different station

## Next Steps

After filling data:

1. **Calculate Parameters** - Use filled data for better statistics
2. **Random Walk Analysis** - Analyze long-term trends
3. **Wave Analysis** - Study seasonal patterns

Filled data provides more complete and reliable results!
