# PrecipGen Scripts Directory

This directory contains utility scripts for building, signing, and managing the PrecipGen Desktop application.

## Build Scripts

### `build_executable.bat` / `build_executable.ps1`
Builds the standalone Windows executable using PyInstaller.

**Usage:**
```cmd
REM Windows Command Prompt
build_executable.bat

REM PowerShell
.\build_executable.ps1
```

**Output:** `dist\PrecipGen.exe`

**See also:** `docs/PACKAGING.md`

## Code Signing Scripts

### `sign_executable.bat` / `sign_executable.ps1`
Signs the PrecipGen.exe executable with a code signing certificate.

**Prerequisites:**
1. Code signing certificate (EV or Standard)
2. Windows SDK with signtool.exe
3. Certificate configuration (see below)

**Usage:**
```cmd
REM Configure certificate (one-time setup)
copy certificate_config.template.bat certificate_config.bat
notepad certificate_config.bat

REM Sign executable
call certificate_config.bat
sign_executable.bat
```

**See also:** `docs/CODE_SIGNING_GUIDE.md`

### `certificate_config.template.bat` / `certificate_config.template.ps1`
Template for certificate configuration. Copy to `certificate_config.bat` (or `.ps1`) and fill in your certificate details.

**Configuration Options:**

**Option 1: Certificate from Windows Store**
```cmd
set CERT_NAME=Your Certificate Name
```

**Option 2: .pfx Certificate File**
```cmd
set CERT_FILE=path\to\certificate.pfx
set CERT_PASSWORD=your_password
```

**Security:** Never commit `certificate_config.bat` to version control!

### `generate_csr.bat`
Generates a Certificate Signing Request (CSR) for obtaining a code signing certificate.

**Usage:**
```cmd
generate_csr.bat
```

**Output:**
- `codesign.csr` - Submit this to your Certificate Authority
- `codesign.inf` - Configuration file (keep secure)

**See also:** `docs/CODE_SIGNING_GUIDE.md` for complete certificate acquisition instructions

## Legacy Scripts

### `easy_start.py`
Legacy script for starting the Streamlit web interface (deprecated).

### `precipgen.bat` / `precipgen.ps1`
Legacy scripts for running PrecipGen (deprecated).

### `start_precipgen.bat` / `start_precipgen.sh`
Legacy startup scripts (deprecated).

## Workflow

### Complete Build and Sign Workflow

1. **Build the executable:**
   ```cmd
   build_executable.bat
   ```

2. **Sign the executable (optional but recommended):**
   ```cmd
   REM First time: configure certificate
   copy certificate_config.template.bat certificate_config.bat
   notepad certificate_config.bat
   
   REM Sign
   call certificate_config.bat
   sign_executable.bat
   ```

3. **Test the executable:**
   ```cmd
   dist\PrecipGen.exe
   ```

4. **Verify signature:**
   ```cmd
   signtool verify /pa dist\PrecipGen.exe
   ```

5. **Distribute:**
   - Upload signed executable to distribution channel
   - Include README and LICENSE files

## Security Best Practices

### Certificate Security
- Never commit certificate files (`.pfx`, `.p12`, `.key`) to version control
- Never commit `certificate_config.bat` or `certificate_config.ps1` to version control
- Store certificates in secure locations
- Use strong passwords for certificate files
- Keep hardware tokens (EV certificates) physically secure

### Password Management
- Use environment variables for passwords
- Consider using password managers
- For CI/CD, use secure secret management (Azure Key Vault, AWS Secrets Manager)

### Access Control
- Limit certificate access to authorized personnel only
- Document who has access to certificates
- Revoke certificates immediately if compromised

## Troubleshooting

### "signtool not found"
**Solution:** Install Windows SDK and add signtool to PATH
- Download: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
- Common locations:
  - `C:\Program Files (x86)\Windows Kits\10\bin\10.0.xxxxx.0\x64\signtool.exe`

### "Certificate not found"
**Solution:** Verify certificate is installed
- For Windows Store: Run `certmgr.msc` and check "Personal" → "Certificates"
- For .pfx files: Verify file path and password
- For hardware tokens: Ensure token is inserted and drivers installed

### "Timestamp server unavailable"
**Solution:** Try a different timestamp server or retry
- DigiCert: `http://timestamp.digicert.com`
- Sectigo: `http://timestamp.sectigo.com`
- GlobalSign: `http://timestamp.globalsign.com`

### Build fails
**Solution:** See `docs/PACKAGING.md` troubleshooting section

## Documentation

- **Complete Packaging Guide:** `docs/PACKAGING.md`
- **Code Signing Guide:** `docs/CODE_SIGNING_GUIDE.md`
- **Certificate Management:** `docs/CERTIFICATE_CHECKLIST.md`
- **Testing Checklist:** `docs/EXECUTABLE_TESTING.md`

## File Exclusions

The following files are excluded from version control (`.gitignore`):
- `certificate_config.bat`
- `certificate_config.ps1`
- `*.pfx`, `*.p12`, `*.key` (certificate files)
- `codesign.inf`, `codesign.csr` (CSR files)

Templates are included:
- `certificate_config.template.bat`
- `certificate_config.template.ps1`

## Support

For issues with:
- **Building:** See `docs/PACKAGING.md`
- **Code signing:** See `docs/CODE_SIGNING_GUIDE.md`
- **Certificates:** Contact your Certificate Authority
- **PrecipGen:** See main project documentation

