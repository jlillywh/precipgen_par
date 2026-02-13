# Build script for PrecipGen Desktop executable
# This script builds a standalone Windows executable using PyInstaller

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PrecipGen Desktop - Build Executable" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PyInstaller is installed
Write-Host "Checking for PyInstaller..." -ForegroundColor Yellow
try {
    python -c "import PyInstaller" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller not found"
    }
    Write-Host "PyInstaller found." -ForegroundColor Green
} catch {
    Write-Host "ERROR: PyInstaller is not installed" -ForegroundColor Red
    Write-Host "Please install it with: pip install pyinstaller" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if all dependencies are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import customtkinter, hypothesis, scipy, pandas, numpy, matplotlib, requests, tqdm" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Dependencies missing"
    }
    Write-Host "All dependencies found." -ForegroundColor Green
} catch {
    Write-Host "ERROR: Some dependencies are missing" -ForegroundColor Red
    Write-Host "Please install all dependencies with: pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Clean previous build artifacts
Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}
Write-Host "Cleanup complete." -ForegroundColor Green
Write-Host ""

# Run PyInstaller
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

pyinstaller precipgen.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Executable location: dist\PrecipGen.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the executable: dist\PrecipGen.exe"
Write-Host "2. (Optional) Sign the executable with code signing certificate"
Write-Host "3. (Optional) Create MSI installer with WiX Toolset"
Write-Host ""
Read-Host "Press Enter to exit"
