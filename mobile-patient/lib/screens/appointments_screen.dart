import 'package:flutter/material.dart';

import 'package:flutter/services.dart';

import '../services/api_service.dart';

import '../theme/app_design.dart';

import '../widgets/empty_placeholder.dart';

import '../widgets/pro_components.dart';

import '../widgets/user_avatar.dart';

import '../widgets/payment_gate_banner.dart';

import 'create_appointment_screen.dart';



class AppointmentsScreen extends StatefulWidget {

  const AppointmentsScreen({super.key, required this.patientId, this.pendingPayments = const [], this.onChanged});



  final int patientId;

  final List<dynamic> pendingPayments;

  final VoidCallback? onChanged;



  @override

  State<AppointmentsScreen> createState() => _AppointmentsScreenState();

}



class _AppointmentsScreenState extends State<AppointmentsScreen> {

  final _api = ApiService();

  List<dynamic> _rdvs = [];

  bool _loading = true;



  @override

  void initState() {

    super.initState();

    _load();

  }



  Future<void> _load() async {

    setState(() => _loading = true);

    try {

      final data = await _api.getAllPages('/appointments/rendez-vous/patient/${widget.patientId}');

      setState(() => _rdvs = data);

    } catch (_) {}

    if (mounted) setState(() => _loading = false);

  }



  Future<void> _openCreate() async {

    HapticFeedback.selectionClick();

    final created = await Navigator.push<bool>(

      context,

      MaterialPageRoute(builder: (_) => CreateAppointmentScreen(patientId: widget.patientId)),

    );

    if (created == true) {

      await _load();

      widget.onChanged?.call();

    }

  }



  Color _statusColor(String? statut) {

    switch (statut) {

      case 'CONFIRME':

        return AppDesign.teal;

      case 'ANNULE':

        return Colors.red;

      case 'TERMINE':

        return AppDesign.navyMid;

      default:

        return Colors.orange;

    }

  }



  Future<void> _annuler(int id) async {

    HapticFeedback.lightImpact();

    final confirm = await showDialog<bool>(

      context: context,

      builder: (ctx) => AlertDialog(

        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),

        title: const Text('Annuler le rendez-vous ?'),

        content: const Text('Cette action est définitive.'),

        actions: [

          TextButton(

            onPressed: () {

              HapticFeedback.selectionClick();

              Navigator.pop(ctx, false);

            },

            child: const Text('Non'),

          ),

          FilledButton(

            onPressed: () {

              HapticFeedback.mediumImpact();

              Navigator.pop(ctx, true);

            },

            style: FilledButton.styleFrom(backgroundColor: Colors.red),

            child: const Text('Oui, annuler'),

          ),

        ],

      ),

    );

    if (confirm != true) return;

