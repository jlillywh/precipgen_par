# Project Reorganization - v1.2.0

This document describes the major reorganization of the PrecipGen PAR project to follow Python best practices and improve maintainability.

## New Structure

```
precipgen_par/
├── precipgen/                  # Main Python package
│   ├── __init__.py            # Package initialization
│   ├── core/                  # Core analysis modules
│   │   ├── __init__.py
│   │   ├── time_series.py
│   │   ├── pgpar.py
│   │   ├── pgpar_ext.py
│   │   ├── pgpar_wave.py
│   │   ├── random_walk_params.py
│   │   ├── precip_stats.py
│   │   └── long_term_analyzer.py
│   ├── data/                  # Data handling modules
│   │   ├── __init__.py
│   │   ├── csv_loader.py
│   │   ├── ghcn_data.py
│   │   ├── data_filler.py
│   │   ├── gap_analyzer.py
│   │   ├── find_stations.py
│   │   └── find_ghcn_stations.py
│   ├── cli/                   # CLI interface
│   │   ├── __init__.py
│   │   └── cli.py
│   └── web/                   # Web interface
│       ├── __init__.py
│       └── streamlit_app.py
├── scripts/                    # Executable scripts
│   ├── easy_start.py          # Interactive menu
│   ├── precipgen.bat          # Windows CLI wrapper
│   ├── precipgen.ps1          # PowerShell CLI wrapper
│   ├── precipgen.sh           # Linux/Mac CLI wrapper
│   ├── start_precipgen.bat    # Windows menu launcher
│   ├── start_precipgen.sh     # Linux/Mac menu launcher
│   ├── run_streamlit.bat      # Windows web launcher
│   └── run_streamlit.sh       # Linux/Mac web launcher
├── docs/                       # Documentation
│   ├── README.md              # Documentation index
│   ├── guides/                # User guides
│   │   ├── GETTING_STARTED.md
│   │   ├── QUICK_REFERENCE.md
│   │   ├── STREAMLIT_GUIDE.md
│   │   ├── STREAMLIT_QUICKSTART.md
│   │   ├── STREAMLIT_FEATURES.md
│   │   ├── STREAMLIT_README.md
│   │   ├── INSTALL_STREAMLIT.md
│   │   ├── FILL_DATA_GUIDE.md
│   │   ├── DOWNLOAD_TIPS.md
│   │   ├── DATA_ORGANIZATION.md
│   │   └── INTERFACE_COMPARISON.md
│   ├── deployment/            # Deployment documentation
│   │   ├── DEPLOYMENT.md
│   │   ├── STREAMLIT_DEPLOYMENT_CHECKLIST.md
│   │   └── PUBLISH_SUMMARY.md
│   ├── api/                   # API documentation (future)
│   ├── BUGFIX_CSV_METADATA.md
│   ├── CHANGES_SUMMARY.md
│   ├── STREAMLIT_SUMMARY.md
│   └── README_BADGES.md
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_comprehensive.py
│   ├── test_comprehensive_final.py
│   ├── test_pgpar.py
│   └── GrandJunction/         # Test data
├── .streamlit/                 # Streamlit configuration
│   └── config.toml
├── precipgen-web.py           # Web interface entry point
├── precipgen-cli.py           # CLI entry point
├── precipgen-menu.py          # Interactive menu entry point
├── README.md                   # Main documentation
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
├── setup.py                    # Package setup
├── requirements.txt            # Dependencies
└── .gitignore                  # Git ignore rules
```

## Key Changes

### 1. Package Structure
- Created proper Python package `precipgen/` with subpackages
- Organized code into logical modules: `core/`, `data/`, `cli/`, `web/`
- Added `__init__.py` files for proper package imports

### 2. Documentation Organization
- Moved all documentation to `docs/` directory
- Organized into subdirectories: `guides/`, `deployment/`, `api/`
- Created `docs/README.md` as documentation index

### 3. Scripts Organization
- Moved all executable scripts to `scripts/` directory
- Updated scripts to reference new package structure
- Maintained backward compatibility with wrapper scripts

### 4. Entry Points
- Created clean entry points in root:
  - `precipgen-web.py` - Launch web interface
  - `precipgen-cli.py` - Launch CLI
  - `precipgen-menu.py` - Launch interactive menu

### 5. Updated Configuration
- Updated `setup.py` with new package structure
- Updated version to 1.2.0
- Fixed entry points for console scripts

## Benefits

1. **Standard Python Layout**: Follows PEP 8 and community best practices
2. **Better Organization**: Clear separation of concerns
3. **Easier Imports**: Proper package structure enables clean imports
4. **Improved Maintainability**: Logical grouping makes code easier to find and modify
5. **Professional Structure**: Ready for PyPI distribution
6. **Better Documentation**: Organized docs are easier to navigate
7. **Cleaner Root**: Root directory only contains essential files

## Migration Guide

### For Users

Old command:
```bash
python cli.py params data.csv -o output.csv
```

New command:
```bash
python precipgen-cli.py params data.csv -o output.csv
```

Or install and use:
```bash
pip install -e .
precipgen-cli params data.csv -o output.csv
```

### For Developers

Old import:
```python
from time_series import TimeSeries
from pgpar import calculate_params
```

New import:
```python
from precipgen.core.time_series import TimeSeries
from precipgen.core.pgpar import calculate_params
```

Or use package-level imports:
```python
from precipgen import TimeSeries, calculate_params
```

## Backward Compatibility

- All functionality remains the same
- Entry point scripts provide backward compatibility
- Tests updated to use new structure
- Documentation updated with new paths

## Next Steps

1. Update all internal imports to use new package structure
2. Run tests to ensure everything works
3. Update CHANGELOG.md
4. Commit and push changes
5. Tag new version v1.2.0
