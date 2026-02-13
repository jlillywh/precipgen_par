# Code Signing Certificate - Management Checklist

This checklist helps you track the complete lifecycle of your code signing certificate for PrecipGen Desktop.

## Certificate Acquisition

### Research Phase
- [ ] Reviewed certificate types (EV vs Standard)
- [ ] Compared Certificate Authorities (DigiCert, Sectigo, GlobalSign, SSL.com)
- [ ] Determined budget ($100-$500/year)
- [ ] Decided on certificate type based on needs

### Purchase Phase
- [ ] Selected Certificate Authority
- [ ] Purchased certificate
- [ ] Received order confirmation
- [ ] Noted order number: _______________

### Validation Phase
- [ ] Submitted required documentation
  - [ ] Business registration (for organizations)
  - [ ] Government-issued ID (for individuals)
  - [ ] Proof of address
  - [ ] Phone verification completed
  - [ ] Email verification completed
  - [ ] DUNS verification (for EV certificates)
- [ ] Validation completed
- [ ] Certificate issued

## Certificate Installation

### CSR Generation
- [ ] Generated Certificate Signing Request (CSR)
  - Method used: [ ] certreq [ ] OpenSSL [ ] CA portal
  - CSR file saved: _______________
  - Private key secured: _______________
- [ ] Submitted CSR to CA
- [ ] Received certificate from CA

### Installation
- [ ] Downloaded certificate file
- [ ] Downloaded intermediate certificates (if applicable)
- [ ] Installed certificate
  - Method: [ ] .pfx file [ ] Hardware token [ ] Certificate store
  - Installation date: _______________
- [ ] Verified certificate installation
  - [ ] Visible in certmgr.msc (for Windows store)
  - [ ] Hardware token recognized (for EV)
  - [ ] Certificate details correct

### Configuration
- [ ] Configured signing scripts
  - [ ] Copied certificate_config.template.bat to certificate_config.bat
  - [ ] Set CERT_FILE or CERT_NAME
  - [ ] Set CERT_PASSWORD (if using .pfx)
  - [ ] Tested configuration
- [ ] Verified signtool is installed and in PATH
- [ ] Tested signing process with test file

## Certificate Details

**Certificate Information:**
- Certificate Authority: _______________
- Certificate Type: [ ] EV [ ] Standard
- Subject Name: _______________
- Thumbprint: _______________
- Serial Number: _______________

**Dates:**
- Purchase Date: _______________
- Issue Date: _______________
- Expiration Date: _______________
- Renewal Reminder Set: [ ] Yes [ ] No (set for 60 days before expiration)

**Storage:**
- Storage Method: [ ] .pfx file [ ] Hardware token [ ] Certificate store
- Storage Location: _______________
- Backup Location 1: _______________
- Backup Location 2: _______________
- Password Manager Entry: [ ] Yes [ ] No

**Cost:**
- Purchase Price: $_______________
- Renewal Price: $_______________
- Payment Method: _______________
- Auto-renewal: [ ] Enabled [ ] Disabled

## Signing Process

### Initial Setup
- [ ] Read CODE_SIGNING_GUIDE.md
- [ ] Configured certificate_config.bat or certificate_config.ps1
- [ ] Tested signing with sign_executable.bat or sign_executable.ps1
- [ ] Verified signature with signtool verify
- [ ] Checked digital signature in Properties dialog

### Regular Signing Workflow
- [ ] Build executable with build_executable.bat
- [ ] Sign executable with sign_executable.bat
- [ ] Verify signature
- [ ] Test on development machine
- [ ] Test on clean Windows machine
- [ ] Verify SmartScreen behavior
- [ ] Distribute signed executable

### Signing Parameters Used
- Hash Algorithm: [ ] SHA256 [ ] SHA1+SHA256 (dual)
- Timestamp Server: _______________
- Description: "PrecipGen Desktop"
- URL: _______________

## Security

### Certificate Security
- [ ] Certificate file stored securely
- [ ] Strong password used (if .pfx)
- [ ] Password stored in password manager
- [ ] Certificate not committed to version control
- [ ] .gitignore configured to exclude certificates
- [ ] Access limited to authorized personnel
- [ ] Hardware token stored securely (if EV)

