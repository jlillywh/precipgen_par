# PrecipGen PAR - Project Structure

## Overview

This document provides a visual overview of the project structure following the v1.2.0 reorganization.

## Directory Tree

```
precipgen_par/
│
├── 📦 precipgen/                    # Main Python package
│   ├── __init__.py                 # Package initialization
│   │
│   ├── 🧮 core/                    # Core analysis modules
│   │   ├── __init__.py
│   │   ├── time_series.py          # Time series data handling
│   │   ├── pgpar.py                # Basic parameter calculation
│   │   ├── pgpar_ext.py            # Extended parameter analysis
│   │   ├── pgpar_wave.py           # Wave function analysis
│   │   ├── random_walk_params.py   # Random walk parameters
│   │   ├── precip_stats.py         # Precipitation statistics
│   │   └── long_term_analyzer.py   # Long-term trend analysis
│   │
│   ├── 📊 data/                    # Data handling modules
│   │   ├── __init__.py
│   │   ├── csv_loader.py           # CSV file loading
│   │   ├── ghcn_data.py            # GHCN data interface
│   │   ├── data_filler.py          # Gap filling algorithms
│   │   ├── gap_analyzer.py         # Gap analysis tools
│   │   ├── find_stations.py        # Station discovery
│   │   └── find_ghcn_stations.py   # GHCN station filtering
│   │
│   ├── ⌨️  cli/                     # Command-line interface
│   │   ├── __init__.py
│   │   └── cli.py                  # CLI implementation
│   │
│   └── 🌐 web/                     # Web interface
│       ├── __init__.py
│       └── streamlit_app.py        # Streamlit web app
│
├── 📜 scripts/                      # Executable scripts
│   ├── easy_start.py               # Interactive menu
│   ├── precipgen.bat               # Windows CLI wrapper
│   ├── precipgen.ps1               # PowerShell CLI wrapper
│   ├── start_precipgen.bat         # Windows menu launcher
│   ├── start_precipgen.sh          # Linux/Mac menu launcher
│   ├── run_streamlit.bat           # Windows web launcher
│   └── run_streamlit.sh            # Linux/Mac web launcher
│
├── 📚 docs/                         # Documentation
│   ├── README.md                   # Documentation index
│   │
│   ├── 📖 guides/                  # User guides
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
│   │
│   ├── 🚀 deployment/              # Deployment docs
│   │   ├── DEPLOYMENT.md
│   │   ├── STREAMLIT_DEPLOYMENT_CHECKLIST.md
│   │   └── PUBLISH_SUMMARY.md
│   │
│   ├── 🔧 api/                     # API documentation (future)
│   │
│   └── Technical docs
│       ├── BUGFIX_CSV_METADATA.md
│       ├── CHANGES_SUMMARY.md
│       ├── STREAMLIT_SUMMARY.md
│       └── README_BADGES.md
│
├── 🧪 tests/                        # Test suite
│   ├── __init__.py
│   ├── test_comprehensive.py
│   ├── test_comprehensive_final.py
│   ├── test_pgpar.py
│   └── GrandJunction/              # Test data
│
├── ⚙️  .streamlit/                  # Streamlit configuration
│   └── config.toml
│
├── 🚀 Entry Points (Root Level)
│   ├── precipgen-web.py            # Launch web interface
│   ├── precipgen-cli.py            # Launch CLI
│   └── precipgen-menu.py           # Launch interactive menu
│
└── 📄 Configuration & Documentation
    ├── README.md                   # Main documentation
    ├── CHANGELOG.md                # Version history
    ├── CONTRIBUTING.md             # Contribution guidelines
    ├── LICENSE                     # MIT License
    ├── REORGANIZATION.md           # Reorganization details
    ├── PROJECT_STRUCTURE.md        # This file
    ├── setup.py                    # Package setup
    ├── requirements.txt            # Dependencies
    ├── precipgen_config.json       # Configuration
    └── .gitignore                  # Git ignore rules
```

## Quick Navigation

### For Users
- **Getting Started**: `docs/guides/GETTING_STARTED.md`
- **Quick Reference**: `docs/guides/QUICK_REFERENCE.md`
- **Web Interface Guide**: `docs/guides/STREAMLIT_GUIDE.md`

### For Developers
- **Core Modules**: `precipgen/core/`
- **Data Handling**: `precipgen/data/`
- **Tests**: `tests/`
- **API Docs**: `docs/api/` (coming soon)

### For Deployment
- **Deployment Guide**: `docs/deployment/DEPLOYMENT.md`
- **Streamlit Deployment**: `docs/deployment/STREAMLIT_DEPLOYMENT_CHECKLIST.md`

## Module Responsibilities

### precipgen.core
- Time series data structures
- Parameter calculations (PWW, PWD, alpha, beta)
- Statistical analysis
- Wave function decomposition
- Random walk modeling

### precipgen.data
- CSV file loading and parsing
- GHCN data fetching
- Station discovery and filtering
- Gap analysis
- Data filling algorithms

### precipgen.cli
- Command-line argument parsing
- CLI commands implementation
- Output formatting

### precipgen.web
- Streamlit web interface
- Interactive visualizations
- User-friendly workflows

## Entry Points

### Web Interface
```bash
streamlit run precipgen-web.py
# or
python scripts/run_streamlit.bat  # Windows
./scripts/run_streamlit.sh        # Linux/Mac
```

### Command Line
```bash
python precipgen-cli.py <command> [options]
# or after installation
precipgen-cli <command> [options]
```

### Interactive Menu
```bash
python precipgen-menu.py
# or
python scripts/easy_start.py
```

## Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Standard Python Layout**: Follows PEP 8 and community best practices
3. **Easy Navigation**: Logical grouping makes code easy to find
4. **Clean Root**: Only essential files in root directory
5. **Comprehensive Documentation**: Well-organized docs for all user types
6. **Multiple Interfaces**: CLI, Web, and Interactive menu for different use cases
7. **Testable**: Clear module boundaries enable easy testing

## Benefits of This Structure

- ✅ Professional, industry-standard layout
- ✅ Easy to understand and navigate
- ✅ Ready for PyPI distribution
- ✅ Supports multiple interfaces (CLI, Web, Menu)
- ✅ Clear documentation organization
- ✅ Maintainable and scalable
- ✅ Follows Python best practices
