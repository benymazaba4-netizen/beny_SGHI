# Configure SGHI pour envoyer de VRAIS e-mails via Gmail (boite mail reelle).
# Necessite un "mot de passe d'application" Google (pas le mot de passe du compte).
# Google : Compte > Securite > Validation en 2 etapes > Mots de passe des applications

param(
    [Parameter(Mandatory = $true)]
    [string]$GmailAddress,

    [Parameter(Mandatory = $true)]
    [string]$AppPassword
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$EnvFile = Join-Path $ProjectRoot ".env"

if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $ProjectRoot ".env.example") $EnvFile
}

$content = Get-Content $EnvFile -Raw

function Set-EnvLine($name, $value) {
    script:param($name, $value)
    $pattern = "(?m)^$name=.*$"
    $line = "$name=$value"
    if ($content -match $pattern) {
        $script:content = $content -replace $pattern, $line
    } else {
        $script:content = $content.TrimEnd() + "`n$line`n"
    }
}

Set-EnvLine "EMAIL_BACKEND" "django.core.mail.backends.smtp.EmailBackend"
Set-EnvLine "EMAIL_HOST" "smtp.gmail.com"
Set-EnvLine "EMAIL_PORT" "587"
Set-EnvLine "EMAIL_USE_TLS" "True"
Set-EnvLine "EMAIL_USE_SSL" "False"
Set-EnvLine "EMAIL_HOST_USER" $GmailAddress
Set-EnvLine "EMAIL_HOST_PASSWORD" $AppPassword
Set-EnvLine "DEFAULT_FROM_EMAIL" "SGHI <$GmailAddress>"
Set-EnvLine "STAFF_OTP_EMAIL" $GmailAddress

Set-Content -Path $EnvFile -Value $content.TrimEnd() -Encoding UTF8

Write-Host "Gmail SMTP configure dans .env" -ForegroundColor Green
Write-Host "Redemarrez Django puis testez :" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\python.exe manage.py test_email --to $GmailAddress" -ForegroundColor Cyan
