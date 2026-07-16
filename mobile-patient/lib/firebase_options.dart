import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart' show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Configuration Firebase — remplacer via `flutterfire configure` ou les variables ci-dessous.
/// Tant que [isConfigured] est false, les push sont désactivés (l'app fonctionne normalement).
class DefaultFirebaseOptions {
  DefaultFirebaseOptions._();

  static const String _projectId = String.fromEnvironment(
    'FIREBASE_PROJECT_ID',
    defaultValue: 'sghi-patient-demo',
  );

  /// Passe à true après `flutterfire configure` ou si FIREBASE_PROJECT_ID réel est défini au build.
  static bool get isConfigured =>
      _projectId.isNotEmpty && _projectId != 'sghi-patient-demo';

  static FirebaseOptions get currentPlatform {
    if (kIsWeb) return web;
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      default:
        throw UnsupportedError('Push FCM non supporté sur cette plateforme.');
    }
  }

  // Placeholders — remplacés par flutterfire configure
  static const FirebaseOptions android = FirebaseOptions(
    apiKey: String.fromEnvironment('FIREBASE_ANDROID_API_KEY', defaultValue: 'REPLACE_ME'),
    appId: String.fromEnvironment('FIREBASE_ANDROID_APP_ID', defaultValue: '1:000000000000:android:0000000000000000000000'),
    messagingSenderId: String.fromEnvironment('FIREBASE_MESSAGING_SENDER_ID', defaultValue: '000000000000'),
    projectId: _projectId,
    storageBucket: String.fromEnvironment('FIREBASE_STORAGE_BUCKET', defaultValue: 'sghi-patient-demo.appspot.com'),
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: String.fromEnvironment('FIREBASE_IOS_API_KEY', defaultValue: 'REPLACE_ME'),
    appId: String.fromEnvironment('FIREBASE_IOS_APP_ID', defaultValue: '1:000000000000:ios:0000000000000000000000'),
    messagingSenderId: String.fromEnvironment('FIREBASE_MESSAGING_SENDER_ID', defaultValue: '000000000000'),
    projectId: _projectId,
    storageBucket: String.fromEnvironment('FIREBASE_STORAGE_BUCKET', defaultValue: 'sghi-patient-demo.appspot.com'),
    iosBundleId: 'com.sghi.patient.sghiPatient',
  );

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: String.fromEnvironment('FIREBASE_WEB_API_KEY', defaultValue: 'REPLACE_ME'),
    appId: String.fromEnvironment('FIREBASE_WEB_APP_ID', defaultValue: '1:000000000000:web:0000000000000000000000'),
    messagingSenderId: String.fromEnvironment('FIREBASE_MESSAGING_SENDER_ID', defaultValue: '000000000000'),
    projectId: _projectId,
    authDomain: String.fromEnvironment('FIREBASE_AUTH_DOMAIN', defaultValue: 'sghi-patient-demo.firebaseapp.com'),
    storageBucket: String.fromEnvironment('FIREBASE_STORAGE_BUCKET', defaultValue: 'sghi-patient-demo.appspot.com'),
  );
}
