# Demarre un serveur SMTP local pour SGHI (Docker Mailpit ou Python)
$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "=== SGHI - SMTP local ===" -ForegroundColor Cyan

function Test-PortOpen($port) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient('127.0.0.1', $port)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}

if (Test-PortOpen 1025) {
    Write-Host "SMTP deja actif sur 127.0.0.1:1025" -ForegroundColor Green
    Write-Host "Mailpit web (si Docker) : http://127.0.0.1:8025" -ForegroundColor Green
    Write-Host "E-mails Python dev : $ProjectRoot\emails\outbox" -ForegroundColor Green
    exit 0
}

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    Write-Host "Demarrage Mailpit via Docker..." -ForegroundColor Yellow
    $existing = docker ps -a --filter "name=sghi-mailpit" --format "{{.Names}}" 2>$null
    if ($existing -eq "sghi-mailpit") {
        docker start sghi-mailpit | Out-Null
    } else {
        docker run -d --name sghi-mailpit -p 1025:1025 -p 8025:8025 --restart unless-stopped axllent/mailpit:latest | Out-Null
    }
    Start-Sleep -Seconds 2
    if (Test-PortOpen 1025) {
        Write-Host "Mailpit OK - http://127.0.0.1:8025" -ForegroundColor Green
        exit 0
    }
}

Write-Host "Docker indisponible - demarrage serveur SMTP Python..." -ForegroundColor Yellow
$python = "$ProjectRoot\venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

Start-Process -FilePath $python -ArgumentList "$PSScriptRoot\dev_smtp_server.py" -WindowStyle Minimized
Start-Sleep -Seconds 2

if (Test-PortOpen 1025) {
    Write-Host "SMTP Python OK sur 127.0.0.1:1025" -ForegroundColor Green
    Write-Host "E-mails dans : $ProjectRoot\emails\outbox" -ForegroundColor Green
} else {
    Write-Host "Echec demarrage SMTP. Installez Docker ou lancez manuellement :" -ForegroundColor Red
    Write-Host "  python scripts\dev_smtp_server.py" -ForegroundColor Yellow
    exit 1
}
