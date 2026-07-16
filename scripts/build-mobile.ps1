# Build release mobile SGHI Patient
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location "$ProjectRoot\mobile-patient"

Write-Host "=== SGHI — Build mobile ===" -ForegroundColor Cyan
flutter pub get

Write-Host ""
Write-Host "Build APK Android..." -ForegroundColor Yellow
flutter build apk --release
Write-Host "APK : build\app\outputs\flutter-apk\app-release.apk" -ForegroundColor Green

Write-Host ""
Write-Host "Build Web (PWA)..." -ForegroundColor Yellow
flutter build web --release
Write-Host "Web : build\web\" -ForegroundColor Green

Write-Host ""
Write-Host "Pour iOS (macOS requis) : flutter build ios --release" -ForegroundColor Yellow
