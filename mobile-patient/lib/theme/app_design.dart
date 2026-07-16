import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Design system SGHI Patient — niveau application professionnelle
class AppDesign {
  AppDesign._();

  // Couleurs institutionnelles
  static const Color navy = Color(0xFF0B1F3A);
  static const Color navyMid = Color(0xFF123456);
  static const Color teal = Color(0xFF0D9488);
  static const Color tealLight = Color(0xFF14B8A6);
  static const Color mint = Color(0xFF5EEAD4);
  static const Color surface = Color(0xFFF4F8FB);
  static const Color card = Colors.white;
  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textSecondary = Color(0xFF64748B);

  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF0B1F3A), Color(0xFF0F4C5C), Color(0xFF0D9488)],
  );

  /// Dégradé hero premium (navy → cyan → teal)
  static const LinearGradient heroPremiumGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0xFF071525),
      Color(0xFF0B2A4A),
      Color(0xFF0E7490),
      Color(0xFF0D9488),
    ],
    stops: [0.0, 0.35, 0.7, 1.0],
  );

  static const LinearGradient cardGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF0D9488), Color(0xFF0891B2)],
  );

  static const LinearGradient buttonShineGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF14B8A6), Color(0xFF0D9488), Color(0xFF0F766E)],
  );

  static const LinearGradient meshBackground = LinearGradient(
    begin: Alignment(-1, -1),
    end: Alignment(1, 1),
    colors: [Color(0xFFE0F2FE), Color(0xFFF0FDFA), Color(0xFFF8FAFC)],
  );

  /// Ombre douce diffuse (cartes)
  static List<BoxShadow> softShadow({Color? tint, double elevation = 1}) => [
        BoxShadow(
          color: (tint ?? navy).withValues(alpha: 0.06 * elevation),
          blurRadius: 24 * elevation,
          offset: Offset(0, 10 * elevation),
          spreadRadius: -2,
        ),
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.03),
          blurRadius: 8,
          offset: const Offset(0, 2),
        ),
      ];

  /// Ombre élevée (hover / focus)
  static List<BoxShadow> elevatedShadow({Color? tint}) => [
        BoxShadow(
          color: (tint ?? teal).withValues(alpha: 0.18),
          blurRadius: 32,
          offset: const Offset(0, 16),
          spreadRadius: -4,
        ),
        BoxShadow(
          color: navy.withValues(alpha: 0.08),
          blurRadius: 12,
          offset: const Offset(0, 4),
        ),
      ];

  static TextTheme textTheme(TextTheme base) {
    return GoogleFonts.plusJakartaSansTextTheme(base).copyWith(
      headlineLarge: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w800, color: textPrimary, letterSpacing: -1),
      headlineMedium: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w800, color: textPrimary, letterSpacing: -0.5),
      titleLarge: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w700, color: textPrimary),
      titleMedium: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w600, color: textPrimary),
      bodyLarge: GoogleFonts.plusJakartaSans(color: textSecondary, height: 1.5),
      bodyMedium: GoogleFonts.plusJakartaSans(color: textSecondary, height: 1.5),
      labelLarge: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w700),
    );
  }

  static ThemeData get theme {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: teal,
        primary: teal,
        secondary: navy,
        surface: surface,
        brightness: Brightness.light,
      ),
      scaffoldBackgroundColor: surface,
    );
    return base.copyWith(
      textTheme: textTheme(base.textTheme),
      appBarTheme: AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.white,
        titleTextStyle: GoogleFonts.plusJakartaSans(fontSize: 18, fontWeight: FontWeight.w700, color: Colors.white),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: card,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        shadowColor: navy.withValues(alpha: 0.08),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.grey.shade200)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.grey.shade200)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: teal, width: 2)),
        labelStyle: GoogleFonts.plusJakartaSans(color: textSecondary, fontWeight: FontWeight.w500),
        hintStyle: GoogleFonts.plusJakartaSans(color: Colors.grey.shade400),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 74,
        elevation: 0,
        backgroundColor: Colors.white,
        indicatorColor: teal.withValues(alpha: 0.12),
        labelTextStyle: WidgetStateProperty.resolveWith((s) => GoogleFonts.plusJakartaSans(
              fontSize: 11,
              fontWeight: s.contains(WidgetState.selected) ? FontWeight.w700 : FontWeight.w500,
              color: s.contains(WidgetState.selected) ? teal : textSecondary,
            )),
      ),
    );
  }

  static const LinearGradient heroOverlay = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0x990B1F3A), Color(0xCC0D9488)],
  );

  static BoxDecoration heroDecoration({String? imageUrl}) => BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: heroPremiumGradient,
        boxShadow: [
          BoxShadow(color: navy.withValues(alpha: 0.28), blurRadius: 36, offset: const Offset(0, 18), spreadRadius: -6),
          BoxShadow(color: teal.withValues(alpha: 0.15), blurRadius: 24, offset: const Offset(0, 8)),
        ],
      );

  static BoxDecoration gradientCardDecoration(Color accent) => BoxDecoration(
        color: accent.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(20),
        boxShadow: softShadow(tint: accent),
      );

  static BoxDecoration glassCard = BoxDecoration(
    color: Colors.white.withValues(alpha: 0.96),
    borderRadius: BorderRadius.circular(28),
    boxShadow: softShadow(elevation: 1.2),
  );
}
