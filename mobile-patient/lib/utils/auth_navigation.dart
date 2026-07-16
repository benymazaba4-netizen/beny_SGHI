import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/push_service.dart';

/// Rôles autorisés sur l'application mobile SGHI.
class AppRoles {
  AppRoles._();

  static const patient = 'PATIENT';
  static const medecin = 'MEDECIN';
  static const secretaire = 'SECRETAIRE';

  static const allowed = {patient, medecin, secretaire};

  static String label(String? role) {
    switch (role) {
      case medecin:
        return 'Médecin';
      case secretaire:
        return 'Secrétaire';
      case patient:
        return 'Patient';
      default:
        return 'Utilisateur';
    }
  }

  static String? homeRoute(String? role) {
    if (role == patient) return '/home';
    if (role == medecin || role == secretaire) return '/staff';
    return null;
  }

  static bool isMobileRole(String? role) => role != null && allowed.contains(role);
}

class AuthNavigation {
  static Future<void> goAfterLogin(BuildContext context, Map<String, dynamic>? user) async {
    final role = user?['role']?.toString();
    final route = AppRoles.homeRoute(role);

    if (route == null) {
      await ApiService().logout();
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Ce rôle est réservé au portail web. Utilisez patient, medecin ou secretaire.'),
        ),
      );
      Navigator.pushReplacementNamed(context, '/login');
      return;
    }

    if (role == AppRoles.patient) {
      await PushNotificationService.instance.registerAfterLogin();
    }

    if (!context.mounted) return;
    if (route == '/staff') {
      Navigator.pushReplacementNamed(context, route, arguments: role);
    } else {
      Navigator.pushReplacementNamed(context, route);
    }
  }
}
