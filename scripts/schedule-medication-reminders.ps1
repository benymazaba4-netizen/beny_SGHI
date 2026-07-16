# Planification rappels médicamenteux (Windows)
# À exécuter 2× par jour via Planificateur de tâches Windows

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& "$ProjectRoot\venv\Scripts\python.exe" manage.py send_medication_reminders
