import 'package:flutter/foundation.dart' show kIsWeb, defaultTargetPlatform, TargetPlatform;

class AppConfig {
  AppConfig._();

  static String get apiBaseUrl {
    const override = String.fromEnvironment('API_BASE_URL');
    if (override.isNotEmpty) return override;

    if (kIsWeb) {
      // Même hôte que la page (localhost ou 127.0.0.1) pour éviter les soucis CORS
      final host = Uri.base.host.isNotEmpty ? Uri.base.host : '127.0.0.1';
      return 'http://$host:8000/api/v1';
    }
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    return 'http://127.0.0.1:8000/api/v1';
  }

  static const String appName = 'SGHI';
  static const String appSubtitle = 'Mobile';
  static const String institution = 'CHU — Centre Hospitalier Universitaire';
  static const String tagline = 'Soins d\'excellence · Gestion intelligente';
}
