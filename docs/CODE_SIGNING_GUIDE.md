# PrecipGen Desktop - Code Signing Guide

## Overview

Code signing is a critical step for professional Windows application distribution. A digitally signed executable:

- **Eliminates SmartScreen warnings**: Users won't see "Windows protected your PC" messages
- **Establishes trust**: Shows users the software comes from a verified publisher
- **Enables enterprise deployment**: Many organizations require signed software
- **Protects integrity**: Ensures the executable hasn't been tampered with

This guide covers the complete process of obtaining a code signing certificate and signing the PrecipGen Desktop executable.

## Table of Contents

1. [Understanding Code Signing Certificates](#understanding-code-signing-certificates)
2. [Obtaining a Certificate](#obtaining-a-certificate)
3. [Installing the Certificate](#installing-the-certificate)
4. [Setting Up signtool](#setting-up-signtool)
5. [Signing the Executable](#signing-the-executable)
6. [Verifying the Signature](#verifying-the-signature)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Understanding Code Signing Certificates

### Certificate Types

**Extended Validation (EV) Certificates**
- **Cost**: $300-$500/year
- **Trust Level**: Highest - immediate SmartScreen reputation
- **Validation**: Rigorous identity verification (2-5 days)
- **Storage**: Hardware token (USB device) required
- **Best For**: Commercial software, enterprise deployment

**Standard (OV) Certificates**
- **Cost**: $100-$300/year
- **Trust Level**: Good - builds reputation over time
- **Validation**: Basic identity verification (1-3 days)
- **Storage**: Software certificate (.pfx file)
- **Best For**: Open source projects, individual developers

### Certificate Authorities (CAs)

Trusted CAs for Windows code signing:

1. **DigiCert** (https://www.digicert.com/)
   - Industry leader, excellent support
   - EV: ~$474/year, Standard: ~$474/year
   - Fast validation process

2. **Sectigo** (https://sectigo.com/)
   - Good value, reliable service
   - EV: ~$299/year, Standard: ~$179/year
   - Competitive pricing

3. **GlobalSign** (https://www.globalsign.com/)
   - Enterprise-focused, global presence
   - EV: ~$399/year, Standard: ~$249/year
   - Strong reputation

4. **SSL.com** (https://www.ssl.com/)
   - Budget-friendly option
   - EV: ~$299/year, Standard: ~$159/year
   - Good for small projects

### Recommendation

For PrecipGen Desktop:
- **Commercial/Enterprise**: DigiCert EV certificate
- **Open Source/Individual**: Sectigo Standard certificate
- **Budget-Conscious**: SSL.com Standard certificate

## Obtaining a Certificate

### Step 1: Choose a Certificate Authority

Select a CA based on your budget and requirements. For this guide, we'll use Sectigo as an example.

### Step 2: Prepare Required Information

You'll need:

**For Organizations:**
- Legal business name
- Business registration number
- Physical business address
- Phone number (must be publicly listed)
- Domain name (for validation)
- DUNS number (for EV certificates)

**For Individuals:**
- Full legal name
- Government-issued ID
- Proof of address
- Phone number

### Step 3: Purchase the Certificate

1. Visit the CA's website
2. Select "Code Signing Certificate"
3. Choose certificate type (EV or Standard)
4. Complete the purchase

### Step 4: Generate Certificate Signing Request (CSR)

**Option A: Using certreq (Windows)**

Create a request file `codesign.inf`:

```ini
[Version]
Signature="$Windows NT$"

[NewRequest]
Subject = "CN=Your Name or Company, O=Your Organization, L=Your City, S=Your State, C=US"
KeyLength = 2048
KeySpec = 1
Exportable = TRUE
MachineKeySet = FALSE
SMIME = FALSE
PrivateKeyArchive = FALSE
UserProtected = FALSE
UseExistingKeySet = FALSE
ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
ProviderType = 12
RequestType = PKCS10
KeyUsage = 0xa0

[EnhancedKeyUsageExtension]
OID=1.3.6.1.5.5.7.3.3 ; Code Signing
```

Generate the CSR:

```cmd
certreq -new codesign.inf codesign.csr
```

**Option B: Using OpenSSL**

```bash
openssl req -new -newkey rsa:2048 -nodes -keyout codesign.key -out codesign.csr
```

### Step 5: Submit CSR to CA

1. Log into your CA account
2. Navigate to certificate management
3. Upload the CSR file
4. Complete validation process

### Step 6: Complete Validation

**For Standard Certificates:**
- Email verification
- Phone verification
- Document submission (business registration, ID)
- Typically takes 1-3 business days

**For EV Certificates:**
- All standard validation steps
- Additional business verification
- DUNS number verification
- Attorney opinion letter (sometimes)
- Typically takes 2-5 business days

### Step 7: Receive Certificate

Once validated, the CA will issue your certificate:
- Download the certificate file (usually .cer or .crt)
- Download any intermediate certificates
- Keep the certificate and private key secure

## Installing the Certificate

### For Standard Certificates (.pfx file)

If you receive a .pfx file (contains both certificate and private key):

1. **Double-click the .pfx file**
2. **Certificate Import Wizard**:
   - Store Location: "Current User"
   - Click "Next"
   - Enter password (if prompted)
   - Select "Automatically select the certificate store"
   - Click "Next" → "Finish"

3. **Verify Installation**:
   ```cmd
   certmgr.msc
   ```
   - Navigate to "Personal" → "Certificates"
   - Find your code signing certificate

### For EV Certificates (Hardware Token)

EV certificates come on a USB hardware token:

1. **Insert the USB token**
2. **Install token drivers** (provided by CA)
3. **Verify token is recognized**:
   ```cmd
   certutil -scinfo
   ```

### Converting Certificate Formats

If you have separate certificate and key files:

```bash
# Combine certificate and key into .pfx
openssl pkcs12 -export -out codesign.pfx -inkey codesign.key -in codesign.cer -certfile intermediate.cer
```

## Setting Up signtool

### Install Windows SDK

signtool.exe is part of the Windows SDK.

**Option 1: Install Full Windows SDK**

1. Download from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
2. Run installer
3. Select "Windows SDK Signing Tools for Desktop Apps"
4. Complete installation

**Option 2: Install Standalone signtool**

For a lighter installation:

1. Download Windows SDK ISO
2. Extract only the signtool components
3. Add to PATH

### Locate signtool.exe

After installation, find signtool.exe:

```cmd
where signtool
```

Common locations:
- `C:\Program Files (x86)\Windows Kits\10\bin\10.0.xxxxx.0\x64\signtool.exe`
- `C:\Program Files (x86)\Microsoft SDKs\Windows\v10.0A\bin\NETFX 4.8 Tools\signtool.exe`

### Add signtool to PATH

**Option 1: Temporary (Current Session)**

```cmd
set PATH=%PATH%;C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64
```

**Option 2: Permanent (System-Wide)**

1. Open "Environment Variables"
2. Edit "Path" variable
3. Add signtool directory
4. Click "OK"

### Verify signtool Installation

```cmd
signtool /?
```

Should display signtool help information.

## Signing the Executable

### Signing with .pfx File

**Basic Signing:**

```cmd
signtool sign /f "path\to\certificate.pfx" /p "certificate_password" /fd SHA256 /t http://timestamp.digicert.com dist\PrecipGen.exe
```

**Parameters Explained:**
- `/f`: Path to certificate file
- `/p`: Certificate password
- `/fd SHA256`: Use SHA256 hash algorithm (required for modern Windows)
- `/t`: Timestamp server URL (ensures long-term validity)
- Last parameter: File to sign

**With Description:**

```cmd
signtool sign /f "certificate.pfx" /p "password" /fd SHA256 /t http://timestamp.digicert.com /d "PrecipGen Desktop" /du "https://precipgen.example.com" dist\PrecipGen.exe
```

Additional parameters:
- `/d`: Description of the signed content
- `/du`: URL for more information

### Signing with Certificate from Store

If certificate is installed in Windows certificate store:

```cmd
signtool sign /n "Your Certificate Name" /fd SHA256 /t http://timestamp.digicert.com dist\PrecipGen.exe
```

Parameters:
- `/n`: Certificate subject name (as shown in certmgr.msc)

### Signing with Hardware Token (EV Certificate)

```cmd
signtool sign /sha1 CERTIFICATE_THUMBPRINT /fd SHA256 /t http://timestamp.digicert.com dist\PrecipGen.exe
```

To find certificate thumbprint:

```cmd
certutil -scinfo
```

Or use certificate store:

```cmd
signtool sign /n "Your EV Certificate Name" /fd SHA256 /t http://timestamp.digicert.com dist\PrecipGen.exe
```

### Timestamp Servers

Use one of these trusted timestamp servers:

- **DigiCert**: `http://timestamp.digicert.com`
- **Sectigo**: `http://timestamp.sectigo.com`
- **GlobalSign**: `http://timestamp.globalsign.com`
- **SSL.com**: `http://ts.ssl.com`

**Why Timestamping is Critical:**
- Without timestamp: Signature expires when certificate expires
- With timestamp: Signature remains valid indefinitely
- Always include `/t` parameter

### Dual Signing (SHA1 + SHA256)

For maximum compatibility with older Windows versions:

```cmd
REM Sign with SHA1 first
signtool sign /f "certificate.pfx" /p "password" /fd SHA1 /t http://timestamp.digicert.com dist\PrecipGen.exe

REM Add SHA256 signature
signtool sign /f "certificate.pfx" /p "password" /fd SHA256 /as /t http://timestamp.digicert.com dist\PrecipGen.exe
```

Note: `/as` appends signature instead of replacing

## Verifying the Signature

### Command-Line Verification

```cmd
signtool verify /pa dist\PrecipGen.exe
```

Expected output:
```
Successfully verified: dist\PrecipGen.exe
```

### Detailed Verification

```cmd
signtool verify /pa /v dist\PrecipGen.exe
```

Shows:
- Certificate details
- Signature algorithm
- Timestamp information
- Certificate chain

### GUI Verification

1. Right-click `PrecipGen.exe`
2. Select "Properties"
3. Go to "Digital Signatures" tab
4. Select signature
5. Click "Details"
6. Verify:
   - Signature is valid
   - Certificate is not expired
   - Timestamp is present
   - Publisher name is correct

### Testing SmartScreen Behavior

1. Copy signed executable to a test machine
2. Download from internet (to trigger SmartScreen)
3. Run the executable
4. Verify:
   - **EV Certificate**: No warning, runs immediately
   - **Standard Certificate**: May show warning initially, builds reputation over time

## Troubleshooting

### Error: "SignTool Error: No certificates were found that met all the given criteria"

**Cause**: Certificate not found or not accessible

**Solutions:**
1. Verify certificate is installed: `certmgr.msc`
2. Check certificate name matches `/n` parameter
3. For .pfx files, verify file path and password
4. For hardware tokens, ensure token is inserted and drivers installed

### Error: "SignTool Error: The specified timestamp server either could not be reached or returned an invalid response"

**Cause**: Timestamp server is unavailable or network issue

**Solutions:**
1. Check internet connection
2. Try a different timestamp server
3. Retry after a few minutes
4. Use `/tr` instead of `/t` for RFC 3161 timestamp servers:
   ```cmd
   signtool sign /f "certificate.pfx" /p "password" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 dist\PrecipGen.exe
   ```

### Error: "SignTool Error: The file is already signed"

**Cause**: Attempting to sign an already-signed file

**Solutions:**
1. Use `/as` to append signature (for dual signing)
2. Remove existing signature first (not recommended)
3. Rebuild executable if you need to replace signature

### Warning: SmartScreen Still Shows Warning

**Cause**: Standard certificates need to build reputation

**Solutions:**
1. **For EV certificates**: Should work immediately, verify certificate is EV type
2. **For Standard certificates**: 
   - Reputation builds over time (weeks to months)
   - More downloads = faster reputation building
   - Consider upgrading to EV certificate
3. Verify signature is valid: `signtool verify /pa dist\PrecipGen.exe`

### Error: "The certificate chain was issued by an authority that is not trusted"

**Cause**: Missing intermediate certificates

**Solutions:**
1. Download intermediate certificates from CA
2. Install intermediate certificates
3. Include intermediate certificates in signing:
   ```cmd
   signtool sign /f "certificate.pfx" /p "password" /fd SHA256 /t http://timestamp.digicert.com /ac "intermediate.cer" dist\PrecipGen.exe
   ```

## Best Practices

### Security

1. **Protect Private Keys**:
   - Store .pfx files in secure location
   - Use strong passwords
   - Never commit certificates to version control
   - For EV certificates, keep hardware token secure

2. **Use Environment Variables for Passwords**:
   ```cmd
   set CERT_PASSWORD=your_password
   signtool sign /f "certificate.pfx" /p "%CERT_PASSWORD%" /fd SHA256 /t http://timestamp.digicert.com dist\PrecipGen.exe
   ```

3. **Limit Certificate Access**:
   - Only authorized personnel should have access
   - Use separate certificates for different projects if needed
   - Revoke certificate immediately if compromised

### Automation

1. **Create Signing Script** (see `scripts/sign_executable.bat`)
2. **Integrate into Build Process**:
   - Sign immediately after building
   - Verify signature before distribution
3. **Use CI/CD Pipelines**:
   - Store certificate securely (Azure Key Vault, AWS Secrets Manager)
   - Automate signing in build pipeline

### Certificate Management

1. **Track Expiration Dates**:
   - Set reminders 60 days before expiration
   - Renew certificates before expiration
   - Test new certificates before old ones expire

2. **Keep Backups**:
   - Backup .pfx files securely
   - Store in multiple secure locations
   - Document certificate passwords securely

3. **Document Certificate Details**:
   - Certificate authority
   - Purchase date and expiration
   - Certificate thumbprint
   - Renewal process

### Distribution

1. **Always Sign Before Distribution**:
   - Never distribute unsigned executables
   - Verify signature after signing
   - Test on clean machine

2. **Provide Verification Instructions**:
   - Include in README how to verify signature
   - Publish certificate thumbprint
   - Provide contact info for security concerns

3. **Monitor Reputation**:
   - Track SmartScreen warnings
   - Monitor user feedback
   - Build reputation through legitimate distribution

## Automated Signing Script

See `scripts/sign_executable.bat` and `scripts/sign_executable.ps1` for automated signing scripts.

## Additional Resources

- **Microsoft Code Signing Documentation**: https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools
- **signtool Reference**: https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool
- **Windows SDK Download**: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
- **Certificate Authority Comparison**: https://codesigning.ksoftware.net/

## Support

For issues with:
- **Certificate purchase/validation**: Contact your CA support
- **signtool errors**: Check Microsoft documentation
- **PrecipGen-specific issues**: See project documentation

## Checklist

Before distributing signed executable:

- [ ] Certificate obtained and installed
- [ ] signtool installed and in PATH
- [ ] Executable signed with SHA256
- [ ] Timestamp included in signature
- [ ] Signature verified with `signtool verify`
- [ ] Digital signature visible in Properties
- [ ] Tested on clean Windows machine
- [ ] SmartScreen behavior verified
- [ ] Certificate expiration tracked
- [ ] Signing process documented

