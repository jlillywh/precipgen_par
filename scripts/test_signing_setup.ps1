# PrecipGen Desktop - Code Signing Setup Test (PowerShell)
# This script verifies that the code signing infrastructure is properly configured

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Code Signing Setup Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0

# Test 1: Check if signtool is available
Write-Host "[1/7] Checking for signtool..." -ForegroundColor Yellow
$signtool = Get-Command signtool -ErrorAction SilentlyContinue
if ($signtool) {
    Write-Host "  [PASS] signtool found" -ForegroundColor Green
    Write-Host "  $($signtool.Source)"
} else {
    Write-Host "  [FAIL] signtool not found in PATH" -ForegroundColor Red
    Write-Host "  Install Windows SDK: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/" -ForegroundColor Yellow
    $errors++
}
Write-Host ""

# Test 2: Check if executable exists
Write-Host "[2/7] Checking for executable..." -ForegroundColor Yellow
if (Test-Path "dist\PrecipGen.exe") {
    Write-Host "  [PASS] dist\PrecipGen.exe found" -ForegroundColor Green
    $exe = Get-Item "dist\PrecipGen.exe"
    Write-Host "  Size: $([math]::Round($exe.Length / 1MB, 2)) MB"
    Write-Host "  Modified: $($exe.LastWriteTime)"
} else {
    Write-Host "  [FAIL] dist\PrecipGen.exe not found" -ForegroundColor Red
    Write-Host "  Build the executable first: .\build_executable.ps1" -ForegroundColor Yellow
    $errors++
}
Write-Host ""

# Test 3: Check if signing scripts exist
Write-Host "[3/7] Checking for signing scripts..." -ForegroundColor Yellow
if (Test-Path "scripts\sign_executable.bat") {
    Write-Host "  [PASS] sign_executable.bat found" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] sign_executable.bat not found" -ForegroundColor Red
    $errors++
}
if (Test-Path "scripts\sign_executable.ps1") {
    Write-Host "  [PASS] sign_executable.ps1 found" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] sign_executable.ps1 not found" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Test 4: Check if certificate templates exist
Write-Host "[4/7] Checking for certificate templates..." -ForegroundColor Yellow
if (Test-Path "scripts\certificate_config.template.bat") {
    Write-Host "  [PASS] certificate_config.template.bat found" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] certificate_config.template.bat not found" -ForegroundColor Red
    $errors++
}
if (Test-Path "scripts\certificate_config.template.ps1") {
    Write-Host "  [PASS] certificate_config.template.ps1 found" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] certificate_config.template.ps1 not found" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Test 5: Check if documentation exists
Write-Host "[5/7] Checking for documentation..." -ForegroundColor Yellow
if (Test-Path "docs\CODE_SIGNING_GUIDE.md") {
    Write-Host "  [PASS] CODE_SIGNING_GUIDE.md found" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] CODE_SIGNING_GUIDE.md not found" -ForegroundColor Red
    $errors++
}
if (Test-Path "docs\CERTIFICATE_CHECKLIST.md") {
    Write-Host "  [PASS] CERTIFICATE_CHECKLIST.md found" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] CERTIFICATE_CHECKLIST.md not found" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Test 6: Check if certificate is configured
Write-Host "[6/7] Checking for certificate configuration..." -ForegroundColor Yellow
if (Test-Path "scripts\certificate_config.bat") {
    Write-Host "  [INFO] certificate_config.bat found" -ForegroundColor Cyan
    Write-Host "  Certificate appears to be configured"
    
    # Check if it's just the template
    $content = Get-Content "scripts\certificate_config.bat" -Raw
    if ($content -match "REM Copy this file") {
        Write-Host "  [WARN] certificate_config.bat appears to be the template" -ForegroundColor Yellow
        Write-Host "  Please configure your certificate details"
    }
} else {
    Write-Host "  [INFO] certificate_config.bat not found" -ForegroundColor Cyan
    Write-Host "  This is expected if you haven't configured a certificate yet"
    Write-Host "  To configure: Copy-Item scripts\certificate_config.template.bat scripts\certificate_config.bat"
}
Write-Host ""

# Test 7: Check .gitignore configuration
Write-Host "[7/7] Checking .gitignore configuration..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    $gitignore = Get-Content ".gitignore" -Raw
    if ($gitignore -match "\*\.pfx") {
        Write-Host "  [PASS] .gitignore configured to exclude certificate files" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] .gitignore may not exclude certificate files" -ForegroundColor Yellow
        $errors++
    }
} else {
    Write-Host "  [WARN] .gitignore not found" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "[PASS] All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Code signing infrastructure is properly set up." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Obtain a code signing certificate (see docs\CODE_SIGNING_GUIDE.md)"
    Write-Host "2. Configure certificate: Copy-Item scripts\certificate_config.template.bat scripts\certificate_config.bat"
    Write-Host "3. Edit certificate_config.bat with your certificate details"
    Write-Host "4. Sign executable: .\scripts\sign_executable.ps1"
    Write-Host ""
} else {
    Write-Host "[FAIL] $errors test(s) failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the issues above before proceeding." -ForegroundColor Yellow
    Write-Host "See docs\CODE_SIGNING_GUIDE.md for detailed instructions." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Additional information
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Additional Information" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Certificate Authorities:" -ForegroundColor Yellow
Write-Host "  - DigiCert: https://www.digicert.com/"
Write-Host "  - Sectigo: https://sectigo.com/"
Write-Host "  - GlobalSign: https://www.globalsign.com/"
Write-Host "  - SSL.com: https://www.ssl.com/"
Write-Host ""
Write-Host "Certificate Types:" -ForegroundColor Yellow
Write-Host "  - EV (Extended Validation): `$300-500/year, immediate trust"
Write-Host "  - Standard: `$100-300/year, builds trust over time"
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  - Complete guide: docs\CODE_SIGNING_GUIDE.md"
Write-Host "  - Certificate checklist: docs\CERTIFICATE_CHECKLIST.md"
Write-Host "  - Packaging guide: docs\PACKAGING.md"
Write-Host ""
