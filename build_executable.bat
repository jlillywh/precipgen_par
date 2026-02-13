@echo off
REM Build script for PrecipGen Desktop executable
REM This script builds a standalone Windows executable using PyInstaller

echo ========================================
echo PrecipGen Desktop - Build Executable
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed
    echo Please install it with: pip install pyinstaller
    echo.
    pause
    exit /b 1
)

REM Check if all dependencies are installed
echo Checking dependencies...
python -c "import customtkinter, hypothesis, scipy, pandas, numpy, matplotlib, requests, tqdm" 2>nul
if errorlevel 1 (
    echo ERROR: Some dependencies are missing
    echo Please install all dependencies with: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo All dependencies found.
echo.

REM Clean previous build artifacts
echo Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

REM Run PyInstaller
echo Building executable with PyInstaller...
echo This may take several minutes...
echo.
pyinstaller precipgen.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\PrecipGen.exe
echo.
echo Next steps:
echo 1. Test the executable: dist\PrecipGen.exe
echo 2. (Optional) Sign the executable with code signing certificate
echo 3. (Optional) Create MSI installer with WiX Toolset
echo.
pause
