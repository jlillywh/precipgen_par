# Data Organization in PrecipGen

## Clean Separation: Code vs. Data

PrecipGen now keeps source code and output data completely separate!

## Directory Structure

```
precipgen_par/                    ← Your project root
├── Source Code Files
│   ├── cli.py
│   ├── streamlit_app.py
│   ├── easy_start.py
│   ├── time_series.py
│   └── ... (all Python files)
│
├── Documentation
│   ├── README.md
│   ├── GETTING_STARTED.md
│   └── ... (all .md files)
│
└── precipgen_data/               ← ALL OUTPUT FILES GO HERE
    ├── README.md
    ├── phoenix_precipgen/
    │   ├── phoenix_stations.csv
    │   ├── USW00023183_data.csv
    │   ├── USW00023183_filled.csv
    │   └── USW00023183_parameters.csv
    ├── denver_precipgen/
    │   └── ...
    └── seattle_precipgen/
        └── ...
```

## Benefits

### 1. Clean Repository
- Source code directory stays organized
- No data files mixed with Python files
- Easy to see what's code vs. what's data

### 2. Easy Backup
- Backup just `precipgen_data/` for all your analysis work
- Or backup just source code without large data files
- Selective backup based on your needs

### 3. Version Control Friendly
- `precipgen_data/` is in `.gitignore`
- Your data stays private and local
- Git commits only track code changes
- No accidentally committing large data files

### 4. Portability
- Move data independently of code
- Share data with colleagues without code
- Archive old projects easily

### 5. Multiple Installations
- Run multiple PrecipGen installations
- Each with its own data directory
- Share the same data across installations if needed

## How It Works

### Streamlit Interface
- Automatically saves all files to `precipgen_data/`
- Automatically searches for files in `precipgen_data/`
- Shows full path when files are saved
- No configuration needed!

### CLI Interface
- Still works as before
- You can manually specify output paths
- Or use default behavior (saves to current directory)

### Easy Start Menu
- Still works as before
- Creates projects in current directory by default
- You can manually move projects to `precipgen_data/` if desired

## File Locations

### Where Files Are Saved

**Streamlit Interface:**
```
precipgen_data/{project_name}_precipgen/
```

**Example:**
```
precipgen_data/phoenix_precipgen/phoenix_stations.csv
```

**Full Path:**
```
C:\Users\YourName\...\precipgen_par\precipgen_data\phoenix_precipgen\
```

### Finding Your Files

**Option 1: Streamlit Interface**
- Home page shows output directory path
- Success messages show full file paths
- Recent projects listed on home page

**Option 2: File Explorer**
1. Navigate to your PrecipGen directory
2. Open `precipgen_data/` folder
3. Find your project folder

**Option 3: Command Line**
```bash
cd precipgen_data
dir  # Windows
ls   # Mac/Linux
```

## Migration from Old Structure

If you have existing project folders in the root directory:

### Option 1: Move Manually
```bash
# Windows
move phoenix_precipgen precipgen_data\
move denver_precipgen precipgen_data\

# Mac/Linux
mv phoenix_precipgen precipgen_data/
mv denver_precipgen precipgen_data/
```

### Option 2: Keep Both
- Old projects stay in root directory
- New projects go to `precipgen_data/`
- Both work fine!

### Option 3: Start Fresh
- Leave old projects where they are
- New analyses automatically use `precipgen_data/`
- Clean slate for new work

## Customization

Want to change the output directory? Edit `streamlit_app.py`:

```python
# Line ~30
OUTPUT_BASE_DIR = "precipgen_data"  # Change this!
```

Options:
- `"data"` - Simple name
- `"outputs"` - Alternative name
- `"analyses"` - Descriptive name
- `"../shared_data"` - Outside project directory
- `"D:/PrecipGenData"` - Absolute path (Windows)
- `"/mnt/data/precipgen"` - Absolute path (Linux)

## Best Practices

### For Individual Users
✅ Use default `precipgen_data/` directory  
✅ Backup `precipgen_data/` regularly  
✅ Keep source code in version control  
✅ Exclude `precipgen_data/` from git  

### For Teams
✅ Share source code via git  
✅ Share data separately (network drive, cloud)  
✅ Document data locations in team wiki  
✅ Use consistent project naming  

### For Researchers
✅ Archive `precipgen_data/` with publications  
✅ Document data provenance  
✅ Include README in archived data  
✅ Version control analysis scripts only  

## Troubleshooting

### "No files found"
- Check that `precipgen_data/` directory exists
- Verify files are in project subfolders
- Look for `{project}_precipgen/` folders

### "Can't find my old projects"
- Old projects may be in root directory
- Move them to `precipgen_data/` (see Migration above)
- Or continue using them from root directory

### "Want different location"
- Edit `OUTPUT_BASE_DIR` in `streamlit_app.py`
- Restart Streamlit
- New projects use new location

## Summary

**Before:**
```
precipgen_par/
├── cli.py
├── streamlit_app.py
├── phoenix_precipgen/        ← Mixed with code!
├── denver_precipgen/          ← Mixed with code!
└── seattle_precipgen/         ← Mixed with code!
```

**After:**
```
precipgen_par/
├── cli.py
├── streamlit_app.py
└── precipgen_data/            ← Clean separation!
    ├── phoenix_precipgen/
    ├── denver_precipgen/
    └── seattle_precipgen/
```

**Result:** Clean, organized, professional! 🎉
