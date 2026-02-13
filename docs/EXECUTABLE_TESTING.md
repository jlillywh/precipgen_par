# PrecipGen Desktop Executable - Testing Checklist

This document provides a comprehensive testing checklist for the PrecipGen Desktop executable before distribution.

## Pre-Distribution Testing

### 1. Build Verification

- [ ] Executable builds without errors
- [ ] No critical warnings in build log
- [ ] Executable file size is reasonable (< 200 MB)
- [ ] Version information is embedded correctly

**How to verify:**
```cmd
pyinstaller precipgen.spec
dir dist\PrecipGen.exe
```

### 2. Development Machine Testing

Test on the machine where the executable was built:

- [ ] Executable launches without errors
- [ ] Main window appears correctly
- [ ] No console window appears (GUI mode)
- [ ] Application icon displays (if icon was provided)
- [ ] Window can be resized and moved
- [ ] Application closes cleanly

**How to test:**
```cmd
dist\PrecipGen.exe
```

### 3. Functional Testing

Test all major features:

#### Project Management
- [ ] Can select project folder
- [ ] Project folder path is displayed correctly
- [ ] Invalid folder selection shows error
- [ ] Project folder persists between sessions

#### Data Search and Download
- [ ] Can search for GHCN stations
- [ ] Search results display correctly
- [ ] Can download station data
- [ ] Download progress indicator works
- [ ] Downloaded data appears in project folder
- [ ] Network errors are handled gracefully

#### Parameter Calculation
- [ ] Historical parameters are calculated
- [ ] Parameters display correctly
- [ ] Out-of-range warnings appear when appropriate

#### Calibration
- [ ] Sliders respond to input
- [ ] Parameter values update in real-time
- [ ] Deviations from historical values are shown
- [ ] Reset button restores historical values
- [ ] Visualizations update correctly

#### Export
- [ ] Can export parameters
- [ ] Export file is created in project folder
- [ ] Export confirmation message appears
- [ ] Exported file contains correct data

### 4. Clean Machine Testing

Test on a Windows machine WITHOUT Python installed:

**Setup:**
- Use a clean Windows VM or test machine
- Ensure Python is NOT installed
- Ensure no development tools are installed

**Tests:**
- [ ] Executable runs without Python
- [ ] No "Python not found" errors
- [ ] All features work correctly
- [ ] Application data is created in AppData

**How to verify Python is not installed:**
```cmd
python --version
REM Should show: 'python' is not recognized as an internal or external command
```

### 5. Windows Version Testing

Test on different Windows versions:

- [ ] Windows 10 (64-bit)
- [ ] Windows 11 (64-bit)
- [ ] Windows Server 2019 or later (if applicable)

### 6. SmartScreen Testing

Test Windows SmartScreen behavior:

**For unsigned executable:**
- [ ] SmartScreen warning appears on first run
- [ ] "More info" → "Run anyway" allows execution
- [ ] Application runs normally after bypass

**For signed executable:**
- [ ] No SmartScreen warning (EV certificate)
- [ ] Minimal warning (Standard certificate)
- [ ] Publisher name displays correctly

### 7. Permissions Testing

Test with different permission levels:

**Standard User:**
- [ ] Application runs without admin rights
- [ ] Can select project folder in user directories
- [ ] Can write to AppData
- [ ] Cannot select system directories

**Administrator:**
- [ ] Application runs with admin rights
- [ ] Can select any folder
- [ ] No permission errors

### 8. Error Handling Testing

Test error scenarios:

**Network Errors:**
- [ ] Disconnect network during download
- [ ] Verify cleanup of partial files
- [ ] Verify error message is clear
- [ ] Verify retry option works

**File System Errors:**
- [ ] Select read-only folder
- [ ] Fill disk during download
- [ ] Delete project folder while app is running
- [ ] Verify error messages are helpful

**Invalid Data:**
- [ ] Corrupt downloaded file
- [ ] Invalid parameter values
- [ ] Verify validation works

### 9. Performance Testing

