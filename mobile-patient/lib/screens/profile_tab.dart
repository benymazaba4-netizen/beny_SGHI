import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/file_service.dart';
import '../theme/app_design.dart';
import '../utils/formatters.dart';
import '../widgets/data_list_card.dart';
import '../widgets/empty_placeholder.dart';
import '../widgets/pro_components.dart';
import 'notifications_screen.dart';
import 'pay_invoice_screen.dart';

class ProfileTab extends StatefulWidget {
  const ProfileTab({
    super.key,
    required this.user,
    required this.factures,
    required this.onLogout,
    required this.onRefresh,
  });

  final Map<String, dynamic>? user;
  final List<dynamic> factures;
  final VoidCallback onLogout;
  final Future<void> Function() onRefresh;

  @override
  State<ProfileTab> createState() => _ProfileTabState();
}

class _ProfileTabState extends State<ProfileTab> {
  final _api = ApiService();

  Future<void> _downloadFacture(int id, String numero) async {
    try {
      final bytes = await _api.downloadBytes('/billing/factures/$id/pdf');
      await FileService.openPdf(bytes, '$numero.pdf');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e'), behavior: SnackBarBehavior.floating));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final u = widget.user;
    final initials = '${u?['first_name']?[0] ?? ''}${u?['last_name']?[0] ?? ''}'.toUpperCase();

    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      color: AppDesign.teal,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
        children: [
          Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              gradient: AppDesign.primaryGradient,
              borderRadius: BorderRadius.circular(24),
              boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.22), blurRadius: 22, offset: const Offset(0, 10))],
            ),
            child: Row(
              children: [
                Container(
                  width: 68,
                  height: 68,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.22),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white38),
                  ),
                  child: Center(
                    child: Text(initials.isEmpty ? 'P' : initials, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 24)),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${u?['first_name'] ?? ''} ${u?['last_name'] ?? ''}'.trim(), style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
                      const SizedBox(height: 4),
                      Text(u?['email']?.toString() ?? u?['username']?.toString() ?? '', style: TextStyle(color: Colors.white.withValues(alpha: 0.82), fontSize: 13)),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(20)),
                        child: Text('Dossier #${u?['patient_id'] ?? '—'}', style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600)),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          const ProSectionHeader(title: 'Mes factures', subtitle: 'Téléchargez vos documents PDF'),
          if (widget.factures.isEmpty)
            const EmptyPlaceholder(icon: Icons.receipt_long_rounded, title: 'Aucune facture', subtitle: 'Vos factures apparaîtront ici.')
          else
            ...widget.factures.map((f) {
              final facture = f as Map<String, dynamic>;
              final pdfOk = facture['pdf_disponible'] == true;
              return DataListCard(
                accentColor: Colors.orange,
                leading: CircleAvatar(
                  backgroundColor: Colors.orange.shade50,
                  child: Icon(Icons.receipt_rounded, color: Colors.orange.shade700, size: 20),
                ),
                title: facture['numero_facture']?.toString() ?? 'Facture',
                subtitle: '${facture['statut']} · ${formatFcfa(facture['montant_patient'])}\nReste: ${formatFcfa(facture['montant_restant'])}',
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if ((facture['montant_restant'] as num? ?? 0) > 0)
                      IconButton(
                        tooltip: 'Payer',
                        icon: Icon(Icons.payment_rounded, color: Colors.green.shade700),
                        onPressed: () async {
                          final paid = await Navigator.push<bool>(
                            context,
                            MaterialPageRoute(builder: (_) => PayInvoiceScreen(facture: facture)),
                          );
                          if (paid == true) widget.onRefresh();
                        },
                      ),
                    if (pdfOk)
                      IconButton(
                        icon: const Icon(Icons.picture_as_pdf_rounded, color: Colors.red),
                        onPressed: () => _downloadFacture(facture['id'] as int, facture['numero_facture']?.toString() ?? 'facture'),
                      ),
                  ],
                ),
              );
            }),
          const SizedBox(height: 8),
          DataListCard(
            accentColor: AppDesign.teal,
            leading: CircleAvatar(backgroundColor: AppDesign.teal.withValues(alpha: 0.12), child: const Icon(Icons.notifications_active_rounded, color: AppDesign.teal, size: 20)),
            title: 'Notifications',
            subtitle: 'Rappels et alertes',
            trailing: const Icon(Icons.chevron_right_rounded),
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
          ),
          const SizedBox(height: 24),
          ProButton(label: 'Déconnexion', outlined: true, icon: Icons.logout_rounded, onPressed: widget.onLogout),
        ],
      ),
    );
  }
}
