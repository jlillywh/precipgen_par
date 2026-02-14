# PrecipGen Desktop - Build Guide

## Quick Start

### Option 1: Run from Source (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m precipgen.desktop.app
```

### Option 2: Build Standalone Executable (Distribution)

#### Windows Command Prompt
```cmd
build_executable.bat
```

#### Windows PowerShell
```powershell
.\build_executable.ps1
```

## Build Process Details

### Prerequisites
1. **Python 3.9+** installed
2. **All dependencies** installed:
   ```bash
   pip install -r requirements.txt
   ```
3. **PyInstaller** installed (included in requirements.txt)

### Build Steps

The build scripts will:
1. ✓ Check for PyInstaller installation
2. ✓ Verify all dependencies are installed
3. ✓ Clean previous build artifacts (build/ and dist/ folders)
4. ✓ Run PyInstaller with precipgen.spec configuration
5. ✓ Create standalone executable in dist/PrecipGen.exe

### Build Output

After successful build:
- **Executable**: `dist/PrecipGen.exe`
- **Size**: ~150-200 MB (includes Python runtime and all dependencies)
- **Type**: Single-file executable (no installation required)

### Testing the Build

```bash
# Run the executable
dist\PrecipGen.exe
```

The application should start with the Home tab visible.

## Build Configuration

### PyInstaller Spec File: `precipgen.spec`

Key configurations:
- **Entry point**: `precipgen/desktop/app.py`
- **Console**: Disabled (GUI application)
- **Icon**: `assets/precipgen.ico` (if available)
- **UPX compression**: Enabled (reduces file size)
- **Hidden imports**: All precipgen modules explicitly included

### Included Modules

The build includes:
- **Core**: pgpar, pgpar_ext, pgpar_wave, time_series, gap_analyzer
- **Data**: GHCN data fetching, CSV loading, data filling
- **Desktop**: All 6 view panels, 3 controllers, models
- **Dependencies**: CustomTkinter, pandas, numpy, scipy, matplotlib, hypothesis

### Excluded Modules (to reduce size)

- Test frameworks (pytest, unittest)
- Development tools (setuptools, pip, wheel)
- Tkinter test modules

## Troubleshooting

### Build Fails: "PyInstaller not found"
```bash
pip install pyinstaller
```

### Build Fails: "Dependencies missing"
```bash
pip install -r requirements.txt
```

### Build Succeeds but Executable Crashes

1. **Check logs**: Look in `%APPDATA%\PrecipGen\logs\precipgen_desktop.log`
2. **Test from source first**: `python -m precipgen.desktop.app`
3. **Verify all modules**: Check that all new panels are in precipgen.spec hiddenimports

### Executable is Too Large

Current size (~150-200 MB) is normal for Python GUI applications with scientific libraries.

To reduce size:
- Remove unused dependencies from requirements.txt
- Disable UPX compression if it's causing issues: `upx=False` in precipgen.spec
- Use one-folder mode instead of one-file (uncomment COLLECT in precipgen.spec)

## Advanced Build Options

### One-Folder Mode (Faster startup, larger distribution)

Edit `precipgen.spec`:
1. Comment out the single-file EXE configuration
2. Uncomment the COLLECT section at the bottom
3. Rebuild

Result: `dist/PrecipGen/` folder with executable and DLLs

### Add Version Information

Create `version_info.txt`:
```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 2, 1, 0),
    prodvers=(1, 2, 1, 0),
    ...
  ),
  ...
)
```

### Code Signing (Optional)

After building, sign the executable:
```powershell
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\PrecipGen.exe
```

## Distribution

### Simple Distribution
1. Build the executable: `build_executable.bat`
2. Zip the dist folder: `dist/PrecipGen.exe`
3. Share the zip file

### Professional Distribution (Optional)
1. Build executable
2. Sign with code certificate
3. Create MSI installer with WiX Toolset
4. Distribute via website or package manager

## Testing Checklist

After building, test:
- [ ] Application starts without errors
- [ ] Home tab displays correctly
- [ ] Can select working directory
- [ ] Search tab can fetch GHCN stations
- [ ] Download functionality works
- [ ] Upload custom data works
- [ ] Basic Analysis calculates statistics
- [ ] Markov Analysis calculates parameters
- [ ] Trend Analysis generates plots
- [ ] Export functions save CSV files
- [ ] Application closes cleanly

## Performance Notes

### Build Time
- First build: 3-5 minutes
- Subsequent builds: 2-3 minutes

### Startup Time
- From source: <1 second
- Executable (one-file): 3-5 seconds (unpacking)
- Executable (one-folder): <1 second

### Runtime Performance
No difference between source and executable versions.

## Support

For build issues:
1. Check this guide
2. Review PyInstaller documentation: https://pyinstaller.org
3. Check project issues on GitHub
4. Review logs in `%APPDATA%\PrecipGen\logs\`

---

**Last Updated**: 2026-02-13
**Version**: 1.2.1
**Build System**: PyInstaller 5.0+
