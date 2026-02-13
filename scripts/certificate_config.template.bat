@echo off
REM PrecipGen Desktop - Certificate Configuration Template
REM Copy this file to certificate_config.bat and fill in your certificate details
REM DO NOT commit certificate_config.bat to version control!

REM ========================================
REM Certificate Configuration
REM ========================================

REM Option 1: Use certificate from Windows certificate store
REM Uncomment and set the certificate name as shown in certmgr.msc
REM set CERT_NAME=Your Certificate Name

REM Option 2: Use .pfx certificate file
REM Uncomment and set the path to your certificate file and password
REM set CERT_FILE=path\to\certificate.pfx
REM set CERT_PASSWORD=your_certificate_password

REM ========================================
REM Timestamp Server (Optional)
REM ========================================
REM Default: http://timestamp.digicert.com
REM Other options:
REM   - http://timestamp.sectigo.com
REM   - http://timestamp.globalsign.com
REM   - http://ts.ssl.com

REM set TIMESTAMP_SERVER=http://timestamp.digicert.com

REM ========================================
REM Usage
REM ========================================
REM After configuring, run the signing script:
REM   call scripts\certificate_config.bat
REM   scripts\sign_executable.bat

REM ========================================
REM Security Notes
REM ========================================
REM - Keep this file secure and never commit to version control
REM - Use strong passwords for certificate files
REM - Store certificate files in a secure location
REM - Consider using environment variables instead of hardcoding passwords
REM - For CI/CD, use secure secret management (Azure Key Vault, AWS Secrets Manager)
