# PrecipGen Desktop - Packaging Guide

This guide explains how to package PrecipGen Desktop as a standalone Windows executable and create an MSI installer for enterprise deployment.

## Overview

The packaging process consists of three main steps:

1. **Build Executable**: Use PyInstaller to create a standalone .exe file
2. **Code Signing**: Sign the executable with a code signing certificate (optional but recommended)
3. **Create MSI Installer**: Use WiX Toolset to create an MSI installer (optional)

## Prerequisites

### Required Software

- **Python 3.9+**: With all dependencies installed (`pip install -r requirements.txt`)
- **PyInstaller**: Install with `pip install pyinstaller`

### Optional Software (for full enterprise deployment)

- **Code Signing Certificate**: EV or Standard certificate from a trusted CA (DigiCert, Sectigo, etc.)
- **Windows SDK**: For signtool.exe (code signing utility)
- **WiX Toolset**: For creating MSI installers (download from https://wixtoolset.org/)

## Step 1: Build Executable

### Quick Build

Use the provided build scripts:

**Windows Command Prompt:**
```cmd
build_executable.bat
```

**PowerShell:**
```powershell
.\build_executable.ps1
```

### Manual Build

If you prefer to build manually:

```cmd
pyinstaller precipgen.spec
```

### Build Output

After a successful build, you'll find:
- **Executable**: `dist\PrecipGen.exe`
- **Build artifacts**: `build\` directory (can be deleted)

### Build Configuration

The build is configured in `precipgen.spec`:

- **Entry point**: `precipgen/desktop/app.py`
- **Mode**: One-file (single .exe)
- **Console**: Disabled (GUI application)
- **Icon**: `assets/precipgen.ico` (if present)
- **Dependencies**: All required packages included
- **UPX compression**: Enabled (reduces file size)

### Customizing the Build

Edit `precipgen.spec` to customize:

- **Add data files**: Modify the `datas` list
- **Add hidden imports**: Modify the `hiddenimports` list
- **Change icon**: Place `precipgen.ico` in `assets/` directory
- **Add version info**: Create a version file and reference it

## Step 2: Code Signing (Optional but Recommended)

Code signing provides several benefits:
- Bypasses Windows SmartScreen warnings
- Establishes trust with users and IT departments
- Required for enterprise deployment in many organizations

**For detailed code signing instructions, see [CODE_SIGNING_GUIDE.md](CODE_SIGNING_GUIDE.md).**

### Quick Start

1. **Obtain a certificate** (see CODE_SIGNING_GUIDE.md for details)
2. **Configure certificate**:
   ```cmd
   copy scripts\certificate_config.template.bat scripts\certificate_config.bat
   REM Edit certificate_config.bat with your certificate details
   ```
3. **Sign the executable**:
   ```cmd
   call scripts\certificate_config.bat
   scripts\sign_executable.bat
   ```

### Obtaining a Certificate

1. **Purchase a certificate** from a trusted CA:
   - DigiCert (https://www.digicert.com/)
   - Sectigo (https://sectigo.com/)
   - GlobalSign (https://www.globalsign.com/)
   - SSL.com (https://www.ssl.com/)

2. **Certificate types**:
   - **EV (Extended Validation)**: Highest trust, immediate SmartScreen reputation
   - **Standard**: Lower cost, builds reputation over time

3. **Cost**: $100-$500/year depending on type and vendor

See [CODE_SIGNING_GUIDE.md](CODE_SIGNING_GUIDE.md) for complete certificate acquisition instructions.

### Signing the Executable

**Automated Method (Recommended):**

```cmd
REM Configure certificate (one-time setup)
copy scripts\certificate_config.template.bat scripts\certificate_config.bat
notepad scripts\certificate_config.bat

REM Sign executable
call scripts\certificate_config.bat
scripts\sign_executable.bat
```

**Manual Method:**

Once you have a certificate:

```cmd
signtool sign /f certificate.pfx /p PASSWORD /t http://timestamp.digicert.com /fd SHA256 dist\PrecipGen.exe
```

Parameters:
- `/f certificate.pfx`: Path to your certificate file
- `/p PASSWORD`: Certificate password
- `/t http://timestamp.digicert.com`: Timestamp server (ensures long-term validity)
- `/fd SHA256`: Use SHA256 hash algorithm

See [CODE_SIGNING_GUIDE.md](CODE_SIGNING_GUIDE.md) for advanced signing options and troubleshooting.

### Verifying the Signature

```cmd
signtool verify /pa dist\PrecipGen.exe
```

## Step 3: Create MSI Installer (Optional)

MSI installers provide:
- Professional installation experience
- Add/Remove Programs integration
- Start menu shortcuts
- Enterprise deployment support (Group Policy, SCCM)

### Prerequisites

Install WiX Toolset from https://wixtoolset.org/

### Creating the Installer

1. **Create WiX configuration** (`precipgen.wxs`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="PrecipGen" Language="1033" Version="1.0.0" 
           Manufacturer="YourOrganization" UpgradeCode="YOUR-GUID-HERE">
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine" />
    
    <MajorUpgrade DowngradeErrorMessage="A newer version is already installed." />
    <MediaTemplate EmbedCab="yes" />

    <Feature Id="ProductFeature" Title="PrecipGen" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
    </Feature>
    
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="PrecipGen" />
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ApplicationProgramsFolder" Name="PrecipGen"/>
      </Directory>
    </Directory>

    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="MainExecutable" Guid="YOUR-GUID-HERE">
        <File Id="PrecipGenEXE" Source="dist\PrecipGen.exe" KeyPath="yes">
          <Shortcut Id="StartMenuShortcut" Directory="ApplicationProgramsFolder"
                    Name="PrecipGen" WorkingDirectory="INSTALLFOLDER"
                    Icon="PrecipGen.ico" IconIndex="0" Advertise="yes" />
        </File>
      </Component>
    </ComponentGroup>
    
    <Icon Id="PrecipGen.ico" SourceFile="assets\precipgen.ico" />
  </Product>
</Wix>
```

2. **Generate GUIDs** for the configuration:

```powershell
[guid]::NewGuid()
```

3. **Build the MSI**:

```cmd
candle.exe precipgen.wxs
light.exe -out PrecipGen.msi precipgen.wixobj
```

4. **Sign the MSI** (if you have a certificate):

```cmd
signtool sign /f certificate.pfx /p PASSWORD /t http://timestamp.digicert.com /fd SHA256 PrecipGen.msi
```

## Testing

### Testing the Executable

1. **Test on development machine**:
   ```cmd
   dist\PrecipGen.exe
   ```

2. **Test on clean Windows machine**:
   - Use a VM or clean Windows installation
   - Verify no Python installation required
   - Test all functionality

### Testing the MSI Installer

1. **Install**:
   ```cmd
   msiexec /i PrecipGen.msi
   ```

2. **Verify**:
   - Check Start menu shortcut
   - Check Add/Remove Programs entry
   - Run the application

3. **Uninstall**:
   ```cmd
   msiexec /x PrecipGen.msi
   ```

4. **Verify cleanup**:
   - Check Program Files directory removed
   - Check Start menu shortcut removed
   - Verify user data preserved (AppData)

## Troubleshooting

### Build Fails with Import Errors

**Problem**: PyInstaller can't find certain modules

**Solution**: Add missing modules to `hiddenimports` in `precipgen.spec`

### Executable Crashes on Startup

**Problem**: Missing dependencies or data files

**Solution**: 
1. Check the error in the log file (AppData\PrecipGen\logs)
2. Add missing data files to `datas` in `precipgen.spec`
3. Add missing imports to `hiddenimports`

### Executable is Too Large

**Problem**: File size is several hundred MB

**Solution**:
1. Ensure UPX compression is enabled (`upx=True`)
2. Add unnecessary packages to `excludes` list
3. Consider using one-folder mode instead of one-file

### SmartScreen Warning

**Problem**: Windows shows "Windows protected your PC" warning

**Solution**:
1. Sign the executable with a code signing certificate
2. For EV certificates, reputation is immediate
3. For standard certificates, reputation builds over time
4. Users can click "More info" → "Run anyway" to bypass

### MSI Build Fails

**Problem**: WiX candle or light commands fail

**Solution**:
1. Verify WiX Toolset is installed and in PATH
2. Check that all GUIDs are valid
3. Verify all file paths in .wxs are correct
4. Check for XML syntax errors

## Distribution

### For Individual Users

Distribute the signed executable:
- Upload to website or file sharing service
- Users download and run directly
- No installation required

### For Enterprise Deployment

Distribute the signed MSI:
- Deploy via Group Policy
- Deploy via SCCM or other management tools
- Users can install via Add/Remove Programs
- Supports silent installation: `msiexec /i PrecipGen.msi /quiet`

## File Locations

After installation, PrecipGen uses these locations:

- **Executable**: `C:\Program Files\PrecipGen\PrecipGen.exe` (if using MSI)
- **Configuration**: `%APPDATA%\PrecipGen\config.json`
- **Logs**: `%APPDATA%\PrecipGen\logs\precipgen_desktop.log`
- **Project Data**: User-selected project folders

## Version Updates

When releasing a new version:

1. Update version in `setup.py`
2. Update version in `precipgen.wxs` (if using MSI)
3. Rebuild executable
4. Re-sign executable and MSI
5. Test upgrade scenario (MSI should preserve user data)

## Additional Resources

- **PyInstaller Documentation**: https://pyinstaller.org/
- **WiX Toolset Documentation**: https://wixtoolset.org/documentation/
- **Code Signing Guide**: https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools
- **Windows Installer**: https://docs.microsoft.com/en-us/windows/win32/msi/windows-installer-portal
