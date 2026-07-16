import 'package:flutter/material.dart';
import '../theme/app_design.dart';
import '../widgets/pro_components.dart';
import '../widgets/payment_gate_banner.dart';

class OverviewTab extends StatelessWidget {
  const OverviewTab({
    super.key,
    required this.userName,
    required this.consultations,
    required this.examens,
    required this.factures,
    required this.prescriptions,
    required this.rendezVous,
    required this.notifications,
    this.pendingPayments = 0,
    required this.onRefresh,
    this.onNavigate,
  });

  final String userName;
  final int consultations;
  final int examens;
  final int factures;
  final int prescriptions;
  final int rendezVous;
  final int notifications;
  final int pendingPayments;
  final Future<void> Function() onRefresh;
  final void Function(int tabIndex)? onNavigate;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh,
      color: AppDesign.teal,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
        children: [
          Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              gradient: AppDesign.primaryGradient,
              borderRadius: BorderRadius.circular(24),
              boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.28), blurRadius: 24, offset: const Offset(0, 12))],
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        userName.isNotEmpty ? 'Bonjour, $userName' : 'Mon espace santé',
                        style: const TextStyle(color: Colors.white, fontSize: 21, fontWeight: FontWeight.w800, letterSpacing: -0.3),
                      ),
                      const SizedBox(height: 6),
                      Text('Vue d\'ensemble de votre parcours', style: TextStyle(color: Colors.white.withValues(alpha: 0.88), fontSize: 13)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.18), borderRadius: BorderRadius.circular(18), border: Border.all(color: Colors.white24)),
                  child: const Icon(Icons.favorite_rounded, color: Colors.white, size: 28),
                ),
              ],
            ),
          ),
          PaymentGateBanner(
            pendingCount: pendingPayments,
            onTap: () => onNavigate?.call(2),
          ),
          const SizedBox(height: 22),
          const ProSectionHeader(title: 'Accès rapide', subtitle: 'Naviguez entre vos services'),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                ProQuickChip(icon: Icons.health_and_safety_rounded, label: 'Santé', color: AppDesign.teal, onTap: () => onNavigate?.call(1)),
                const SizedBox(width: 12),
                ProQuickChip(icon: Icons.event_rounded, label: 'RDV', color: AppDesign.navyMid, onTap: () => onNavigate?.call(2)),
                const SizedBox(width: 12),
                ProQuickChip(icon: Icons.chat_rounded, label: 'Messages', color: Colors.purple, onTap: () => onNavigate?.call(3)),
                const SizedBox(width: 12),
                ProQuickChip(icon: Icons.person_rounded, label: 'Profil', color: Colors.orange, onTap: () => onNavigate?.call(4)),
              ],
            ),
          ),
          const SizedBox(height: 26),
          const ProSectionHeader(title: 'Indicateurs', subtitle: 'Vos données en un coup d\'œil'),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 14,
            crossAxisSpacing: 14,
            childAspectRatio: 0.9,
            children: [
              ProStatCard(label: 'Consultations', value: '$consultations', icon: Icons.medical_information_rounded, color: AppDesign.teal),
              ProStatCard(label: 'Examens', value: '$examens', icon: Icons.science_rounded, color: Colors.purple),
              ProStatCard(label: 'Ordonnances', value: '$prescriptions', icon: Icons.local_pharmacy_rounded, color: Colors.green),
              ProStatCard(label: 'Factures', value: '$factures', icon: Icons.account_balance_wallet_rounded, color: Colors.orange),
              ProStatCard(label: 'RDV', value: '$rendezVous', icon: Icons.event_available_rounded, color: AppDesign.navyMid),
              ProStatCard(label: 'Alertes', value: '$notifications', icon: Icons.notifications_active_rounded, color: Colors.blue),
            ],
          ),
          const SizedBox(height: 22),
          Container(
            padding: const EdgeInsets.all(18),
            decoration: AppDesign.gradientCardDecoration(AppDesign.teal),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: AppDesign.teal.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(14)),
                  child: const Icon(Icons.shield_rounded, color: AppDesign.teal, size: 28),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(
                    'Vos données sont chiffrées et accessibles uniquement avec votre compte patient.',
                    style: TextStyle(color: AppDesign.navy.withValues(alpha: 0.85), fontSize: 13, height: 1.45, fontWeight: FontWeight.w500),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
