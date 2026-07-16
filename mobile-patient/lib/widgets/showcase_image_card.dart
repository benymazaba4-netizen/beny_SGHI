import 'package:flutter/material.dart';
import '../theme/app_design.dart';
import 'network_image_safe.dart';

/// Carte galerie vitrine — dégradé coloré + icône, avec légende et hover web.
class ShowcaseImageCard extends StatelessWidget {
  const ShowcaseImageCard({
    super.key,
    required this.icon,
    required this.label,
    this.accent,
    this.width = 200,
    this.height = 260,
    this.onTap,
  });

  final IconData icon;
  final String label;
  final Color? accent;
  final double width;
  final double height;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 14),
      child: HoverScaleCard(
        onTap: onTap,
        borderRadius: 22,
        child: SizedBox(
          width: width,
          height: height,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(22),
            child: Stack(
              fit: StackFit.expand,
              children: [
                MedicalIconPanel(icon: icon, accent: accent ?? AppDesign.teal, iconSize: 44),
                Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Colors.transparent,
                        Colors.transparent,
                        Colors.black.withValues(alpha: 0.45),
                      ],
                      stops: const [0.0, 0.6, 1.0],
                    ),
                  ),
                ),
                Positioned(
                  left: 14,
                  right: 14,
                  bottom: 14,
                  child: Text(
                    label,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                      fontSize: 14,
                      height: 1.25,
                      shadows: [Shadow(color: Colors.black45, blurRadius: 8)],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Tuile bento pour la galerie mobile — dégradé + icône.
class ShowcaseBentoTile extends StatelessWidget {
  const ShowcaseBentoTile({
    super.key,
    required this.icon,
    required this.label,
    this.accent,
    this.flex = 1,
    this.onTap,
  });

  final IconData icon;
  final String label;
  final Color? accent;
  final int flex;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      flex: flex,
      child: Padding(
        padding: const EdgeInsets.all(5),
        child: HoverScaleCard(
          onTap: onTap,
          hoverScale: 1.04,
          borderRadius: 18,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(18),
            child: Stack(
              fit: StackFit.expand,
              children: [
                MedicalIconPanel(icon: icon, accent: accent ?? AppDesign.navyMid, iconSize: 28),
                Positioned(
                  left: 10,
                  right: 10,
                  bottom: 10,
                  child: Text(
                    label,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                      fontSize: 11,
                      shadows: [Shadow(color: Colors.black38, blurRadius: 6)],
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
