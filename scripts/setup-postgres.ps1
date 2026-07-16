# Configuration PostgreSQL pour SGHI (Docker ou instance locale)
param(
    [switch]$SkipDocker,
    [switch]$SkipSeed,
    [string]$DbName = "sghi_db",
    [string]$DbUser = "postgres",
    [string]$DbPassword = "postgres",
    [string]$DbHost = "localhost",
    [string]$DbPort = "5432"
)

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

function Set-EnvDatabase {
    param(
        [string]$Engine,
        [string]$Name,
        [string]$User,
        [string]$Password,
        [string]$DatabaseHost,
        [string]$Port
    )
    if (-not (Test-Path ".\.env")) {
        Copy-Item ".\.env.example" ".\.env"
    }
    $lines = Get-Content ".\.env" -Encoding UTF8
    $keys = @{
        "DB_ENGINE"   = $Engine
        "DB_NAME"     = $Name
        "DB_USER"     = $User
        "DB_PASSWORD" = $Password
        "DB_HOST"     = $DatabaseHost
        "DB_PORT"     = $Port
    }
    $seen = @{}
    $out = foreach ($line in $lines) {
        if ($line -match '^\s*#?\s*(DB_ENGINE|DB_NAME|DB_USER|DB_PASSWORD|DB_HOST|DB_PORT)\s*=') {
            $key = $Matches[1]
            if (-not $seen.ContainsKey($key)) {
                $seen[$key] = $true
                "$key=$($keys[$key])"
            }
        } else {
            $line
        }
    }
    foreach ($key in $keys.Keys) {
        if (-not $seen.ContainsKey($key)) {
            $out += "$key=$($keys[$key])"
        }
    }
    $out | Set-Content ".\.env" -Encoding UTF8
}

Write-Host "=== SGHI - Configuration PostgreSQL ===" -ForegroundColor Cyan

if (-not $SkipDocker) {
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        Write-Host "Demarrage du conteneur PostgreSQL (docker compose)..." -ForegroundColor Yellow
        docker compose up -d db 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "docker compose a echoue. Verifiez que Docker Desktop est demarre."
        } else {
            $deadline = (Get-Date).AddMinutes(2)
            while ((Get-Date) -lt $deadline) {
                if (Test-TcpPort -HostName $DbHost -Port ([int]$DbPort)) {
                    Write-Host "PostgreSQL accessible sur ${DbHost}:${DbPort}" -ForegroundColor Green
                    break
                }
                Start-Sleep -Seconds 2
            }
        }
    } else {
        Write-Warning "Docker introuvable - utilisation d'une instance PostgreSQL locale (port $DbPort)."
    }
}

if (-not (Test-TcpPort -HostName $DbHost -Port ([int]$DbPort))) {
    Write-Error @"
PostgreSQL n'est pas accessible sur ${DbHost}:${DbPort}.

Options :
  1. Demarrer Docker Desktop puis relancer : .\scripts\setup-postgres.ps1
  2. Installer PostgreSQL 16+ sur Windows et creer la base '$DbName'
  3. Lancer uniquement la BDD : docker compose up -d db
"@
}

function Invoke-ManageStep {
    param([string]$Label, [string[]]$Args)
    Write-Host $Label -ForegroundColor Yellow
    & .\venv\Scripts\python.exe manage.py @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Echec : manage.py $($Args -join ' ')"
    }
}

Write-Host "Mise a jour de .env (DB_ENGINE=postgresql)..." -ForegroundColor Yellow
Set-EnvDatabase -Engine "postgresql" -Name $DbName -User $DbUser -Password $DbPassword -DatabaseHost $DbHost -Port $DbPort

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    python -m venv venv
    .\venv\Scripts\pip.exe install -r requirements.txt
}

Write-Host "Creation de la base si necessaire..." -ForegroundColor Yellow
$env:DB_NAME = $DbName
$env:DB_USER = $DbUser
$env:DB_PASSWORD = $DbPassword
$env:DB_HOST = $DbHost
$env:DB_PORT = $DbPort
& .\venv\Scripts\python.exe .\scripts\ensure_postgres_db.py
if ($LASTEXITCODE -ne 0) { throw "Echec creation base PostgreSQL" }

Write-Host "Verification psycopg2..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -c "import psycopg2; print('psycopg2 OK')"
if ($LASTEXITCODE -ne 0) { throw "psycopg2 indisponible" }

Invoke-ManageStep "Migrations Django..." @("migrate", "--noinput")
Invoke-ManageStep "Chargement CIM-10..." @("load_cim10")

if (-not $SkipSeed) {
    Invoke-ManageStep "Comptes demo (seed_demo_users)..." @("seed_demo_users")
}

Write-Host ""
Write-Host "PostgreSQL pret !" -ForegroundColor Green
Write-Host "  Base   : $DbName @ ${DbHost}:${DbPort}" -ForegroundColor White
Write-Host "  Compte : $DbUser" -ForegroundColor White
Write-Host ""
Write-Host "Lancer l'API : .\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000" -ForegroundColor Green
