# PrecipGen Desktop - Code Signing Script (PowerShell)
# This script signs the PrecipGen.exe executable with a code signing certificate

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PrecipGen Desktop - Code Signing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if executable exists
if (-not (Test-Path "dist\PrecipGen.exe")) {
    Write-Host "ERROR: dist\PrecipGen.exe not found!" -ForegroundColor Red
    Write-Host "Please build the executable first using build_executable.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if signtool is available
$signtool = Get-Command signtool -ErrorAction SilentlyContinue
if (-not $signtool) {
    Write-Host "ERROR: signtool.exe not found in PATH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Windows SDK and add signtool to PATH." -ForegroundColor Yellow
    Write-Host "Download from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Common signtool locations:" -ForegroundColor Yellow
    Write-Host "  C:\Program Files (x86)\Windows Kits\10\bin\10.0.xxxxx.0\x64\signtool.exe"
    Write-Host "  C:\Program Files (x86)\Microsoft SDKs\Windows\v10.0A\bin\NETFX 4.8 Tools\signtool.exe"
    exit 1
}

Write-Host "signtool found: $($signtool.Source)" -ForegroundColor Green
Write-Host ""

# Configuration
# You can set these as environment variables or edit them here
$certFile = if ($env:CERT_FILE) { $env:CERT_FILE } else { "certificate.pfx" }
$certPassword = $env:CERT_PASSWORD
$certName = $env:CERT_NAME
$timestampServer = if ($env:TIMESTAMP_SERVER) { $env:TIMESTAMP_SERVER } else { "http://timestamp.digicert.com" }

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Certificate File: $certFile"
Write-Host "  Certificate Name: $certName"
Write-Host "  Timestamp Server: $timestampServer"
Write-Host ""

# Determine signing method
if ($certName) {
    Write-Host "Using certificate from Windows certificate store..." -ForegroundColor Yellow
    Write-Host "Certificate Name: $certName"
    Write-Host ""
    
    # Sign with certificate from store
    $signArgs = @(
        "sign",
        "/n", $certName,
        "/fd", "SHA256",
        "/t", $timestampServer,
        "/d", "PrecipGen Desktop",
        "/du", "https://github.com/yourusername/precipgen",
        "dist\PrecipGen.exe"
    )
    
    & signtool @signArgs
    $signResult = $LASTEXITCODE
    
} elseif (Test-Path $certFile) {
    Write-Host "Using certificate file: $certFile" -ForegroundColor Yellow
    Write-Host ""
    
    if (-not $certPassword) {
        Write-Host "ERROR: CERT_PASSWORD environment variable not set!" -ForegroundColor Red
        Write-Host "Please set the certificate password:" -ForegroundColor Yellow
        Write-Host '  $env:CERT_PASSWORD = "your_password"' -ForegroundColor Yellow
        Write-Host "  .\scripts\sign_executable.ps1" -ForegroundColor Yellow
        exit 1
    }
    
    # Sign with .pfx file
    $signArgs = @(
        "sign",
        "/f", $certFile,
        "/p", $certPassword,
        "/fd", "SHA256",
        "/t", $timestampServer,
        "/d", "PrecipGen Desktop",
        "/du", "https://github.com/yourusername/precipgen",
        "dist\PrecipGen.exe"
    )
    
    & signtool @signArgs
    $signResult = $LASTEXITCODE
    
} else {
    Write-Host "ERROR: No certificate configured!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please configure one of the following:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1: Use certificate from Windows certificate store" -ForegroundColor Cyan
    Write-Host '  $env:CERT_NAME = "Your Certificate Name"' -ForegroundColor White
    Write-Host "  .\scripts\sign_executable.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 2: Use .pfx certificate file" -ForegroundColor Cyan
    Write-Host '  $env:CERT_FILE = "path\to\certificate.pfx"' -ForegroundColor White
    Write-Host '  $env:CERT_PASSWORD = "your_password"' -ForegroundColor White
    Write-Host "  .\scripts\sign_executable.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "See docs/CODE_SIGNING_GUIDE.md for detailed instructions." -ForegroundColor Yellow
    exit 1
}

if ($signResult -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Signing failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Certificate not found or incorrect name"
    Write-Host "  - Incorrect password"
    Write-Host "  - Timestamp server unavailable (try again)"
    Write-Host "  - Certificate expired"
    Write-Host ""
    Write-Host "See docs/CODE_SIGNING_GUIDE.md for troubleshooting." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Signing successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Verify signature
Write-Host "Verifying signature..." -ForegroundColor Yellow
& signtool verify /pa dist\PrecipGen.exe
$verifyResult = $LASTEXITCODE

if ($verifyResult -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Signature verification failed!" -ForegroundColor Red
    Write-Host "The executable was signed but verification failed." -ForegroundColor Yellow
    Write-Host "This may indicate a problem with the certificate chain." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Verification successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The executable is now signed and ready for distribution." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the signed executable: dist\PrecipGen.exe"
Write-Host "2. Verify digital signature in Properties dialog"
Write-Host "3. Test on a clean Windows machine"
Write-Host "4. (Optional) Create MSI installer with WiX Toolset"
Write-Host ""
Write-Host "See docs/CODE_SIGNING_GUIDE.md for more information." -ForegroundColor Cyan