    try {

      await _api.post('/appointments/rendez-vous/$id/annuler', {});

      HapticFeedback.mediumImpact();

      await _load();

      widget.onChanged?.call();

      if (mounted) {

        ScaffoldMessenger.of(context).showSnackBar(

          const SnackBar(content: Text('Rendez-vous annulé'), behavior: SnackBarBehavior.floating),

        );

      }

    } catch (e) {

      HapticFeedback.lightImpact();

      if (mounted) {

        ScaffoldMessenger.of(context).showSnackBar(

          SnackBar(content: Text('$e'), behavior: SnackBarBehavior.floating, backgroundColor: Colors.red.shade700),

        );

      }

    }

  }



  String? _paymentStatusForRdv(int? rdvId) {

    if (rdvId == null) return null;

    for (final raw in widget.pendingPayments) {

      final inv = raw as Map<String, dynamic>;

      if (inv['rendez_vous_id'] == rdvId) return 'PENDING';

    }

    return null;

  }



  @override

  Widget build(BuildContext context) {

    final rdvDates = _rdvs.map((r) {

      final raw = (r as Map<String, dynamic>)['date_heure']?.toString() ?? '';

      return raw.length >= 10 ? raw.substring(0, 10) : raw;

    }).where((d) => d.isNotEmpty).toSet();



    return Stack(

      children: [

        if (_loading)

          const Center(child: CircularProgressIndicator(color: AppDesign.teal, strokeWidth: 2.5))

        else if (_rdvs.isEmpty)

          const EmptyPlaceholder(

            icon: Icons.event_available_rounded,

            title: 'Aucun rendez-vous planifié',

            subtitle: 'Appuyez sur + pour prendre un rendez-vous.',

          )

        else

          Column(

            children: [

              PaymentGateBanner(

                pendingCount: widget.pendingPayments.length,

                amount: widget.pendingPayments.isNotEmpty

                    ? (widget.pendingPayments.first as Map<String, dynamic>)['amount'] as num?

                    : null,

              ),

              Padding(

                padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),

                child: Container(

                  padding: const EdgeInsets.all(12),

                  decoration: BoxDecoration(

                    color: Colors.white,

                    borderRadius: BorderRadius.circular(16),

                    border: Border.all(color: Colors.grey.shade200),

                  ),

                  child: Column(

                    crossAxisAlignment: CrossAxisAlignment.start,

                    children: [

                      const Text('Calendrier', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14)),

                      const SizedBox(height: 8),

                      Wrap(

                        spacing: 6,

                        runSpacing: 6,

                        children: rdvDates.map((d) => Chip(

                          label: Text(d, style: const TextStyle(fontSize: 11)),

                          backgroundColor: AppDesign.teal.withValues(alpha: 0.12),

                          side: BorderSide.none,

                        )).toList(),

                      ),

                    ],

                  ),

                ),

              ),

              Expanded(

                child: RefreshIndicator(

                  onRefresh: () async {

                    HapticFeedback.selectionClick();

                    await _load();

                  },

                  color: AppDesign.teal,

                  child: ListView.builder(

                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),

                    itemCount: _rdvs.length,

                    itemBuilder: (context, i) {

                      final r = _rdvs[i] as Map<String, dynamic>;

                      final statut = r['statut'] as String?;

                      final color = _statusColor(statut);

                      final paymentStatus = _paymentStatusForRdv(r['id'] as int?);

                      return Container(

                        margin: const EdgeInsets.only(bottom: 14),

                        decoration: BoxDecoration(

                          color: Colors.white,

                          borderRadius: BorderRadius.circular(22),

                          border: Border.all(color: color.withValues(alpha: 0.18)),

                          boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.06), blurRadius: 16, offset: const Offset(0, 6))],

                        ),

                        child: Padding(

                          padding: const EdgeInsets.all(16),

                          child: Row(

                            crossAxisAlignment: CrossAxisAlignment.start,

                            children: [

                              UserAvatar(name: r['medecin']?.toString() ?? 'Médecin', size: 48),

                              const SizedBox(width: 14),

                              Expanded(

                                child: Column(

                                  crossAxisAlignment: CrossAxisAlignment.start,

                                  children: [

                                    Row(

                                      children: [

                                        Expanded(

                                          child: Text(

                                            r['date_heure']?.toString().substring(0, 16).replaceAll('T', ' ') ?? '',

                                            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppDesign.textPrimary),

                                          ),

                                        ),

                                        ProStatusChip(label: statut ?? '', color: color),

                                        if (paymentStatus != null) ...[

                                          const SizedBox(width: 6),

                                          PaymentStatusChip(status: paymentStatus),

                                        ],

                                      ],

                                    ),

                                    const SizedBox(height: 6),

                                    Text('Dr ${r['medecin']}', style: const TextStyle(fontWeight: FontWeight.w600, color: AppDesign.textPrimary)),

                                    if (r['motif'] != null && '${r['motif']}'.isNotEmpty)

                                      Padding(

                                        padding: const EdgeInsets.only(top: 4),

                                        child: Text('${r['motif']}', style: const TextStyle(color: AppDesign.textSecondary, fontSize: 13)),

                                      ),

                                    if (paymentStatus == 'PENDING')

                                      Padding(

                                        padding: const EdgeInsets.only(top: 8),

                                        child: Text(

                                          'Réglez les frais au secrétariat avant votre consultation.',

                                          style: TextStyle(color: Colors.red.shade700, fontSize: 12, fontWeight: FontWeight.w600),

                                        ),

                                      ),

                                    if (r['service'] != null)

                                      Padding(

                                        padding: const EdgeInsets.only(top: 2),

                                        child: Text('${r['service']}', style: TextStyle(color: Colors.grey.shade500, fontSize: 12)),

                                      ),

                                  ],

                                ),

                              ),

                              if (statut == 'CONFIRME' || statut == 'PLANIFIE')

                                IconButton(

                                  tooltip: 'Annuler',

                                  icon: Icon(Icons.cancel_outlined, color: Colors.red.shade400),

                                  onPressed: () => _annuler(r['id'] as int),

                                ),

                            ],

                          ),

                        ),

                      );

                    },

                  ),

                ),

              ),

            ],

          ),

        Positioned(right: 20, bottom: 24, child: ProFab(label: 'Nouveau RDV', icon: Icons.add_rounded, onPressed: _openCreate)),

      ],

    );

  }

}


