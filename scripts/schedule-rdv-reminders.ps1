# Planifie l'envoi des rappels RDV (toutes les heures) via le Planificateur de taches Windows
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

$TaskName = "SGHI-RDV-Reminders"
$Action = New-ScheduledTaskAction -Execute $Python -Argument "manage.py send_rdv_reminders" -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null

Write-Host "Tache planifiee : $TaskName (toutes les heures)" -ForegroundColor Green
Write-Host "Test manuel : $Python manage.py send_rdv_reminders" -ForegroundColor Yellow