- [ ] Application starts in < 5 seconds
- [ ] UI remains responsive during operations
- [ ] Long operations show progress indicators
- [ ] Memory usage is reasonable (< 500 MB)
- [ ] No memory leaks during extended use

**How to test:**
- Open Task Manager
- Monitor PrecipGen.exe process
- Perform various operations
- Check memory usage over time

### 10. Session Persistence Testing

- [ ] Window size persists between sessions
- [ ] Window position persists between sessions
- [ ] Project folder persists between sessions
- [ ] Configuration file is created correctly

**How to test:**
1. Run application
2. Resize and move window
3. Select project folder
4. Close application
5. Reopen application
6. Verify settings restored

### 11. Logging Testing

- [ ] Log file is created in AppData
- [ ] Log file contains useful information
- [ ] Errors are logged with stack traces
- [ ] Log rotation works (after 10 MB)
- [ ] Old log files are kept (5 backups)

**Log location:**
```
%APPDATA%\PrecipGen\logs\precipgen_desktop.log
```

### 12. Uninstallation Testing

- [ ] Can delete executable without errors
- [ ] Application data remains in AppData
- [ ] Project data remains in project folders
- [ ] No registry entries left behind
- [ ] No system files modified

## Code Signing Testing (Optional)

If the executable is code-signed:

### Certificate Verification
- [ ] Certificate is valid
- [ ] Certificate is not expired
- [ ] Certificate chain is complete
- [ ] Timestamp is present

**How to verify:**
```cmd
signtool verify /pa dist\PrecipGen.exe
```

### Signature Properties
- [ ] Right-click executable → Properties → Digital Signatures
- [ ] Signature is valid
- [ ] Publisher name is correct
- [ ] Timestamp is present

## Distribution Testing

Before distributing to users:

### Packaging
- [ ] Executable is in clean directory
- [ ] README.txt is included
- [ ] LICENSE file is included (if applicable)
- [ ] No development files included

### Distribution Methods
- [ ] ZIP file extracts correctly
- [ ] Download from website works
- [ ] File integrity (checksum) is correct
- [ ] Antivirus doesn't flag executable

### User Documentation
- [ ] README is clear and complete
- [ ] Installation instructions are accurate
- [ ] Troubleshooting section is helpful
- [ ] Contact information is provided

## Regression Testing

After any changes to the code or build process:

- [ ] Re-run all functional tests
- [ ] Re-run clean machine test
- [ ] Verify no new issues introduced
- [ ] Update version number
- [ ] Update CHANGELOG

## Test Results Documentation

Document test results:

```
Test Date: _______________
Tester: _______________
Build Version: _______________
Windows Version: _______________

Results:
- Development Machine: PASS / FAIL
- Clean Machine: PASS / FAIL
- Functional Tests: PASS / FAIL
- Error Handling: PASS / FAIL
- Performance: PASS / FAIL

Issues Found:
1. _______________
2. _______________

Notes:
_______________
```

## Automated Testing

For continuous integration:

```python
# Run automated tests
python test_executable.py

# Expected output:
# ✓ All tests passed! The executable is ready for distribution.
```

## Known Issues and Limitations

Document any known issues:

- [ ] List any known bugs
- [ ] List any limitations
- [ ] List any workarounds
- [ ] List any platform-specific issues

## Sign-Off

Before distribution, ensure:

- [ ] All critical tests pass
- [ ] No critical bugs remain
- [ ] Documentation is complete
- [ ] Version number is correct
- [ ] CHANGELOG is updated

**Approved by:** _______________
**Date:** _______________
**Version:** _______________

## Post-Distribution Monitoring

After distribution:

- [ ] Monitor user feedback
- [ ] Track crash reports
- [ ] Monitor download statistics
- [ ] Collect feature requests
- [ ] Plan next release

## Resources

- Build script: `build_executable.bat` or `build_executable.ps1`
- Test script: `test_executable.py`
- Packaging guide: `docs/PACKAGING.md`
- Spec file: `precipgen.spec`
