import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/file_service.dart';
import '../theme/app_design.dart';
import '../utils/formatters.dart';
import '../widgets/data_list_card.dart';
import '../widgets/empty_placeholder.dart';
import '../widgets/patient_qr_card.dart';

class HealthTab extends StatefulWidget {
  const HealthTab({
    super.key,
    required this.patientId,
    required this.consultations,
    required this.examens,
    required this.prescriptions,
    required this.plansSoins,
    required this.onRefresh,
  });

  final int patientId;
  final List<dynamic> consultations;
  final List<dynamic> examens;
  final List<dynamic> prescriptions;
  final List<dynamic> plansSoins;
  final Future<void> Function() onRefresh;

  @override
  State<HealthTab> createState() => _HealthTabState();
}

class _HealthTabState extends State<HealthTab> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _api = ApiService();
  bool _downloading = false;
  bool _qrLoading = false;
  Map<String, dynamic>? _qrAccess;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _downloadLabPdf(int resultatId) async {
    setState(() => _downloading = true);
    try {
      final bytes = await _api.downloadBytes('/laboratory/resultats/$resultatId/pdf');
      await FileService.openPdf(bytes, 'resultat-$resultatId.pdf');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  Future<void> _generatePatientQr() async {
    setState(() => _qrLoading = true);
    try {
      final data = await _api.post('/clinical/patients/${widget.patientId}/qr-access', {});
      if (mounted) setState(() => _qrAccess = Map<String, dynamic>.from(data as Map));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    } finally {
      if (mounted) setState(() => _qrLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
            boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.05), blurRadius: 12, offset: const Offset(0, 4))],
          ),
          child: TabBar(
            controller: _tabController,
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            dividerColor: Colors.transparent,
            indicatorSize: TabBarIndicatorSize.tab,
            indicator: BoxDecoration(
              color: AppDesign.teal.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            labelColor: AppDesign.teal,
            unselectedLabelColor: Colors.grey.shade600,
            labelStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
            padding: const EdgeInsets.all(6),
            tabs: const [
              Tab(text: 'Dossier'),
              Tab(text: 'Labo'),
              Tab(text: 'Ordonnances'),
              Tab(text: 'Soins'),
              Tab(text: 'Observance'),
            ],
          ),
        ),
        if (_downloading) const LinearProgressIndicator(),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildConsultations(),
              _buildExamens(),
              _buildPrescriptions(),
              _buildSoins(),
              _buildObservance(),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildConsultations() {
    if (widget.consultations.isEmpty) {
      return RefreshIndicator(
        onRefresh: widget.onRefresh,
        child: ListView(
          children: [
            PatientQrCard(
              qrCodeBase64: _qrAccess?['qr_code_base64']?.toString(),
              expiresAt: _qrAccess?['expires_at']?.toString(),
              loading: _qrLoading,
              onGenerate: _generatePatientQr,
            ),
            const EmptyPlaceholder(
              icon: Icons.folder_open_rounded,
              title: 'Aucune consultation',
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: widget.consultations.length + 1,
        itemBuilder: (_, i) {
          if (i == 0) {
            return PatientQrCard(
              qrCodeBase64: _qrAccess?['qr_code_base64']?.toString(),
              expiresAt: _qrAccess?['expires_at']?.toString(),
              loading: _qrLoading,
              onGenerate: _generatePatientQr,
            );
          }
          final c = widget.consultations[i - 1] as Map<String, dynamic>;
          return DataListCard(
            leading: CircleAvatar(backgroundColor: Colors.teal.shade50, child: Icon(Icons.medical_services, color: Colors.teal.shade700, size: 20)),
            title: formatDateShort(c['date_consultation']?.toString()),
            subtitle: '${c['motif'] ?? ''}\n${c['diagnostic'] ?? '—'} · CIM-10: ${c['diagnostic_cim10'] ?? '—'}',
          );
        },
      ),
    );
  }

  Widget _buildExamens() {
    if (widget.examens.isEmpty) {
      return const EmptyPlaceholder(icon: Icons.biotech_outlined, title: 'Aucun examen');
    }
    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: widget.examens.length,
        itemBuilder: (_, i) {
          final e = widget.examens[i] as Map<String, dynamic>;
          final published = e['resultat_publie'] == true;
          final resultatId = e['resultat_id'];
          return DataListCard(
            leading: CircleAvatar(backgroundColor: Colors.purple.shade50, child: Icon(Icons.science_outlined, color: Colors.purple.shade700, size: 20)),
            title: e['examen_type_nom']?.toString() ?? 'Examen',
            subtitle: 'Statut: ${e['statut']} · ${formatDateShort(e['date_prescription']?.toString())}',
            trailing: published && resultatId != null
                ? IconButton(
                    icon: const Icon(Icons.picture_as_pdf_outlined, color: Colors.red),
                    onPressed: () => _downloadLabPdf(resultatId as int),
                  )
                : null,
          );
        },
      ),
    );
  }

  Widget _buildPrescriptions() {
    if (widget.prescriptions.isEmpty) {
      return const EmptyPlaceholder(icon: Icons.medication_outlined, title: 'Aucune ordonnance');
    }
    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: widget.prescriptions.length,
        itemBuilder: (_, i) {
          final p = widget.prescriptions[i] as Map<String, dynamic>;
          return DataListCard(
            leading: CircleAvatar(backgroundColor: Colors.green.shade50, child: Icon(Icons.medication_liquid, color: Colors.green.shade700, size: 20)),
            title: 'Ordonnance #${p['id']}',
            subtitle: '${p['statut']} · ${formatDateShort(p['date_debut']?.toString())} → ${formatDateShort(p['date_fin']?.toString())}',
          );
        },
      ),
    );
  }

  Widget _buildObservance() {
    final rappels = <Map<String, dynamic>>[];
    for (final p in widget.prescriptions) {
      final presc = p as Map<String, dynamic>;
      if (presc['est_verrouillee'] != true) continue;
      final lignes = presc['lignes'] as List<dynamic>? ?? [];
      for (final l in lignes) {
        final ligne = l as Map<String, dynamic>;
        if ((ligne['quantite_restante'] as num? ?? 0) <= 0) continue;
        rappels.add({
          'medicament': ligne['medicament_nom'] ?? 'Médicament',
          'frequence': ligne['frequence'] ?? '—',
          'restant': ligne['quantite_restante'],
        });
      }
    }

    final postOp = widget.plansSoins.where((s) {
      final plan = s as Map<String, dynamic>;
      final text = '${plan['titre'] ?? ''} ${plan['description'] ?? ''}'.toLowerCase();
      return text.contains('post') || text.contains('opératoire') || text.contains('operatoire');
    }).toList();

    if (rappels.isEmpty && postOp.isEmpty) {
      return const EmptyPlaceholder(
        icon: Icons.notifications_active_outlined,
        title: 'Aucun rappel actif',
        subtitle: 'Les rappels médicamenteux apparaissent après validation d\'une ordonnance.',
      );
    }

    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (rappels.isNotEmpty) ...[
            Text('Rappels médicamenteux', style: TextStyle(fontWeight: FontWeight.w800, color: Colors.green.shade800)),
            const SizedBox(height: 8),
            ...rappels.map((r) => DataListCard(
              leading: CircleAvatar(
                backgroundColor: Colors.green.shade50,
                child: Icon(Icons.alarm_rounded, color: Colors.green.shade700, size: 20),
              ),
              title: r['medicament'] as String,
              subtitle: '${r['frequence']} · ${r['restant']} dose(s) restante(s)',
            )),
            const SizedBox(height: 16),
          ],
          if (postOp.isNotEmpty) ...[
            Text('Suivi post-opératoire', style: TextStyle(fontWeight: FontWeight.w800, color: Colors.orange.shade800)),
            const SizedBox(height: 8),
            ...postOp.map((s) {
              final plan = s as Map<String, dynamic>;
              return DataListCard(
                leading: CircleAvatar(
                  backgroundColor: Colors.orange.shade50,
                  child: Icon(Icons.healing_rounded, color: Colors.orange.shade700, size: 20),
                ),
                title: plan['titre']?.toString() ?? 'Suivi post-op',
                subtitle: '${plan['frequence'] ?? ''} · ${plan['statut'] ?? ''} · ${formatDateShort(plan['date_debut']?.toString())}',
              );
            }),
          ],
        ],
      ),
    );
  }

  Widget _buildSoins() {
    if (widget.plansSoins.isEmpty) {
      return const EmptyPlaceholder(icon: Icons.healing_outlined, title: 'Aucun plan de soins');
    }
    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: widget.plansSoins.length,
        itemBuilder: (_, i) {
          final s = widget.plansSoins[i] as Map<String, dynamic>;
          return DataListCard(
            leading: CircleAvatar(backgroundColor: Colors.cyan.shade50, child: Icon(Icons.favorite_outline, color: Colors.cyan.shade700, size: 20)),
            title: s['titre']?.toString() ?? 'Plan de soins',
            subtitle: '${s['frequence']} · ${s['statut']} · depuis ${formatDateShort(s['date_debut']?.toString())}',
          );
        },
      ),
    );
  }
}
