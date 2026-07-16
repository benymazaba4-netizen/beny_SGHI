import 'package:flutter/material.dart';
import '../theme/app_design.dart';

/// Panneau décoratif sans image — dégradé médical + grande icône blanche.
/// Remplace tous les anciens visuels réseau (zéro requête HTTP, zéro 404).
class MedicalIconPanel extends StatelessWidget {
  const MedicalIconPanel({
    super.key,
    required this.icon,
    this.accent,
    this.iconSize = 34,
  });

  final IconData icon;
  final Color? accent;
  final double iconSize;

  @override
  Widget build(BuildContext context) {
    final c = accent ?? AppDesign.teal;
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            c,
            Color.lerp(c, AppDesign.navy, 0.45)!,
            Color.lerp(c, const Color(0xFF7DD3FC), 0.35)!,
          ],
        ),
      ),
      child: Stack(
        children: [
          // Cercles décoratifs subtils
          Positioned(
            right: -18,
            top: -18,
            child: Container(
              width: 90,
              height: 90,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white.withValues(alpha: 0.08),
              ),
            ),
          ),
          Positioned(
            left: -12,
            bottom: -20,
            child: Container(
              width: 70,
              height: 70,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white.withValues(alpha: 0.06),
              ),
            ),
          ),
          Center(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.18),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white24),
              ),
              child: Icon(icon, color: Colors.white, size: iconSize),
            ),
          ),
        ],
      ),
    );
  }
}

/// Wrapper hover web + scale press pour cartes cliquables.
class HoverScaleCard extends StatefulWidget {
  const HoverScaleCard({
    super.key,
    required this.child,
    this.onTap,
    this.hoverScale = 1.03,
    this.pressScale = 0.97,
    this.borderRadius = 22,
  });

  final Widget child;
  final VoidCallback? onTap;
  final double hoverScale;
  final double pressScale;
  final double borderRadius;

  @override
  State<HoverScaleCard> createState() => _HoverScaleCardState();
}

class _HoverScaleCardState extends State<HoverScaleCard> {
  bool _hovered = false;
  bool _pressed = false;

  double get _scale {
    if (_pressed) return widget.pressScale;
    if (_hovered) return widget.hoverScale;
    return 1.0;
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      cursor: widget.onTap != null ? SystemMouseCursors.click : SystemMouseCursors.basic,
      child: GestureDetector(
        onTap: widget.onTap,
        onTapDown: (_) => setState(() => _pressed = true),
        onTapUp: (_) => setState(() => _pressed = false),
        onTapCancel: () => setState(() => _pressed = false),
        child: AnimatedScale(
          scale: _scale,
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeOutCubic,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(widget.borderRadius),
              boxShadow: [
                BoxShadow(
                  color: AppDesign.navy.withValues(alpha: _hovered ? 0.16 : 0.08),
                  blurRadius: _hovered ? 28 : 18,
                  offset: Offset(0, _hovered ? 14 : 8),
                  spreadRadius: _hovered ? 1 : 0,
                ),
              ],
            ),
            child: widget.child,
          ),
        ),
      ),
    );
  }
}
