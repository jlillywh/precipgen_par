@echo off
REM PrecipGen Desktop - Certificate Signing Request (CSR) Generator
REM This script helps generate a CSR for obtaining a code signing certificate

echo ========================================
echo Certificate Signing Request Generator
echo ========================================
echo.

REM Check if certreq is available
where certreq >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: certreq.exe not found!
    echo certreq is part of Windows and should be available by default.
    exit /b 1
)

echo This script will generate a Certificate Signing Request (CSR)
echo for obtaining a code signing certificate.
echo.
echo You will need to provide:
echo   - Your name or company name
echo   - Organization name
echo   - City
echo   - State/Province
echo   - Country (2-letter code, e.g., US)
echo.

REM Get user input
set /p COMMON_NAME="Enter your name or company name: "
set /p ORGANIZATION="Enter organization name: "
set /p CITY="Enter city: "
set /p STATE="Enter state/province: "
set /p COUNTRY="Enter country code (2 letters, e.g., US): "

echo.
echo Generating CSR with the following information:
echo   Common Name (CN): %COMMON_NAME%
echo   Organization (O): %ORGANIZATION%
echo   City (L): %CITY%
echo   State (S): %STATE%
echo   Country (C): %COUNTRY%
echo.

REM Create request configuration file
echo [Version] > codesign.inf
echo Signature="$Windows NT$" >> codesign.inf
echo. >> codesign.inf
echo [NewRequest] >> codesign.inf
echo Subject = "CN=%COMMON_NAME%, O=%ORGANIZATION%, L=%CITY%, S=%STATE%, C=%COUNTRY%" >> codesign.inf
echo KeyLength = 2048 >> codesign.inf
echo KeySpec = 1 >> codesign.inf
echo Exportable = TRUE >> codesign.inf
echo MachineKeySet = FALSE >> codesign.inf
echo SMIME = FALSE >> codesign.inf
echo PrivateKeyArchive = FALSE >> codesign.inf
echo UserProtected = FALSE >> codesign.inf
echo UseExistingKeySet = FALSE >> codesign.inf
echo ProviderName = "Microsoft RSA SChannel Cryptographic Provider" >> codesign.inf
echo ProviderType = 12 >> codesign.inf
echo RequestType = PKCS10 >> codesign.inf
echo KeyUsage = 0xa0 >> codesign.inf
echo. >> codesign.inf
echo [EnhancedKeyUsageExtension] >> codesign.inf
echo OID=1.3.6.1.5.5.7.3.3 ; Code Signing >> codesign.inf

echo Generating CSR...
certreq -new codesign.inf codesign.csr

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to generate CSR!
    del codesign.inf
    exit /b 1
)

echo.
echo ========================================
echo CSR Generated Successfully!
echo ========================================
echo.
echo Files created:
echo   - codesign.csr (Certificate Signing Request)
echo   - codesign.inf (Configuration file)
echo.
echo Next steps:
echo 1. Submit codesign.csr to your Certificate Authority (CA)
echo 2. Complete the CA's validation process
echo 3. Download the issued certificate
echo 4. Install the certificate on this machine
echo 5. Use sign_executable.bat to sign your executable
echo.
echo IMPORTANT: Keep codesign.inf secure! It contains information
echo about your private key. Do not share it publicly.
echo.
echo See docs/CODE_SIGNING_GUIDE.md for detailed instructions.
