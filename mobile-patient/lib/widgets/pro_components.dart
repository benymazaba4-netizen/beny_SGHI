import 'package:flutter/material.dart';
import '../theme/app_design.dart';
class ProButton extends StatefulWidget {
  const ProButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.loading = false,
    this.icon,
    this.outlined = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool loading;
  final IconData? icon;
  final bool outlined;

  @override
  State<ProButton> createState() => _ProButtonState();
}

class _ProButtonState extends State<ProButton> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    if (widget.outlined) {
      return MouseRegion(
        onEnter: (_) => setState(() => _hovered = true),
        onExit: (_) => setState(() => _hovered = false),
        cursor: SystemMouseCursors.click,
        child: AnimatedScale(
          scale: _hovered ? 1.02 : 1.0,
          duration: const Duration(milliseconds: 160),
          child: SizedBox(
            width: double.infinity,
            height: 54,
            child: OutlinedButton.icon(
              onPressed: widget.loading ? null : widget.onPressed,
              icon: Icon(widget.icon ?? Icons.arrow_forward_rounded, size: 20),
              label: Text(widget.label),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppDesign.teal,
                backgroundColor: _hovered ? AppDesign.teal.withValues(alpha: 0.06) : null,
                side: BorderSide(color: AppDesign.teal.withValues(alpha: _hovered ? 0.8 : 0.5), width: 1.5),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
              ),
            ),
          ),
        ),
      );
    }

    final enabled = widget.onPressed != null && !widget.loading;
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      cursor: enabled ? SystemMouseCursors.click : SystemMouseCursors.basic,
      child: AnimatedScale(
        scale: _hovered && enabled ? 1.02 : 1.0,
        duration: const Duration(milliseconds: 160),
        child: SizedBox(
          width: double.infinity,
          height: 54,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              gradient: enabled ? AppDesign.buttonShineGradient : null,
              color: enabled ? null : Colors.grey.shade300,
              borderRadius: BorderRadius.circular(16),
              boxShadow: enabled
                  ? [
                      BoxShadow(
                        color: AppDesign.teal.withValues(alpha: _hovered ? 0.5 : 0.35),
                        blurRadius: _hovered ? 22 : 16,
                        offset: Offset(0, _hovered ? 10 : 6),
                      ),
                    ]
                  : null,
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: widget.loading ? null : widget.onPressed,
                borderRadius: BorderRadius.circular(16),
                child: Center(
                  child: widget.loading
                      ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white))
                      : Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (widget.icon != null) ...[Icon(widget.icon, color: Colors.white, size: 20), const SizedBox(width: 10)],
                            Text(widget.label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                          ],
                        ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class ProLogo extends StatelessWidget {
  const ProLogo({super.key, this.size = 72});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        gradient: AppDesign.cardGradient,
        borderRadius: BorderRadius.circular(size * 0.28),
        boxShadow: [BoxShadow(color: AppDesign.teal.withValues(alpha: 0.45), blurRadius: 20, offset: const Offset(0, 8))],
      ),
      child: const Icon(Icons.local_hospital_rounded, color: Colors.white, size: 36),
    );
  }
}

class ProField extends StatelessWidget {
  const ProField({
    super.key,
    required this.controller,
    required this.label,
    this.obscure = false,
    this.icon,
    this.onSubmitted,
    this.keyboardType,
  });

  final TextEditingController controller;
  final String label;
  final bool obscure;
  final IconData? icon;
  final VoidCallback? onSubmitted;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      keyboardType: keyboardType,
      textInputAction: obscure ? TextInputAction.done : TextInputAction.next,
      onSubmitted: onSubmitted != null ? (_) => onSubmitted!() : null,
      style: const TextStyle(fontWeight: FontWeight.w600, color: AppDesign.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon ?? Icons.edit_outlined, color: AppDesign.teal, size: 22),
      ),
    );
  }
}

class ProSectionHeader extends StatelessWidget {
  const ProSectionHeader({super.key, required this.title, this.subtitle});

