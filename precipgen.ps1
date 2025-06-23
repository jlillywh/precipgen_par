# PrecipGen CLI Helper Script for PowerShell
# This script runs the CLI tool using the virtual environment Python

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "Virtual environment not found at .venv"
    Write-Host "Please make sure you're in the project directory and the virtual environment is set up."
    exit 1
}

# Run the CLI using the virtual environment Python directly
& ".venv\Scripts\python.exe" "cli.py" @Arguments