### Access Control
**Authorized Personnel:**
1. Name: _______________ Role: _______________ Access Level: _______________
2. Name: _______________ Role: _______________ Access Level: _______________
3. Name: _______________ Role: _______________ Access Level: _______________

### Backup and Recovery
- [ ] Certificate backed up to secure location
- [ ] Backup tested (can restore and use)
- [ ] Recovery procedure documented
- [ ] Emergency contact information recorded

## Monitoring and Maintenance

### Regular Checks (Monthly)
- [ ] Certificate still valid (not expired)
- [ ] Certificate not revoked
- [ ] Signing process still works
- [ ] SmartScreen reputation maintained
- [ ] No security alerts from CA

### Expiration Management
- [ ] Expiration date tracked in calendar
- [ ] Reminder set for 60 days before expiration
- [ ] Reminder set for 30 days before expiration
- [ ] Renewal process documented
- [ ] Budget allocated for renewal

### Reputation Monitoring (for Standard certificates)
- [ ] Tracking SmartScreen warnings
- [ ] Monitoring user feedback
- [ ] Recording download statistics
- [ ] Documenting reputation improvements

## Troubleshooting History

**Issue Log:**

| Date | Issue | Resolution | Notes |
|------|-------|------------|-------|
|      |       |            |       |
|      |       |            |       |
|      |       |            |       |

## Renewal Process

### 60 Days Before Expiration
- [ ] Review current certificate performance
- [ ] Decide on renewal or upgrade (Standard → EV)
- [ ] Check for CA promotions or discounts
- [ ] Verify budget approval

### 30 Days Before Expiration
- [ ] Initiate renewal with CA
- [ ] Generate new CSR (if required)
- [ ] Submit renewal request
- [ ] Complete validation (if required)

### After Renewal
- [ ] Receive new certificate
- [ ] Install new certificate
- [ ] Test signing with new certificate
- [ ] Update certificate details in this checklist
- [ ] Verify old certificate is backed up
- [ ] Update expiration reminders

## Revocation (Emergency)

**If certificate is compromised:**

- [ ] Immediately contact CA to revoke certificate
- [ ] Document incident
- [ ] Notify users if necessary
- [ ] Obtain replacement certificate
- [ ] Re-sign all distributed executables
- [ ] Update distribution channels
- [ ] Review security procedures

**CA Revocation Contact:**
- Phone: _______________
- Email: _______________
- Portal: _______________

## Documentation

### Files and Locations
- [ ] CODE_SIGNING_GUIDE.md reviewed
- [ ] Certificate files location documented
- [ ] Signing scripts location documented
- [ ] Backup locations documented
- [ ] Recovery procedures documented

### Team Knowledge
- [ ] Team trained on signing process
- [ ] Documentation accessible to authorized personnel
- [ ] Emergency procedures communicated
- [ ] Contact information distributed

## Compliance and Audit

### Internal Audit (Quarterly)
- [ ] Certificate usage reviewed
- [ ] Security practices verified
- [ ] Access control checked
- [ ] Backup integrity verified
- [ ] Documentation updated

### External Requirements
- [ ] Organizational security policies followed
- [ ] Industry compliance requirements met
- [ ] Audit trail maintained
- [ ] Incident response plan in place

## Notes

**Additional Information:**
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________

## Sign-Off

**Certificate Manager:** _______________
**Date:** _______________
**Next Review Date:** _______________

## Quick Reference

**Emergency Contacts:**
- CA Support: _______________
- IT Security: _______________
- Certificate Manager: _______________

**Key Files:**
- Certificate: _______________
- Config: scripts/certificate_config.bat
- Signing Script: scripts/sign_executable.bat
- Documentation: docs/CODE_SIGNING_GUIDE.md

**Quick Commands:**
```cmd
REM Sign executable
call scripts\certificate_config.bat
scripts\sign_executable.bat

REM Verify signature
signtool verify /pa dist\PrecipGen.exe

REM View certificate details
certmgr.msc
```

