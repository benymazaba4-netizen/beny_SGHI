import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_design.dart';
import '../utils/auth_navigation.dart';
import '../widgets/data_list_card.dart';
import '../widgets/pro_components.dart';
import '../widgets/stat_card.dart';

class StaffHomeScreen extends StatefulWidget {
  const StaffHomeScreen({super.key, required this.role});

  final String role;

  @override
  State<StaffHomeScreen> createState() => _StaffHomeScreenState();
}

class _StaffHomeScreenState extends State<StaffHomeScreen> {
  final _api = ApiService();
  int _tab = 0;
  bool _loading = true;
  String _error = '';
  Map<String, dynamic>? _user;

  List<dynamic> _patients = [];
  List<dynamic> _admissions = [];
  List<dynamic> _labo = [];
  List<dynamic> _medecins = [];

  bool get _isMedecin => widget.role == AppRoles.medecin;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final user = await _api.getCurrentUser();
      if (!mounted) return;
      if (user == null || user['role'] != widget.role) {
        Navigator.pushReplacementNamed(context, '/login');
        return;
      }
      _user = user;

      final patients = await _api.get('/clinical/patients');
      final admissions = await _api.get('/clinical/admissions/actives');

      List<dynamic> labo = [];
      List<dynamic> medecins = [];
      if (_isMedecin) {
        try {
          labo = await _api.get('/laboratory/demandes/en-cours') as List<dynamic>;
        } catch (_) {}
      } else {
        try {
          medecins = await _api.get('/auth/medecins') as List<dynamic>;
        } catch (_) {}
      }

      if (!mounted) return;
      setState(() {
        _patients = patients is List ? patients : [];
        _admissions = admissions is List ? admissions : [];
        _labo = labo;
        _medecins = medecins;
      });
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _logout() async {
    await _api.logout();
    if (!mounted) return;
    Navigator.pushReplacementNamed(context, '/');
  }

  String get _greeting {
    final name = _user?['first_name']?.toString();
    if (name != null && name.isNotEmpty) return 'Bonjour, $name';
    return 'Bonjour';
  }

  @override
  Widget build(BuildContext context) {
    final accent = _isMedecin ? Colors.blue : Colors.pink;

    return Scaffold(
      backgroundColor: AppDesign.surface,
      appBar: AppBar(
        flexibleSpace: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: _isMedecin
                  ? [const Color(0xFF1E3A8A), const Color(0xFF3B82F6)]
                  : [const Color(0xFF881337), const Color(0xFFE11D48)],
            ),
          ),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(AppRoles.label(widget.role), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
            Text(_greeting, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Colors.white70)),
          ],
        ),
        actions: [
          IconButton(onPressed: _load, icon: const Icon(Icons.refresh_rounded)),
          IconButton(onPressed: _logout, icon: const Icon(Icons.logout_rounded)),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppDesign.teal))
          : RefreshIndicator(
              onRefresh: _load,
              child: _tab == 0 ? _overviewTab(accent) : _tab == 1 ? _patientsTab() : _thirdTab(),
            ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: [
          const NavigationDestination(icon: Icon(Icons.dashboard_rounded), label: 'Accueil'),
          const NavigationDestination(icon: Icon(Icons.people_rounded), label: 'Patients'),
          NavigationDestination(
            icon: Icon(_isMedecin ? Icons.biotech_rounded : Icons.local_hospital_rounded),
            label: _isMedecin ? 'Labo' : 'Admissions',
          ),
        ],
      ),
    );
  }

  Widget _overviewTab(Color accent) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        if (_error.isNotEmpty) ...[ProErrorBanner(message: _error), const SizedBox(height: 16)],
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 12,
          crossAxisSpacing: 12,
          childAspectRatio: 1.35,
          children: [
            StatCard(label: 'Patients', value: '${_patients.length}', icon: Icons.people_rounded, color: accent),
            StatCard(
              label: 'Admissions',
              value: '${_admissions.length}',
              icon: Icons.local_hospital_rounded,
              color: AppDesign.teal,
            ),
            if (_isMedecin)
              StatCard(label: 'Examens', value: '${_labo.length}', icon: Icons.biotech_rounded, color: Colors.purple)
            else
              StatCard(label: 'Médecins', value: '${_medecins.length}', icon: Icons.medical_services_rounded, color: Colors.blue),
            StatCard(
              label: 'Lits occupés',
              value: '${_admissions.where((a) => a['lit_numero'] != null).length}',
              icon: Icons.bed_rounded,
              color: Colors.orange,
            ),
          ],
        ),
        const SizedBox(height: 24),
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.grey.shade100),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _isMedecin ? 'Espace médecin mobile' : 'Espace secrétaire mobile',
                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppDesign.textPrimary),
              ),
              const SizedBox(height: 8),
              Text(
                _isMedecin
                    ? 'Consultez patients, hospitalisations et demandes labo. Les actions avancées (consultation, prescription) restent sur le portail web.'
                    : 'Suivez patients et admissions. Création patient, admission et RDV détaillés sur le portail web.',
                style: TextStyle(color: Colors.grey.shade600, height: 1.45, fontSize: 13),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _patientsTab() {
    if (_patients.isEmpty) {
      return ListView(
        children: const [
          SizedBox(height: 80),
          Center(child: Text('Aucun patient enregistré')),
        ],
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: _patients.length,
      itemBuilder: (context, i) {
        final p = _patients[i] as Map<String, dynamic>;
        return DataListCard(
          title: '${p['nom'] ?? ''} ${p['prenom'] ?? ''}'.trim(),
          subtitle: 'Dossier ${p['numero_dossier'] ?? '—'} · ${p['telephone'] ?? ''}',
          leading: CircleAvatar(
            backgroundColor: AppDesign.teal.withValues(alpha: 0.12),
            child: const Icon(Icons.person_rounded, color: AppDesign.teal, size: 20),
          ),
        );
      },
    );
  }

  Widget _thirdTab() {
    if (_isMedecin) return _laboTab();
    return _admissionsTab();
  }

  Widget _laboTab() {
    if (_labo.isEmpty) {
      return ListView(
        children: const [
          SizedBox(height: 80),
          Center(child: Text('Aucune demande labo en cours')),
        ],
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: _labo.length,
      itemBuilder: (context, i) {
        final d = _labo[i] as Map<String, dynamic>;
        return DataListCard(
          title: d['examen_type_nom']?.toString() ?? 'Examen',
          subtitle: '${d['patient_nom'] ?? ''} ${d['patient_prenom'] ?? ''} · ${d['statut'] ?? ''}',
          accentColor: Colors.purple,
          leading: const CircleAvatar(
            backgroundColor: Color(0x1A7C3AED),
            child: Icon(Icons.biotech_rounded, color: Colors.purple, size: 20),
          ),
        );
      },
    );
  }

  Widget _admissionsTab() {
    if (_admissions.isEmpty) {
      return ListView(
        children: const [
          SizedBox(height: 80),
          Center(child: Text('Aucune admission active')),
        ],
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: _admissions.length,
      itemBuilder: (context, i) {
        final a = _admissions[i] as Map<String, dynamic>;
        return DataListCard(
          title: a['patient_nom']?.toString() ?? 'Patient',
          subtitle: '${a['service_nom'] ?? ''} · Lit ${a['lit_numero'] ?? '—'}',
          accentColor: Colors.pink,
          leading: const CircleAvatar(
            backgroundColor: Color(0x1AE11D48),
            child: Icon(Icons.local_hospital_rounded, color: Colors.pink, size: 20),
          ),
        );
      },
    );
  }
}
