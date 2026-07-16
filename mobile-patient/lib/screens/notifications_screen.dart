import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_design.dart';
import '../widgets/empty_placeholder.dart';
class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final _api = ApiService();
  List<dynamic> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await _api.get('/notifications/notifications');
      setState(() => _items = data as List<dynamic>);
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  IconData _iconForType(String? type) {
    switch (type) {
      case 'RDV':
        return Icons.event_rounded;
      case 'LABO':
        return Icons.biotech_rounded;
      case 'FACTURE':
        return Icons.receipt_long_rounded;
      default:
        return Icons.notifications_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 140,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              title: const Text('Notifications', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              background: Stack(
                fit: StackFit.expand,
                children: [
                  const DecoratedBox(decoration: BoxDecoration(gradient: AppDesign.heroPremiumGradient)),
                  Positioned(
                    right: 20,
                    bottom: 20,
                    child: Icon(Icons.notifications_rounded, size: 70, color: Colors.white.withValues(alpha: 0.16)),
                  ),
                  const DecoratedBox(decoration: BoxDecoration(gradient: AppDesign.heroOverlay)),
                ],
              ),
            ),
          ),
          if (_loading)
            const SliverFillRemaining(child: Center(child: CircularProgressIndicator(color: AppDesign.teal, strokeWidth: 2.5)))
          else if (_items.isEmpty)
            const SliverFillRemaining(
              child: EmptyPlaceholder(
                icon: Icons.notifications_none_rounded,
                title: 'Aucune notification',
                subtitle: 'Rappels de rendez-vous et alertes apparaîtront ici.',
              ),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.all(16),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, i) {
                    final n = _items[i] as Map<String, dynamic>;
                    final isUnread = n['est_lue'] != true;
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        color: isUnread ? AppDesign.teal.withValues(alpha: 0.06) : Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: isUnread ? AppDesign.teal.withValues(alpha: 0.25) : Colors.grey.shade100),
                        boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.05), blurRadius: 12, offset: const Offset(0, 4))],
                      ),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        leading: Container(
                          width: 46,
                          height: 46,
                          decoration: BoxDecoration(
                            color: isUnread ? AppDesign.teal.withValues(alpha: 0.15) : Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Icon(
                            _iconForType(n['type_notification'] as String?),
                            color: isUnread ? AppDesign.teal : Colors.grey.shade600,
                            size: 22,
                          ),
                        ),
                        title: Text(
                          n['titre'] as String? ?? '',
                          style: TextStyle(fontWeight: isUnread ? FontWeight.w800 : FontWeight.w600, color: AppDesign.textPrimary),
                        ),
                        subtitle: Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Text(n['corps'] as String? ?? '', style: const TextStyle(color: AppDesign.textSecondary, height: 1.35)),
                        ),
                        trailing: isUnread
                            ? Container(width: 10, height: 10, decoration: const BoxDecoration(color: AppDesign.teal, shape: BoxShape.circle))
                            : null,
                        onTap: () async {
                          if (isUnread) {
                            await _api.post('/notifications/notifications/${n['id']}/lue', {});
                            _load();
                          }
                        },
                      ),
                    );
                  },
                  childCount: _items.length,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
