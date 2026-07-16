import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_design.dart';
import 'network_image_safe.dart';

class PortalServiceTile extends StatefulWidget {
  const PortalServiceTile({
    super.key,
    required this.title,
    required this.subtitle,
    required this.icon,
    this.accent,
    this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color? accent;
  final VoidCallback? onTap;

  @override
  State<PortalServiceTile> createState() => _PortalServiceTileState();
}

class _PortalServiceTileState extends State<PortalServiceTile> {
  bool _hovered = false;
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final c = widget.accent ?? Theme.of(context).colorScheme.primary;
    final scale = _pressed ? 0.97 : (_hovered ? 1.03 : 1.0);

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTapDown: (_) => setState(() => _pressed = true),
        onTapUp: (_) {
          setState(() => _pressed = false);
          HapticFeedback.selectionClick();
          widget.onTap?.call();
        },
        onTapCancel: () => setState(() => _pressed = false),
        child: AnimatedScale(
          scale: scale,
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeOutCubic,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(22),
              boxShadow: _hovered ? AppDesign.elevatedShadow(tint: c) : AppDesign.softShadow(tint: c),
            ),
            clipBehavior: Clip.antiAlias,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                SizedBox(
                  height: 120,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      MedicalIconPanel(icon: widget.icon, accent: c, iconSize: 36),
                      Positioned(
                        left: 12,
                        bottom: 10,
                        right: 12,
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(
                                widget.title,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w800,
                                  fontSize: 14,
                                  shadows: [Shadow(color: Colors.black38, blurRadius: 6)],
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            Icon(Icons.arrow_forward_ios_rounded, color: Colors.white.withValues(alpha: 0.8), size: 12),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
                  child: Text(
                    widget.subtitle,
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 12, height: 1.35, fontWeight: FontWeight.w500),
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
