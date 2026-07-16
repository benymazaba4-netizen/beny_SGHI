import 'dart:ui';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/push_service.dart';
import '../utils/auth_navigation.dart';
import '../theme/app_design.dart';
import '../widgets/pro_components.dart';
import 'overview_tab.dart';
import 'health_tab.dart';
import 'appointments_screen.dart';
import 'chat_screen.dart';
import 'profile_tab.dart';
import 'notifications_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = ApiService();
  int _tabIndex = 0;
  bool _loading = true;
  Map<String, dynamic>? _user;
  int? _patientId;

  List<dynamic> _consultations = [];
  List<dynamic> _examens = [];
  List<dynamic> _factures = [];
  List<dynamic> _prescriptions = [];
  List<dynamic> _plansSoins = [];
  List<dynamic> _rendezVous = [];
  List<dynamic> _notifications = [];
  List<dynamic> _pendingPayments = [];
  int _pendingPaymentCount = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final user = await _api.getCurrentUser();
    if (user == null) {
      if (mounted) Navigator.pushReplacementNamed(context, '/');
      return;
    }
    if (user['role'] != AppRoles.patient) {
      await _api.logout();
      if (mounted) Navigator.pushReplacementNamed(context, '/login');
      return;
    }

    setState(() {
      _user = user;
      _patientId = user['patient_id'] as int?;
    });

    if (_patientId == null) {
      setState(() => _loading = false);
      return;
    }

    setState(() => _loading = true);
    try {
      final pid = _patientId!;
      final results = await Future.wait([
        _api.get('/clinical/consultations/patient/$pid'),
        _api.get('/laboratory/demandes/patient/$pid'),
        _api.get('/billing/factures/patient/$pid'),
        _api.get('/prescriptions/prescriptions/patient/$pid'),
        _api.get('/clinical/plans-soins/patient/$pid'),
        _api.get('/appointments/rendez-vous/patient/$pid'),
        _api.get('/notifications/notifications'),
        _api.get('/secretariat/invoices/patient/$pid', params: {'status': 'PENDING'}),
      ]);
      setState(() {
        _consultations = results[0] as List<dynamic>;
        _examens = results[1] as List<dynamic>;
        _factures = results[2] as List<dynamic>;
        _prescriptions = results[3] as List<dynamic>;
        _plansSoins = results[4] as List<dynamic>;
        _rendezVous = results[5] as List<dynamic>;
        _notifications = results[6] as List<dynamic>;
        _pendingPayments = results[7] as List<dynamic>;
        _pendingPaymentCount = _pendingPayments.length;
      });
    } catch (_) {}
    setState(() => _loading = false);
    await PushNotificationService.instance.registerAfterLogin();
  }

  Future<void> _logout() async {
    await PushNotificationService.instance.unregister();
    await _api.logout();
    if (mounted) Navigator.pushReplacementNamed(context, '/');
  }

  String get _userName => '${_user?['first_name'] ?? ''} ${_user?['last_name'] ?? ''}'.trim();
  int get _unreadNotifs => _notifications.where((n) => (n as Map)['est_lue'] != true).length;

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        body: Container(
          decoration: const BoxDecoration(gradient: AppDesign.primaryGradient),
          child: const Center(child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5)),
        ),
      );
    }

    if (_patientId == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('SGHI Patient'), backgroundColor: AppDesign.navy),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: ProGlassCard(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.error_outline_rounded, size: 56, color: Colors.orange.shade700),
                  const SizedBox(height: 16),
                  const Text('Compte patient incomplet — aucun dossier associé.', textAlign: TextAlign.center),
                  const SizedBox(height: 20),
                  ProButton(label: 'Se déconnecter', onPressed: _logout),
                ],
              ),
            ),
          ),
        ),
      );
    }

    return Scaffold(
      extendBody: true,
      body: Container(
        decoration: const BoxDecoration(gradient: AppDesign.meshBackground),
        child: NestedScrollView(
          headerSliverBuilder: (context, innerBoxIsScrolled) => [
            SliverAppBar(
              expandedHeight: 168,
              pinned: true,
              stretch: true,
              actions: [
                Stack(
                  children: [
                    IconButton(
                      tooltip: 'Notifications',
                      icon: const Icon(Icons.notifications_outlined, color: Colors.white),
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const NotificationsScreen()),
                      ).then((_) => _load()),
                    ),
                    if (_unreadNotifs > 0)
                      Positioned(
                        right: 10,
                        top: 10,
                        child: Container(
                          padding: const EdgeInsets.all(5),
                          decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
                          child: Text('$_unreadNotifs', style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold)),
                        ),
                      ),
                  ],
                ),
              ],
              flexibleSpace: FlexibleSpaceBar(
                stretchModes: const [StretchMode.zoomBackground],
                titlePadding: const EdgeInsets.only(left: 20, bottom: 14),
                title: Text(
                  _userName.isNotEmpty ? _userName : 'Mon espace',
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, shadows: [Shadow(color: Colors.black38, blurRadius: 6)]),
                ),
                background: Stack(
                  fit: StackFit.expand,
                  children: [
                    const DecoratedBox(decoration: BoxDecoration(gradient: AppDesign.heroPremiumGradient)),
                    Positioned(
                      right: 20,
                      top: 40,
                      child: Icon(Icons.health_and_safety_rounded, size: 90, color: Colors.white.withValues(alpha: 0.12)),
                    ),
                    Container(decoration: const BoxDecoration(gradient: AppDesign.heroOverlay)),
                    Positioned(
                      left: 20,
                      bottom: 44,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                        decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white24)),
                        child: const Text('Espace patient sécurisé', style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w600)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          body: IndexedStack(
            index: _tabIndex,
            children: [
              OverviewTab(
                userName: _userName,
                consultations: _consultations.length,
                examens: _examens.length,
                factures: _factures.length,
                prescriptions: _prescriptions.length,
                rendezVous: _rendezVous.length,
                notifications: _unreadNotifs,
                pendingPayments: _pendingPaymentCount,
                onRefresh: _load,
                onNavigate: (i) => setState(() => _tabIndex = i),
              ),
              HealthTab(
                patientId: _patientId!,
                consultations: _consultations,
                examens: _examens,
                prescriptions: _prescriptions,
                plansSoins: _plansSoins,
                onRefresh: _load,
              ),
              AppointmentsScreen(
                patientId: _patientId!,
                pendingPayments: _pendingPayments,
                onChanged: _load,
              ),
              const ChatScreen(),
              ProfileTab(user: _user, factures: _factures, onLogout: _logout, onRefresh: _load),
            ],
          ),
        ),
      ),
      bottomNavigationBar: ClipRRect(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(26)),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.94),
              border: Border(top: BorderSide(color: AppDesign.teal.withValues(alpha: 0.12))),
              boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.1), blurRadius: 24, offset: const Offset(0, -6))],
            ),
            child: NavigationBar(
              selectedIndex: _tabIndex,
              onDestinationSelected: (i) => setState(() => _tabIndex = i),
              backgroundColor: Colors.transparent,
              elevation: 0,
              indicatorColor: AppDesign.teal.withValues(alpha: 0.14),
              destinations: const [
                NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard_rounded), label: 'Accueil'),
                NavigationDestination(icon: Icon(Icons.health_and_safety_outlined), selectedIcon: Icon(Icons.health_and_safety_rounded), label: 'Santé'),
                NavigationDestination(icon: Icon(Icons.event_outlined), selectedIcon: Icon(Icons.event_rounded), label: 'RDV'),
                NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble_rounded), label: 'Messages'),
                NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person_rounded), label: 'Profil'),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
