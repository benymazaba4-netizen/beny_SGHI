# Prepare tout SGHI (SMTP + migrations + seed) sans lancer le serveur
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

function Test-TcpPort {
    param([string]$HostName, [int]$Port)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        $ok = $async.AsyncWaitHandle.WaitOne(2000, $false)
        if ($ok) { $client.EndConnect($async) }
        $client.Close()
        return $ok
    } catch {
        return $false
    }
}

Write-Host "=== SGHI — Preparation complete ===" -ForegroundColor Cyan

& "$PSScriptRoot\start-mailpit.ps1"

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    python -m venv venv
    .\venv\Scripts\pip.exe install -r requirements.txt
}

.\venv\Scripts\pip.exe install -q python-dotenv aiosmtpd 2>$null
if (-not (Test-Path ".\.env")) { Copy-Item ".\.env.example" ".\.env" }

$dbEngine = (Get-Content ".\.env" -Encoding UTF8 | Where-Object { $_ -match '^\s*DB_ENGINE\s*=\s*(\S+)' } | ForEach-Object { $Matches[1] }) | Select-Object -First 1
if ($dbEngine -eq 'postgresql') {
    if (-not (Test-TcpPort -HostName 'localhost' -Port 5432)) {
        Write-Host "PostgreSQL non detecte — lancement via setup-postgres.ps1..." -ForegroundColor Yellow
        & "$PSScriptRoot\setup-postgres.ps1" -SkipSeed
    }
}

.\venv\Scripts\python.exe manage.py migrate --noinput
.\venv\Scripts\python.exe manage.py load_cim10
.\venv\Scripts\python.exe manage.py seed_demo_users

Write-Host ""
Write-Host "Pret ! Ouvrez 3 terminaux :" -ForegroundColor Green
Write-Host "  1. .\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000" -ForegroundColor White
Write-Host "  2. cd frontend-web; npm run dev" -ForegroundColor White
Write-Host "  3. cd mobile-patient; flutter run -d chrome --web-port=5180" -ForegroundColor White
Write-Host ""
Write-Host "Compte demo : patient / Demo2026!" -ForegroundColor Green
Write-Host "Mailpit : http://127.0.0.1:8025" -ForegroundColor Green
