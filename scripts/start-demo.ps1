# Lancer la démo SGHI (Windows PowerShell)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

Write-Host "=== SGHI - Démarrage démo ===" -ForegroundColor Cyan

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Création du venv..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\pip.exe install -r requirements.txt
}

Write-Host "Migrations + seed + CIM-10..." -ForegroundColor Yellow
.\venv\Scripts\pip.exe install -q python-dotenv 2>$null
if (-not (Test-Path ".\.env")) {
    Copy-Item ".\.env.example" ".\.env"
    Write-Host "Fichier .env cree depuis .env.example" -ForegroundColor Yellow
}

Write-Host "Demarrage Mailpit (SMTP local)..." -ForegroundColor Yellow
try {
    & "$PSScriptRoot\start-mailpit.ps1"
} catch {
    Write-Host "Mailpit non demarre (Docker indisponible ?). Configurez Gmail dans .env" -ForegroundColor Yellow
}

.\venv\Scripts\python.exe manage.py migrate --noinput
.\venv\Scripts\python.exe manage.py load_cim10
.\venv\Scripts\python.exe manage.py seed_demo_users

Write-Host ""
Write-Host "Backend : http://127.0.0.1:8000/api/v1/docs" -ForegroundColor Green
Write-Host "Boite mail (Mailpit) : http://127.0.0.1:8025" -ForegroundColor Green
Write-Host "Test e-mail : .\venv\Scripts\python.exe manage.py test_email --to vous@example.com" -ForegroundColor Green
Write-Host "Mot de passe démo : Demo2026!" -ForegroundColor Green
Write-Host ""
Write-Host "Lancez le frontend dans un autre terminal :" -ForegroundColor Yellow
Write-Host "  cd frontend-web; npm run dev" -ForegroundColor White
Write-Host ""

.\venv\Scripts\python.exe manage.py runserver
