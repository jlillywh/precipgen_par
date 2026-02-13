# PrecipGen Desktop - Certificate Configuration Template (PowerShell)
# Copy this file to certificate_config.ps1 and fill in your certificate details
# DO NOT commit certificate_config.ps1 to version control!

# ========================================
# Certificate Configuration
# ========================================

# Option 1: Use certificate from Windows certificate store
# Uncomment and set the certificate name as shown in certmgr.msc
# $env:CERT_NAME = "Your Certificate Name"

# Option 2: Use .pfx certificate file
# Uncomment and set the path to your certificate file and password
# $env:CERT_FILE = "path\to\certificate.pfx"
# $env:CERT_PASSWORD = "your_certificate_password"

# ========================================
# Timestamp Server (Optional)
# ========================================
# Default: http://timestamp.digicert.com
# Other options:
#   - http://timestamp.sectigo.com
#   - http://timestamp.globalsign.com
#   - http://ts.ssl.com

# $env:TIMESTAMP_SERVER = "http://timestamp.digicert.com"

# ========================================
# Usage
# ========================================
# After configuring, run the signing script:
#   . .\scripts\certificate_config.ps1
#   .\scripts\sign_executable.ps1

# ========================================
# Security Notes
# ========================================
# - Keep this file secure and never commit to version control
# - Use strong passwords for certificate files
# - Store certificate files in a secure location
# - Consider using SecureString for passwords in production
# - For CI/CD, use secure secret management (Azure Key Vault, AWS Secrets Manager)

# ========================================
# Example: Using SecureString for Password
# ========================================
# $securePassword = ConvertTo-SecureString "your_password" -AsPlainText -Force
# $env:CERT_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
#     [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
# )
