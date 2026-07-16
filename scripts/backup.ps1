# Backup quotidien SGHI (PostgreSQL + media)
param(
    [string]$BackupDir = ".\backups",
    [string]$DbName = "sghi_db",
    [string]$DbUser = "postgres",
    [string]$DbHost = "localhost"
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$pgDump = "pg_dump"
$dumpFile = Join-Path $BackupDir "sghi_db_$timestamp.sql"
& $pgDump -h $DbHost -U $DbUser -d $DbName -F c -f $dumpFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "Backup BDD OK : $dumpFile"
} else {
    Write-Error "Echec backup BDD"
    exit 1
}

$mediaArchive = Join-Path $BackupDir "sghi_media_$timestamp.zip"
if (Test-Path ".\media") {
    Compress-Archive -Path ".\media\*" -DestinationPath $mediaArchive -Force
    Write-Host "Backup media OK : $mediaArchive"
}

Write-Host "Backup termine — conserver hors site (DRP)"
