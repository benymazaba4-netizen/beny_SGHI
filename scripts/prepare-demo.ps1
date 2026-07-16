# Prépare l'environnement de démonstration SGHI (à lancer avant la démo)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== SGHI — Preparation demo ===" -ForegroundColor Cyan

& .\venv\Scripts\python.exe manage.py migrate --noinput
& .\venv\Scripts\python.exe manage.py seed_demo_users

Write-Host ""
Write-Host "Pret ! Ouvrez :" -ForegroundColor Green
Write-Host "  API   : http://127.0.0.1:8000/api/v1/docs"
Write-Host "  Web   : http://localhost:5173"
Write-Host "  Mobile: http://localhost:5180 (flutter run -d chrome --web-port=5180)"
Write-Host ""
Write-Host "Mot de passe : Demo2026!  |  OTP -> benymazaba4@gmail.com"
Write-Host "Guide pas-a-pas : DEMO.md"
Write-Host ""
