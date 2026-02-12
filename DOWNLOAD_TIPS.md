# Download Tips for Large Datasets

## The Issue

When downloading stations with 100+ years of data, the download can take 2-5 minutes and may appear stuck.

## Why It Happens

- NOAA servers can be slow
- Large datasets (133 years = ~48,000 rows)
- Network speed varies
- Processing time for data formatting

## What to Do If Download Appears Stuck

### Option 1: Wait It Out
- Downloads typically complete in 2-5 minutes
- The spinner will keep spinning until done
- Don't close the browser tab

### Option 2: Check If It's Actually Done
1. Open File Explorer
2. Navigate to: `precipgen_data\{project}_precipgen\`
3. Look for `{STATION_ID}_data.csv`
4. If file exists and is growing, download is working
5. If file exists and stopped growing, it's done!

### Option 3: Refresh and Continue
If the file exists:
1. Refresh your browser
2. Go back to Download Data page
3. The file will show as "already exists"
4. Click checkbox to skip re-downloading
5. Continue to next step!

## How We Fixed It

### Before (Hung on Large Downloads)
```python
# Captured all output - caused hanging
success, stdout, stderr = run_cli_command(cmd)
```

### After (No More Hanging)
```python
# Don't capture stdout for large downloads
subprocess.run(cmd, stdout=subprocess.DEVNULL)
```

## Tips for Faster Downloads

### 1. Choose Stations with Less Data
- Look at "Duration" in station list
- Stations with 20-50 years download faster
- 100+ year stations take longer

### 2. Check "Already Downloaded"
- The app now checks if file exists
- Won't re-download if already there
- Saves time on repeated attempts

### 3. Use CLI for Batch Downloads
For multiple stations, use CLI:
```bash
python cli.py download-station USC00046719 -o data.csv
```

## Expected Download Times

| Data Range | Approximate Time |
|------------|------------------|
| 20-30 years | 30-60 seconds |
| 50-70 years | 1-2 minutes |
| 100+ years | 2-5 minutes |
| 130+ years | 3-7 minutes |

Times vary based on:
- Network speed
- NOAA server load
- Time of day
- Data density (gaps vs. complete)

## Troubleshooting

### "Download timed out"
- Station has too much data
- Try a different station
- Or use CLI with no timeout

### "File is empty"
- Download failed
- Check internet connection
- Try again

### "Still stuck after 10 minutes"
- Refresh browser
- Check if file exists
- If exists, continue to next step
- If not, try different station

## Best Practices

✅ **Start with shorter duration stations** (20-50 years)  
✅ **Check file exists before re-downloading**  
✅ **Be patient with 100+ year stations**  
✅ **Use CLI for batch processing**  
✅ **Keep browser tab open during download**  

## Station Examples

### Fast Downloads (< 1 minute)
- Stations with 20-40 years
- Recent stations (2000-2024)
- Stations with many gaps

### Slow Downloads (2-5 minutes)
- Historic stations (1893-2024)
- Complete data (few gaps)
- 100+ years of records

## Your Current Download

**Station:** USC00046719 (Pasadena)  
**Range:** 1893-2026 (133 years)  
**Expected Time:** 3-5 minutes  
**Status:** File exists - download likely complete!

**Next Steps:**
1. Refresh your browser
2. File should be ready to use
3. Continue to "Fill Missing Data" or "Calculate Parameters"

## Future Improvements

Possible enhancements:
- Real-time progress bar
- Estimated time remaining
- Background downloads
- Download queue
- Parallel downloads

For now, the app works reliably - just be patient with large datasets!
