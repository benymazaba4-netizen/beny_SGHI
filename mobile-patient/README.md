# SGHI Patient — Application mobile Flutter

Application mobile **patient** pour l'ERP SGHI (consultations, labo, RDV, messagerie, factures PDF, push FCM).

## Prérequis

- Flutter SDK 3.2+
- Backend Django sur `http://127.0.0.1:8000`
- Firebase (optionnel, pour push Android/iOS) : `..\scripts\setup-firebase.ps1`

## Installation

```powershell
cd mobile-patient
flutter pub get
```

## Lancer

```powershell
# Web PWA (recommandé Windows)
flutter run -d chrome --web-port=5180

# Android émulateur
flutter run -d android

# iOS simulateur (macOS)
flutter run -d ios

# URL API personnalisée
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1
```

## Backend + démo

```powershell
cd ..
.\scripts\start-all.ps1
# Puis dans un terminal :
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

**Compte démo** : `patient` / `Demo2026!`

## Push FCM (Android / iOS)

1. `..\scripts\setup-firebase.ps1` ou `flutterfire configure`
2. Copier `google-services.json` → `android/app/`
3. Copier `GoogleService-Info.plist` → `ios/Runner/`
4. Backend `.env` : `FCM_SERVER_KEY=votre_cle`
5. Test : `python manage.py send_test_push --username patient`

Sans Firebase configuré, l'app fonctionne normalement (notifications in-app uniquement).

## Build release

```powershell
..\scripts\build-mobile.ps1
# ou manuellement :
flutter build apk --release
flutter build web --release
flutter build ios --release   # macOS + Xcode
```

| Plateforme | Sortie |
|------------|--------|
| Android | `build/app/outputs/flutter-apk/app-release.apk` |
| Web PWA | `build/web/` |
| iOS | `build/ios/` (archive Xcode) |

## Configuration API

| Plateforme | URL par défaut |
|------------|----------------|
| Web / Windows / iOS sim | `http://127.0.0.1:8000/api/v1` (ou hôte page web) |
| Android émulateur | `http://10.0.2.2:8000/api/v1` |
| Appareil physique | `--dart-define=API_BASE_URL=http://<IP_PC>:8000/api/v1` |

## Fonctionnalités

| Écran | Description |
|-------|-------------|
| **Portail** | Accueil public, services, login/inscription |
| **Connexion** | JWT + MFA, push FCM après login |
| **Accueil** | Statistiques parcours de soins |
| **Santé** | Dossier, labo PDF, ordonnances, soins |
| **RDV** | Liste, création, annulation |
| **Messages** | Chat médecin ↔ patient |
| **Profil** | Factures PDF, notifications, déconnexion |

## PWA

Installable depuis Chrome. Manifest brandé SGHI (`web/manifest.json`).
