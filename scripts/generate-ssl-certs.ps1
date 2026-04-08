# Generate self-signed SSL certificates for development (Windows)

$ErrorActionPreference = "Stop"

$SSL_DIR = "nginx/ssl"
$CERT_FILE = "$SSL_DIR/cert.pem"
$KEY_FILE = "$SSL_DIR/key.pem"

Write-Host "Generating self-signed SSL certificates for development..." -ForegroundColor Green

# Create SSL directory if it doesn't exist
if (-not (Test-Path $SSL_DIR)) {
    New-Item -ItemType Directory -Path $SSL_DIR -Force | Out-Null
}

# Generate self-signed certificate using OpenSSL (requires OpenSSL to be installed)
# Alternative: Use New-SelfSignedCertificate for Windows
try {
    # Try OpenSSL first
    & openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
        -keyout $KEY_FILE `
        -out $CERT_FILE `
        -subj "/C=US/ST=State/L=City/O=AI Research Copilot/CN=localhost"
    
    Write-Host "SSL certificates generated successfully using OpenSSL!" -ForegroundColor Green
} catch {
    Write-Host "OpenSSL not found. Using Windows certificate generation..." -ForegroundColor Yellow
    
    # Fallback to Windows certificate generation
    $cert = New-SelfSignedCertificate `
        -DnsName "localhost" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddYears(1) `
        -KeyAlgorithm RSA `
        -KeyLength 2048
    
    # Export certificate
    $certPath = "Cert:\CurrentUser\My\$($cert.Thumbprint)"
    Export-Certificate -Cert $certPath -FilePath $CERT_FILE -Type CERT
    
    # Export private key (requires password)
    $password = ConvertTo-SecureString -String "dev" -Force -AsPlainText
    Export-PfxCertificate -Cert $certPath -FilePath "$SSL_DIR/cert.pfx" -Password $password
    
    Write-Host "SSL certificates generated successfully using Windows!" -ForegroundColor Green
    Write-Host "Note: You may need to convert the certificate format for Nginx." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Certificate: $CERT_FILE" -ForegroundColor Cyan
Write-Host "Private Key: $KEY_FILE" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: These are self-signed certificates for development only." -ForegroundColor Yellow
Write-Host "For production, use certificates from a trusted CA (Let's Encrypt, etc.)" -ForegroundColor Yellow
