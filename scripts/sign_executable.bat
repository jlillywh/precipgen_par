@echo off
REM PrecipGen Desktop - Code Signing Script (Windows Batch)
REM This script signs the PrecipGen.exe executable with a code signing certificate

echo ========================================
echo PrecipGen Desktop - Code Signing
echo ========================================
echo.

REM Check if executable exists
if not exist "dist\PrecipGen.exe" (
    echo ERROR: dist\PrecipGen.exe not found!
    echo Please build the executable first using build_executable.bat
    exit /b 1
)

REM Check if signtool is available
where signtool >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: signtool.exe not found in PATH!
    echo.
    echo Please install Windows SDK and add signtool to PATH.
    echo Download from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
    echo.
    echo Common signtool locations:
    echo   C:\Program Files (x86)\Windows Kits\10\bin\10.0.xxxxx.0\x64\signtool.exe
    echo   C:\Program Files (x86)\Microsoft SDKs\Windows\v10.0A\bin\NETFX 4.8 Tools\signtool.exe
    exit /b 1
)

echo signtool found: 
where signtool
echo.

REM Configuration
REM You can set these as environment variables or edit them here
if "%CERT_FILE%"=="" set CERT_FILE=certificate.pfx
if "%CERT_PASSWORD%"=="" set CERT_PASSWORD=
if "%CERT_NAME%"=="" set CERT_NAME=
if "%TIMESTAMP_SERVER%"=="" set TIMESTAMP_SERVER=http://timestamp.digicert.com

echo Configuration:
echo   Certificate File: %CERT_FILE%
echo   Certificate Name: %CERT_NAME%
echo   Timestamp Server: %TIMESTAMP_SERVER%
echo.

REM Determine signing method
if not "%CERT_NAME%"=="" (
    echo Using certificate from Windows certificate store...
    echo Certificate Name: %CERT_NAME%
    echo.
    
    REM Sign with certificate from store
    signtool sign /n "%CERT_NAME%" /fd SHA256 /t %TIMESTAMP_SERVER% /d "PrecipGen Desktop" /du "https://github.com/yourusername/precipgen" dist\PrecipGen.exe
    
) else if exist "%CERT_FILE%" (
    echo Using certificate file: %CERT_FILE%
    echo.
    
    if "%CERT_PASSWORD%"=="" (
        echo ERROR: CERT_PASSWORD environment variable not set!
        echo Please set the certificate password:
        echo   set CERT_PASSWORD=your_password
        echo   scripts\sign_executable.bat
        exit /b 1
    )
    
    REM Sign with .pfx file
    signtool sign /f "%CERT_FILE%" /p "%CERT_PASSWORD%" /fd SHA256 /t %TIMESTAMP_SERVER% /d "PrecipGen Desktop" /du "https://github.com/yourusername/precipgen" dist\PrecipGen.exe
    
) else (
    echo ERROR: No certificate configured!
    echo.
    echo Please configure one of the following:
    echo.
    echo Option 1: Use certificate from Windows certificate store
    echo   set CERT_NAME=Your Certificate Name
    echo   scripts\sign_executable.bat
    echo.
    echo Option 2: Use .pfx certificate file
    echo   set CERT_FILE=path\to\certificate.pfx
    echo   set CERT_PASSWORD=your_password
    echo   scripts\sign_executable.bat
    echo.
    echo See docs/CODE_SIGNING_GUIDE.md for detailed instructions.
    exit /b 1
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Signing failed!
    echo.
    echo Common issues:
    echo   - Certificate not found or incorrect name
    echo   - Incorrect password
    echo   - Timestamp server unavailable (try again)
    echo   - Certificate expired
    echo.
    echo See docs/CODE_SIGNING_GUIDE.md for troubleshooting.
    exit /b 1
)

echo.
echo ========================================
echo Signing successful!
echo ========================================
echo.

REM Verify signature
echo Verifying signature...
signtool verify /pa dist\PrecipGen.exe

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Signature verification failed!
    echo The executable was signed but verification failed.
    echo This may indicate a problem with the certificate chain.
    exit /b 1
)

echo.
echo ========================================
echo Verification successful!
echo ========================================
echo.
echo The executable is now signed and ready for distribution.
echo.
echo Next steps:
echo 1. Test the signed executable: dist\PrecipGen.exe
echo 2. Verify digital signature in Properties dialog
echo 3. Test on a clean Windows machine
echo 4. (Optional) Create MSI installer with WiX Toolset
echo.
echo See docs/CODE_SIGNING_GUIDE.md for more information.