  final String title;
  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          if (subtitle != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(subtitle!, style: Theme.of(context).textTheme.bodyMedium),
            ),
        ],
      ),
    );
  }
}

class ProQuickChip extends StatelessWidget {
  const ProQuickChip({
    super.key,
    required this.icon,
    required this.label,
    required this.color,
    this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          width: 92,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: color.withValues(alpha: 0.15)),
            boxShadow: [BoxShadow(color: color.withValues(alpha: 0.08), blurRadius: 16, offset: const Offset(0, 6))],
          ),
          child: Column(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [color.withValues(alpha: 0.15), color.withValues(alpha: 0.05)]),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(icon, color: color, size: 22),
              ),
              const SizedBox(height: 8),
              Text(label, textAlign: TextAlign.center, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color.withValues(alpha: 0.9))),
            ],
          ),
        ),
      ),
    );
  }
}

class ProStatCard extends StatelessWidget {
  const ProStatCard({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    this.color,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final c = color ?? AppDesign.teal;
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.06), blurRadius: 20, offset: const Offset(0, 10))],
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Bandeau dégradé coloré avec icône (remplace l'ancienne image)
          SizedBox(
            height: 58,
            child: Stack(
              fit: StackFit.expand,
              children: [
                DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [c, Color.lerp(c, AppDesign.navy, 0.35)!],
                    ),
                  ),
                ),
                Positioned(
                  right: -8,
                  top: -12,
                  child: Container(
                    width: 60,
                    height: 60,
                    decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withValues(alpha: 0.12)),
                  ),
                ),
                Positioned(right: 12, bottom: 8, child: Icon(icon, color: Colors.white, size: 24)),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppDesign.textSecondary, letterSpacing: 0.3)),
                const SizedBox(height: 4),
                Text(value, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: AppDesign.textPrimary, height: 1)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class ProGlassCard extends StatelessWidget {
  const ProGlassCard({super.key, required this.child, this.padding = const EdgeInsets.all(20)});

  final Widget child;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: AppDesign.glassCard,
      child: child,
    );
  }
}

class ProErrorBanner extends StatelessWidget {
  const ProErrorBanner({super.key, required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFFECACA)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline_rounded, color: Color(0xFFDC2626), size: 20),
          const SizedBox(width: 10),
          Expanded(child: Text(message, style: const TextStyle(color: Color(0xFFB91C1C), fontSize: 13, height: 1.4))),
        ],
      ),
    );
  }
}

class ProStatusChip extends StatelessWidget {
  const ProStatusChip({super.key, required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color)),
    );
  }
}

class ProFab extends StatelessWidget {
  const ProFab({super.key, required this.label, required this.icon, required this.onPressed});

  final String label;
  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 0,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(20),
        child: Ink(
          decoration: BoxDecoration(
            gradient: AppDesign.cardGradient,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [BoxShadow(color: AppDesign.teal.withValues(alpha: 0.4), blurRadius: 16, offset: const Offset(0, 6))],
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, color: Colors.white, size: 22),
                const SizedBox(width: 8),
                Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class ProHeroSliverAppBar extends StatelessWidget {
  const ProHeroSliverAppBar({super.key, required this.title, this.icon = Icons.local_hospital_rounded});

  final String title;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return SliverAppBar(
      expandedHeight: 160,
      pinned: true,
      flexibleSpace: FlexibleSpaceBar(
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        background: Stack(
          fit: StackFit.expand,
          children: [
            const DecoratedBox(decoration: BoxDecoration(gradient: AppDesign.heroPremiumGradient)),
            Positioned(
              right: -20,
              top: -20,
              child: Container(
                width: 140,
                height: 140,
                decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withValues(alpha: 0.08)),
              ),
            ),
            Positioned(
              right: 24,
              bottom: 40,
              child: Icon(icon, color: Colors.white.withValues(alpha: 0.22), size: 72),
            ),
            const DecoratedBox(decoration: BoxDecoration(gradient: AppDesign.heroOverlay)),
          ],
        ),
      ),
    );
  }
}
