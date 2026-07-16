# Configuration Firebase SGHI Patient
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location "$ProjectRoot\mobile-patient"

Write-Host "=== SGHI — Configuration Firebase (FCM) ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Creez un projet sur https://console.firebase.google.com" -ForegroundColor Yellow
Write-Host "2. Ajoutez une app Android (com.sghi.patient.sghi_patient)" -ForegroundColor Yellow
Write-Host "3. Ajoutez une app iOS (com.sghi.patient.sghiPatient)" -ForegroundColor Yellow
Write-Host "4. Installez FlutterFire CLI et configurez :" -ForegroundColor Yellow
Write-Host ""
Write-Host "   dart pub global activate flutterfire_cli" -ForegroundColor White
Write-Host "   flutterfire configure --project=VOTRE_PROJECT_ID" -ForegroundColor White
Write-Host ""
Write-Host "5. Copiez la cle serveur FCM dans .env backend :" -ForegroundColor Yellow
Write-Host "   FCM_SERVER_KEY=votre_cle_legacy_ou_http_v1" -ForegroundColor White
Write-Host ""
Write-Host "6. Test push :" -ForegroundColor Yellow
Write-Host "   python manage.py send_test_push --username patient" -ForegroundColor White
Write-Host ""

if (Get-Command flutterfire -ErrorAction SilentlyContinue) {
    Write-Host "FlutterFire detecte — lancement de configure..." -ForegroundColor Green
    flutterfire configure
} else {
    Write-Host "FlutterFire non installe. Executez les commandes ci-dessus." -ForegroundColor Yellow
}
