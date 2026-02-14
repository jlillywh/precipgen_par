# Quick Build Instructions

## TL;DR

### Run from Source
```bash
python -m precipgen.desktop.app
```

### Build Executable
```bash
# Windows Command Prompt
build_executable.bat

# OR Windows PowerShell
.\build_executable.ps1
```

Output: `dist/PrecipGen.exe`

## That's It!

The build scripts handle everything:
- ✓ Dependency checking
- ✓ Cleanup
- ✓ PyInstaller execution
- ✓ Error handling

## First Time Setup

```bash
# Install dependencies (one time only)
pip install -r requirements.txt
```

## What Gets Built

- **Single executable**: `dist/PrecipGen.exe` (~150-200 MB)
- **No installation required**: Just run the .exe
- **Includes everything**: Python runtime + all dependencies
- **GUI application**: No console window

## Verify Build

```bash
# Test the executable
dist\PrecipGen.exe
```

Should open the PrecipGen application with 6 tabs:
1. Home
2. Search
3. Upload
4. Basic Analysis
5. Markov Analysis
6. Trend Analysis

---

For detailed information, see [BUILD_GUIDE.md](BUILD_GUIDE.md)
