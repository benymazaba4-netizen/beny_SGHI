import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../config/app_config.dart';
import '../services/api_service.dart';
import '../services/push_service.dart';
import '../utils/auth_navigation.dart';
import '../theme/app_design.dart';
import '../widgets/portal_service_tile.dart';
import '../widgets/showcase_image_card.dart';
import '../widgets/pro_components.dart';

class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({super.key});

  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen> with TickerProviderStateMixin {
  final _api = ApiService();
  final _pageController = PageController();
  bool _checking = true;
  int _heroPage = 0;
  late AnimationController _fadeAnim;
  late AnimationController _floatAnim;

  static const _heroSlides = [
    (title: 'Votre santé,\nà portée de main', subtitle: 'RDV, labo, ordonnances et paiements en un seul endroit.', icon: Icons.health_and_safety_rounded),
    (title: 'Équipe médicale\nd\'excellence', subtitle: 'Des spécialistes au service de votre bien-être.', icon: Icons.medical_services_rounded),
    (title: 'CHU moderne\n& connecté', subtitle: 'Infrastructure hospitalière de pointe.', icon: Icons.apartment_rounded),
    (title: 'Résultats labo\nen temps réel', subtitle: 'Téléchargez vos comptes-rendus PDF dès publication.', icon: Icons.science_rounded),
    (title: 'Paiement\nsimplifié', subtitle: 'MTN Mobile Money, carte ou espèces — suivi transparent.', icon: Icons.account_balance_wallet_rounded),
  ];

  static const _galleryItems = [
    (icon: Icons.apartment_rounded, label: 'Infrastructure moderne', color: AppDesign.navy),
    (icon: Icons.groups_rounded, label: 'Équipe soignante', color: AppDesign.teal),
    (icon: Icons.science_rounded, label: 'Laboratoire certifié', color: Colors.purple),
    (icon: Icons.local_pharmacy_rounded, label: 'Pharmacie hospitalière', color: Colors.indigo),
    (icon: Icons.favorite_rounded, label: 'Soins & accompagnement', color: Colors.pink),
    (icon: Icons.meeting_room_rounded, label: 'Accueil patients', color: Colors.teal),
  ];

  static const _stats = [
    (value: '24/7', label: 'Accès sécurisé'),
    (value: '100%', label: 'Chiffré'),
    (value: 'PDF', label: 'Résultats'),
    (value: 'MTN', label: 'Paiement'),
  ];

  static const _features = [
    (icon: Icons.event_available_rounded, label: 'RDV en ligne', color: AppDesign.teal),
    (icon: Icons.biotech_rounded, label: 'Labo PDF', color: Colors.purple),
    (icon: Icons.medication_rounded, label: 'Ordonnances', color: AppDesign.navy),
    (icon: Icons.chat_rounded, label: 'Messagerie', color: Colors.blue),
    (icon: Icons.notifications_active_rounded, label: 'Rappels', color: Colors.orange),
  ];

  @override
  void initState() {
    super.initState();
    _fadeAnim = AnimationController(vsync: this, duration: const Duration(milliseconds: 900))..forward();
    _floatAnim = AnimationController(vsync: this, duration: const Duration(seconds: 3))..repeat(reverse: true);
    _checkSession();
  }

  @override
  void dispose() {
    _pageController.dispose();
    _fadeAnim.dispose();
    _floatAnim.dispose();
    super.dispose();
  }

  Future<void> _checkSession() async {
    if (await _api.isLoggedIn()) {
      final user = await _api.getCurrentUser();
      if (!mounted) return;
      if (AppRoles.isMobileRole(user?['role']?.toString())) {
        if (user?['role'] == AppRoles.patient) {
          await PushNotificationService.instance.registerAfterLogin();
        }
        if (!mounted) return;
        final route = AppRoles.homeRoute(user?['role']?.toString());
        if (route == '/staff') {
          Navigator.pushReplacementNamed(context, route!, arguments: user?['role']);
        } else if (route != null) {
          Navigator.pushReplacementNamed(context, route);
        }
        return;
      }
    }
    if (mounted) setState(() => _checking = false);
  }

  void _goLogin() {
    HapticFeedback.lightImpact();
    Navigator.pushNamed(context, '/login');
  }

  @override
  Widget build(BuildContext context) {
    if (_checking) {
      return Scaffold(
        body: Container(
          decoration: const BoxDecoration(gradient: AppDesign.primaryGradient),
          child: const Center(child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5)),
        ),
      );
    }

    return Scaffold(
      body: Stack(
        children: [
          Container(decoration: const BoxDecoration(gradient: AppDesign.meshBackground)),
          CustomScrollView(
            slivers: [
              // Carousel hero
              SliverToBoxAdapter(
                child: FadeTransition(
                  opacity: CurvedAnimation(parent: _fadeAnim, curve: Curves.easeOut),
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 48, 16, 0),
                    child: Column(
                      children: [
                        SizedBox(
                          height: 340,
                          child: PageView.builder(
                            controller: _pageController,
                            itemCount: _heroSlides.length,
                            onPageChanged: (i) => setState(() => _heroPage = i),
                            itemBuilder: (context, i) {
                              final slide = _heroSlides[i];
                              return AnimatedBuilder(
                                animation: _floatAnim,
                                builder: (context, child) => Transform.translate(
                                  offset: Offset(0, _floatAnim.value * 4 - 2),
                                  child: child,
                                ),
                                child: Container(
                                  margin: const EdgeInsets.symmetric(horizontal: 2),
                                  decoration: AppDesign.heroDecoration(),
                                  clipBehavior: Clip.antiAlias,
                                  child: Stack(
                                    fit: StackFit.expand,
                                    children: [
                                      const DecoratedBox(
                                        decoration: BoxDecoration(gradient: AppDesign.heroPremiumGradient),
                                      ),
                                      // Grande icône du service en filigrane
                                      Positioned(
                                        right: 20,
                                        top: 90,
                                        child: Icon(
                                          slide.icon,
                                          size: 120,
                                          color: Colors.white.withValues(alpha: 0.14),
                                        ),
                                      ),
                                      // Motif décoratif subtil
                                      Positioned(
                                        right: -40,
                                        top: -30,
                                        child: Container(
                                          width: 180,
                                          height: 180,
                                          decoration: BoxDecoration(
                                            shape: BoxShape.circle,
                                            color: Colors.white.withValues(alpha: 0.06),
                                          ),
                                        ),
                                      ),
                                      Positioned(
                                        right: 40,
                                        bottom: 60,
                                        child: Container(
                                          width: 100,
                                          height: 100,
                                          decoration: BoxDecoration(
                                            shape: BoxShape.circle,
                                            color: AppDesign.mint.withValues(alpha: 0.08),
                                          ),
                                        ),
                                      ),
                                      Positioned(
                                        top: 20,
                                        left: 20,
                                        child: ProLogo(size: 52),
                                      ),
                                      Positioned(
                                        top: 24,
                                        right: 20,
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                          decoration: BoxDecoration(
                                            color: Colors.white.withValues(alpha: 0.15),
                                            borderRadius: BorderRadius.circular(20),
                                            border: Border.all(color: Colors.white30),
                                            boxShadow: [
                                              BoxShadow(color: Colors.black.withValues(alpha: 0.15), blurRadius: 12),
                                            ],
                                          ),
                                          child: const Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              Icon(Icons.auto_awesome, color: Colors.tealAccent, size: 14),
                                              SizedBox(width: 4),
                                              Text('Portail patient', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
                                            ],
                                          ),
                                        ),
                                      ),
                                      Positioned(
                                        left: 24,
                                        right: 24,
                                        bottom: 28,
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              slide.title,
                                              style: const TextStyle(
                                                color: Colors.white,
                                                fontSize: 26,
                                                fontWeight: FontWeight.w800,
                                                height: 1.15,
                                                letterSpacing: -0.5,
                                                shadows: [Shadow(color: Colors.black38, blurRadius: 12)],
                                              ),
                                            ),
                                            const SizedBox(height: 8),
                                            Text(
                                              slide.subtitle,
                                              style: TextStyle(
                                                color: Colors.white.withValues(alpha: 0.9),
                                                fontSize: 14,
                                                height: 1.4,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: List.generate(_heroSlides.length, (i) {
                            final active = i == _heroPage;
                            return AnimatedContainer(
                              duration: const Duration(milliseconds: 250),
                              margin: const EdgeInsets.symmetric(horizontal: 3),
                              width: active ? 24 : 8,
                              height: 8,
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(4),
                                color: active ? AppDesign.teal : Colors.grey.shade300,
                              ),
                            );
                          }),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              // Stats
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 24, 16, 0),
                  child: Row(
                    children: _stats.map((s) => Expanded(
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: AppDesign.softShadow(tint: AppDesign.teal),
                        ),
                        child: Column(
                          children: [
                            Text(s.value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppDesign.teal)),
                            const SizedBox(height: 2),
                            Text(s.label, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Colors.grey.shade600), textAlign: TextAlign.center),
                          ],
                        ),
                      ),
                    )).toList(),
                  ),
                ),
              ),

              // Galerie horizontale
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.only(top: 28),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('NOTRE ÉTABLISSEMENT', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppDesign.teal, letterSpacing: 1.2)),
                            const SizedBox(height: 4),
                            Text('L\'excellence du CHU', style: Theme.of(context).textTheme.titleLarge),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        height: 270,
                        child: ListView.builder(
                          scrollDirection: Axis.horizontal,
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          itemCount: _galleryItems.length,
                          itemBuilder: (context, i) {
                            final item = _galleryItems[i];
                            return ShowcaseImageCard(
                              icon: item.icon,
                              label: item.label,
                              accent: item.color,
                              width: i == 0 ? 240 : 200,
                              height: 270,
                              onTap: _goLogin,
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Bento mobile
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(15, 20, 15, 0),
                  child: Column(
                    children: [
                      SizedBox(
                        height: 200,
                        child: Row(
                          children: [
                            ShowcaseBentoTile(icon: Icons.apartment_rounded, label: 'CHU connecté', accent: AppDesign.navy, flex: 3, onTap: _goLogin),
                            ShowcaseBentoTile(icon: Icons.medical_services_rounded, label: 'Médecins', accent: AppDesign.teal, flex: 2, onTap: _goLogin),
                          ],
                        ),
                      ),
                      SizedBox(
                        height: 120,
                        child: Row(
                          children: [
                            ShowcaseBentoTile(icon: Icons.science_rounded, label: 'Labo', accent: Colors.purple, flex: 2, onTap: _goLogin),
                            ShowcaseBentoTile(icon: Icons.local_pharmacy_rounded, label: 'Pharmacie', accent: Colors.indigo, flex: 2, onTap: _goLogin),
                            ShowcaseBentoTile(icon: Icons.favorite_rounded, label: 'Soins', accent: Colors.pink, flex: 2, onTap: _goLogin),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Feature chips
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(0, 24, 0, 0),
                  child: SizedBox(
                    height: 44,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemCount: _features.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 10),
                      itemBuilder: (context, i) {
                        final f = _features[i];
                        return Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(colors: [f.color.withValues(alpha: 0.12), f.color.withValues(alpha: 0.05)]),
                            borderRadius: BorderRadius.circular(22),
                            border: Border.all(color: f.color.withValues(alpha: 0.2)),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(f.icon, size: 16, color: f.color),
                              const SizedBox(width: 6),
                              Text(f.label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: f.color)),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ),

              // CTA buttons
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Prêt à commencer ?', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 6),
                      Text('Inscription gratuite en 2 minutes.', style: Theme.of(context).textTheme.bodyMedium),
                      const SizedBox(height: 20),
                      ProButton(label: 'Se connecter', icon: Icons.login_rounded, onPressed: _goLogin),
                      const SizedBox(height: 12),
                      ProButton(label: 'Créer mon compte patient', outlined: true, icon: Icons.person_add_rounded, onPressed: () => Navigator.pushNamed(context, '/register')),
                    ],
                  ),
                ),
              ),

              // Services grid
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(20, 32, 20, 12),
                sliver: SliverToBoxAdapter(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Découvrez nos services', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 4),
                      Text('Connectez-vous pour accéder à chaque service.', style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
              ),
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                sliver: SliverGrid(
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: 14,
                    crossAxisSpacing: 14,
                    childAspectRatio: 0.78,
                  ),
                  delegate: SliverChildListDelegate([
                    PortalServiceTile(title: 'Rendez-vous', subtitle: 'Planifiez avec un spécialiste', icon: Icons.event_available_rounded, accent: AppDesign.teal, onTap: _goLogin),
                    PortalServiceTile(title: 'Dossier médical', subtitle: 'Historique & diagnostics', icon: Icons.assignment_rounded, accent: AppDesign.navy, onTap: _goLogin),
                    PortalServiceTile(title: 'Laboratoire', subtitle: 'Résultats PDF instantanés', icon: Icons.science_rounded, accent: Colors.purple, onTap: _goLogin),
                    PortalServiceTile(title: 'Ordonnances', subtitle: 'Suivi des traitements', icon: Icons.local_pharmacy_rounded, accent: Colors.indigo, onTap: _goLogin),
                    PortalServiceTile(title: 'Facturation', subtitle: 'Paiement Mobile Money', icon: Icons.account_balance_wallet_rounded, accent: Colors.orange, onTap: _goLogin),
                    PortalServiceTile(title: 'Messagerie', subtitle: 'Contactez votre médecin', icon: Icons.chat_rounded, accent: Colors.teal, onTap: _goLogin),
                  ]),
                ),
              ),

              // How it works — avec image
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(24),
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        boxShadow: AppDesign.softShadow(elevation: 1.2),
                      ),
                      child: Column(
                        children: [
                          SizedBox(
                            height: 130,
                            width: double.infinity,
                            child: Stack(
                              fit: StackFit.expand,
                              children: [
                                const DecoratedBox(
                                  decoration: BoxDecoration(gradient: AppDesign.heroPremiumGradient),
                                ),
                                Positioned(
                                  right: 16,
                                  bottom: -10,
                                  child: Icon(
                                    Icons.help_center_rounded,
                                    size: 90,
                                    color: Colors.white.withValues(alpha: 0.15),
                                  ),
                                ),
                                const Positioned(
                                  left: 20,
                                  bottom: 18,
                                  child: Text(
                                    'Comment ça marche ?',
                                    style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.all(20),
                            child: Column(
                              children: [
                                _buildStep(1, 'Créez votre compte', 'Inscription gratuite — code OTP par e-mail.'),
                                _buildStep(2, 'Explorez vos services', 'RDV, labo, messagerie centralisés.'),
                                _buildStep(3, 'Suivez votre santé', 'Notifications et rappels médicaments.'),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),

              // Trust banner avec image
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 0, 20, 100),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(20),
                    child: SizedBox(
                      height: 120,
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          Container(
                            decoration: const BoxDecoration(
                              gradient: LinearGradient(
                                colors: [Color(0xFF0B1F3A), Color(0xFF0D9488)],
                              ),
                            ),
                          ),
                          Positioned(
                            right: 12,
                            top: -8,
                            child: Icon(
                              Icons.verified_user_rounded,
                              size: 80,
                              color: Colors.white.withValues(alpha: 0.12),
                            ),
                          ),
                          const Center(
                            child: Padding(
                              padding: EdgeInsets.symmetric(horizontal: 20),
                              child: Text(
                                'JWT · MFA · Chiffrement AES-256 · Conformité RGPD',
                                textAlign: TextAlign.center,
                                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.white, height: 1.4),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),

          // Sticky bottom CTA
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Container(
              padding: EdgeInsets.fromLTRB(20, 12, 20, MediaQuery.of(context).padding.bottom + 12),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.95),
                border: Border(top: BorderSide(color: Colors.grey.shade200)),
                boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.06), blurRadius: 16, offset: const Offset(0, -4))],
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text(AppConfig.appName, style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14, color: AppDesign.textPrimary)),
                        Text(AppConfig.institution, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  MouseRegion(
                    cursor: SystemMouseCursors.click,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: AppDesign.buttonShineGradient,
                        borderRadius: BorderRadius.circular(14),
                        boxShadow: [
                          BoxShadow(color: AppDesign.teal.withValues(alpha: 0.4), blurRadius: 14, offset: const Offset(0, 6)),
                        ],
                      ),
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: _goLogin,
                          borderRadius: BorderRadius.circular(14),
                          child: const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                            child: Text('Connexion', style: TextStyle(fontWeight: FontWeight.w700, color: Colors.white)),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep(int num, String title, String desc) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AppDesign.teal, AppDesign.navy],
              ),
              borderRadius: BorderRadius.circular(12),
              boxShadow: AppDesign.softShadow(tint: AppDesign.teal),
            ),
            child: Center(child: Text('$num', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 16))),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: AppDesign.textPrimary)),
                const SizedBox(height: 2),
                Text(desc, style: TextStyle(fontSize: 12, color: Colors.grey.shade600, height: 1.35)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
