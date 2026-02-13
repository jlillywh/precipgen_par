# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PrecipGen Desktop Application.

This spec file configures PyInstaller to create a standalone Windows executable
that includes all necessary dependencies and assets.

Usage:
    pyinstaller precipgen.spec

Requirements:
    - PyInstaller installed (pip install pyinstaller)
    - All dependencies from requirements.txt installed
    - Optional: precipgen.ico file in assets/ directory for application icon
"""

import sys
from pathlib import Path

# Determine the project root directory
project_root = Path.cwd()

# Define data files to include
datas = []

# Include any assets if they exist (icons, images, etc.)
assets_dir = project_root / 'assets'
if assets_dir.exists():
    datas.append((str(assets_dir), 'assets'))

# Include precipgen package data files if any
precipgen_data = project_root / 'precipgen' / 'data'
if precipgen_data.exists():
    # Add any data files from precipgen.data package
    pass

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'customtkinter',
    'hypothesis',
    'scipy',
    'scipy.special',
    'scipy.special._ufuncs_cxx',
    'scipy.stats',
    'scipy.optimize',
    'pandas',
    'numpy',
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
    'PIL',
    'PIL._tkinter_finder',
    'requests',
    'tqdm',
    # PrecipGen modules
    'precipgen.core',
    'precipgen.core.pgpar',
    'precipgen.core.pgpar_ext',
    'precipgen.core.pgpar_wave',
    'precipgen.core.precip_stats',
    'precipgen.core.time_series',
    'precipgen.core.long_term_analyzer',
    'precipgen.core.random_walk_params',
    'precipgen.core.log_config',
    'precipgen.data',
    'precipgen.data.csv_loader',
    'precipgen.data.data_filler',
    'precipgen.data.find_ghcn_stations',
    'precipgen.data.find_stations',
    'precipgen.data.gap_analyzer',
    'precipgen.data.ghcn_data',
    'precipgen.desktop',
    'precipgen.desktop.app',
    'precipgen.desktop.models.app_state',
    'precipgen.desktop.models.session_config',
    'precipgen.desktop.controllers.project_controller',
    'precipgen.desktop.controllers.data_controller',
    'precipgen.desktop.controllers.calibration_controller',
    'precipgen.desktop.views.main_window',
    'precipgen.desktop.views.project_panel',
    'precipgen.desktop.views.data_panel',
    'precipgen.desktop.views.calibration_panel',
]

# Binaries to exclude (reduce size)
excludes = [
    'tkinter.test',
    'unittest',
    'test',
    'tests',
    'pytest',
    'setuptools',
    'pip',
    'wheel',
]

# Analysis: Scan the main script and dependencies
a = Analysis(
    ['precipgen/desktop/app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ: Create a compressed archive of Python modules
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
)

# EXE: Create the executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PrecipGen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI application)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets_dir / 'precipgen.ico') if (assets_dir / 'precipgen.ico').exists() else None,
    version_file='version_info.txt',  # Include version information
)

# Optional: Create a COLLECT for one-folder mode (uncomment if needed)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='PrecipGen'
# )
