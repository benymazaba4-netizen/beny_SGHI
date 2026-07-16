import 'package:flutter/material.dart';

class UserAvatar extends StatelessWidget {
  const UserAvatar({
    super.key,
    required this.name,
    this.size = 40,
    this.photoUrl,
  });

  final String name;
  final double size;
  // Conservé pour compatibilité d'API mais volontairement ignoré :
  // aucune image réseau n'est chargée, on affiche toujours les initiales.
  final String? photoUrl;

  @override
  Widget build(BuildContext context) {
    return _initialsAvatar(_initials(name), _colorFromName(name));
  }

  Widget _initialsAvatar(String initials, Color color) {
    return CircleAvatar(
      radius: size / 2,
      backgroundColor: color,
      child: Text(
        initials,
        style: TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w700,
          fontSize: size * 0.34,
        ),
      ),
    );
  }

  String _initials(String value) {
    final parts = value.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first.substring(0, parts.first.length >= 2 ? 2 : 1).toUpperCase();
    return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
  }

  Color _colorFromName(String value) {
    var hash = 0;
    for (final code in value.codeUnits) {
      hash = code + ((hash << 5) - hash);
    }
    final hue = (hash.abs() % 360).toDouble();
    return HSLColor.fromAHSL(1, hue, 0.55, 0.45).toColor();
  }
}
