@echo off
REM PrecipGen Desktop - Code Signing Setup Test
REM This script verifies that the code signing infrastructure is properly configured

echo ========================================
echo Code Signing Setup Test
echo ========================================
echo.

set ERRORS=0

REM Test 1: Check if signtool is available
echo [1/7] Checking for signtool...
where signtool >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [PASS] signtool found
    where signtool
) else (
    echo   [FAIL] signtool not found in PATH
    echo   Install Windows SDK: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
    set /a ERRORS+=1
)
echo.

REM Test 2: Check if executable exists
echo [2/7] Checking for executable...
if exist "dist\PrecipGen.exe" (
    echo   [PASS] dist\PrecipGen.exe found
    dir dist\PrecipGen.exe | findstr "PrecipGen.exe"
) else (
    echo   [FAIL] dist\PrecipGen.exe not found
    echo   Build the executable first: build_executable.bat
    set /a ERRORS+=1
)
echo.

REM Test 3: Check if signing scripts exist
echo [3/7] Checking for signing scripts...
if exist "scripts\sign_executable.bat" (
    echo   [PASS] sign_executable.bat found
) else (
    echo   [FAIL] sign_executable.bat not found
    set /a ERRORS+=1
)
if exist "scripts\sign_executable.ps1" (
    echo   [PASS] sign_executable.ps1 found
) else (
    echo   [FAIL] sign_executable.ps1 not found
    set /a ERRORS+=1
)
echo.

REM Test 4: Check if certificate templates exist
echo [4/7] Checking for certificate templates...
if exist "scripts\certificate_config.template.bat" (
    echo   [PASS] certificate_config.template.bat found
) else (
    echo   [FAIL] certificate_config.template.bat not found
    set /a ERRORS+=1
)
if exist "scripts\certificate_config.template.ps1" (
    echo   [PASS] certificate_config.template.ps1 found
) else (
    echo   [FAIL] certificate_config.template.ps1 not found
    set /a ERRORS+=1
)
echo.

REM Test 5: Check if documentation exists
echo [5/7] Checking for documentation...
if exist "docs\CODE_SIGNING_GUIDE.md" (
    echo   [PASS] CODE_SIGNING_GUIDE.md found
) else (
    echo   [FAIL] CODE_SIGNING_GUIDE.md not found
    set /a ERRORS+=1
)
if exist "docs\CERTIFICATE_CHECKLIST.md" (
    echo   [PASS] CERTIFICATE_CHECKLIST.md found
) else (
    echo   [FAIL] CERTIFICATE_CHECKLIST.md not found
    set /a ERRORS+=1
)
echo.

REM Test 6: Check if certificate is configured
echo [6/7] Checking for certificate configuration...
if exist "scripts\certificate_config.bat" (
    echo   [INFO] certificate_config.bat found
    echo   Certificate appears to be configured
    
    REM Check if it's just the template
    findstr /C:"REM Copy this file" scripts\certificate_config.bat >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo   [WARN] certificate_config.bat appears to be the template
        echo   Please configure your certificate details
    )
) else (
    echo   [INFO] certificate_config.bat not found
    echo   This is expected if you haven't configured a certificate yet
    echo   To configure: copy scripts\certificate_config.template.bat scripts\certificate_config.bat
)
echo.

REM Test 7: Check .gitignore configuration
echo [7/7] Checking .gitignore configuration...
findstr /C:"*.pfx" .gitignore >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [PASS] .gitignore configured to exclude certificate files
) else (
    echo   [WARN] .gitignore may not exclude certificate files
    set /a ERRORS+=1
)
echo.

REM Summary
echo ========================================
echo Test Summary
echo ========================================
if %ERRORS% EQU 0 (
    echo [PASS] All tests passed!
    echo.
    echo Code signing infrastructure is properly set up.
    echo.
    echo Next steps:
    echo 1. Obtain a code signing certificate (see docs\CODE_SIGNING_GUIDE.md)
    echo 2. Configure certificate: copy scripts\certificate_config.template.bat scripts\certificate_config.bat
    echo 3. Edit certificate_config.bat with your certificate details
    echo 4. Sign executable: scripts\sign_executable.bat
    echo.
) else (
    echo [FAIL] %ERRORS% test(s) failed
    echo.
    echo Please fix the issues above before proceeding.
    echo See docs\CODE_SIGNING_GUIDE.md for detailed instructions.
    echo.
    exit /b 1
)

REM Additional information
echo ========================================
echo Additional Information
echo ========================================
echo.
echo Certificate Authorities:
echo   - DigiCert: https://www.digicert.com/
echo   - Sectigo: https://sectigo.com/
echo   - GlobalSign: https://www.globalsign.com/
echo   - SSL.com: https://www.ssl.com/
echo.
echo Certificate Types:
echo   - EV (Extended Validation): $300-500/year, immediate trust
echo   - Standard: $100-300/year, builds trust over time
echo.
echo Documentation:
echo   - Complete guide: docs\CODE_SIGNING_GUIDE.md
echo   - Certificate checklist: docs\CERTIFICATE_CHECKLIST.md
echo   - Packaging guide: docs\PACKAGING.md
echo.
