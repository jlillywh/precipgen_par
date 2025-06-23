@echo off
REM PrecipGen CLI Helper Script for Windows
REM This script runs the CLI tool using the virtual environment Python

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found at .venv
    echo Please make sure you're in the project directory and the virtual environment is set up.
    exit /b 1
)

REM Run the CLI using the virtual environment Python directly
.venv\Scripts\python.exe cli.py %*
