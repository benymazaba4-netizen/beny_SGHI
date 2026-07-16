import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../config/app_config.dart';
import '../services/api_service.dart';
import '../utils/auth_navigation.dart';
import '../theme/app_design.dart';
import '../widgets/pro_components.dart';
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> with SingleTickerProviderStateMixin {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _mfaController = TextEditingController();
  final _otpController = TextEditingController();
  final _api = ApiService();
  bool _loading = false;
  bool _mfaStep = false;
  bool _otpStep = false;
  String _otpEmailHint = '';
  bool _obscure = true;
  String _error = '';
  bool _resendLoading = false;
  int _resendCooldown = 0;
  late AnimationController _anim;

  @override
  void initState() {
    super.initState();
    _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 800))..forward();
  }

  @override
  void dispose() {
    _anim.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _mfaController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  Future<void> _submitOtp() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final result = await _api.loginOtp(_otpController.text);
      if (!mounted) return;
      if (result['success'] == true) {
        final user = await _api.getCurrentUser();
        if (!mounted) return;
        await AuthNavigation.goAfterLogin(context, user);
      } else {
        setState(() => _error = result['error']?.toString() ?? 'Code OTP invalide');
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _login({String? mfaToken}) async {
    setState(() {
      _loading = true;
      _error = '';
    });

    try {
      final result = await _api.login(
        _usernameController.text,
        _passwordController.text,
        mfaToken: mfaToken,
      );

      if (!mounted) return;

      if (result['mfa_required'] == true) {
        setState(() => _mfaStep = true);
        return;
      }

      if (result['otp_required'] == true) {
        setState(() {
          _otpStep = true;
          _mfaStep = false;
          _otpEmailHint = result['otp_email_hint']?.toString() ?? '';
          _otpController.clear();
        });
        return;
      }

      if (result['success'] == true) {
        final user = await _api.getCurrentUser();
        if (!mounted) return;
        await AuthNavigation.goAfterLogin(context, user);
      } else {
        setState(() => _error = result['error']?.toString() ?? 'Identifiants incorrects');
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (e) {
      if (mounted) setState(() => _error = 'Erreur inattendue : $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _resendOtp() async {
    setState(() {
      _resendLoading = true;
      _error = '';
    });
    try {
      final result = await _api.resendOtp();
      if (!mounted) return;
      if (result['success'] == true) {
        HapticFeedback.lightImpact();
        if (result['otp_email_hint'] != null) {
          _otpEmailHint = result['otp_email_hint'].toString();
        }
        setState(() => _resendCooldown = 60);
        for (var i = 59; i >= 0; i--) {
          await Future.delayed(const Duration(seconds: 1));
          if (!mounted) return;
          setState(() => _resendCooldown = i);
        }
      } else {
        setState(() => _error = result['error']?.toString() ?? 'Impossible de renvoyer le code');
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _resendLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          Container(decoration: const BoxDecoration(gradient: AppDesign.heroPremiumGradient)),
          Positioned(
            right: -30,
            top: 60,
            child: Icon(Icons.local_hospital_rounded, size: 180, color: Colors.white.withValues(alpha: 0.08)),
          ),
          Positioned(
            left: -40,
            bottom: 80,
            child: Container(
              width: 160,
              height: 160,
              decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withValues(alpha: 0.05)),
            ),
          ),
          SafeArea(
            child: FadeTransition(
              opacity: CurvedAnimation(parent: _anim, curve: Curves.easeOut),
              child: SlideTransition(
                position: Tween<Offset>(begin: const Offset(0, 0.06), end: Offset.zero).animate(CurvedAnimation(parent: _anim, curve: Curves.easeOutCubic)),
                child: Column(
                  children: [
                    Align(
                      alignment: Alignment.centerLeft,
                      child: TextButton.icon(
                        onPressed: () => Navigator.pushReplacementNamed(context, '/'),
                        icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 16, color: Colors.white70),
                        label: const Text('Portail', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w600)),
                      ),
                    ),
                    const Spacer(),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.fromLTRB(28, 32, 28, 28),
                        decoration: AppDesign.glassCard,
                        child: _mfaStep ? _mfaForm() : (_otpStep ? _otpForm() : _loginForm()),
                      ),
                    ),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _header() {
    return Column(
      children: [
        const ProLogo(size: 64),
        const SizedBox(height: 16),
        RichText(
          text: TextSpan(
            style: Theme.of(context).textTheme.headlineMedium,
            children: [
              TextSpan(text: '${AppConfig.appName} ', style: const TextStyle(color: AppDesign.navy)),
              TextSpan(text: AppConfig.appSubtitle, style: const TextStyle(color: AppDesign.teal)),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Text('Connexion sécurisée', style: Theme.of(context).textTheme.bodyMedium),
      ],
    );
  }

  Widget _loginForm() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _header(),
        const SizedBox(height: 28),
        ProField(controller: _usernameController, label: 'Nom d\'utilisateur', icon: Icons.person_outline_rounded),
        const SizedBox(height: 14),
        ProField(
          controller: _passwordController,
          label: 'Mot de passe',
          icon: Icons.lock_outline_rounded,
          obscure: _obscure,
          onSubmitted: () => _login(),
        ),
        Align(
          alignment: Alignment.centerRight,
          child: TextButton(
            onPressed: () => setState(() => _obscure = !_obscure),
            child: Text(_obscure ? 'Afficher' : 'Masquer', style: const TextStyle(fontSize: 12, color: AppDesign.teal)),
          ),
        ),
        const SizedBox(height: 8),
        ProButton(label: 'Se connecter', icon: Icons.login_rounded, loading: _loading, onPressed: _loading ? null : () => _login()),
        if (_error.isNotEmpty) ...[const SizedBox(height: 16), ProErrorBanner(message: _error)],
        const SizedBox(height: 20),
        Row(
          children: [
            Expanded(child: Divider(color: Colors.grey.shade300)),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Text('ou', style: TextStyle(color: Colors.grey.shade500, fontSize: 12)),
            ),
            Expanded(child: Divider(color: Colors.grey.shade300)),
          ],
        ),
        const SizedBox(height: 16),
        ProButton(label: 'Créer un compte', outlined: true, icon: Icons.person_add_alt_1_rounded, onPressed: () => Navigator.pushNamed(context, '/register')),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: AppDesign.surface, borderRadius: BorderRadius.circular(12)),
          child: Text(
            'Démo : patient / medecin / secretaire\n'
            'Mot de passe : Demo2026!\n'
            'Code de validation à 2 étapes envoyé par e-mail (vérifiez les spams).\n'
            'API : ${AppConfig.apiBaseUrl}',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 11, color: Colors.grey.shade600, height: 1.4),
          ),
        ),
      ],
    );
  }

  Widget _otpForm() {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [AppDesign.teal.withValues(alpha: 0.1), AppDesign.mint.withValues(alpha: 0.15)],
            ),
            borderRadius: BorderRadius.circular(20),
          ),
          child: const Icon(Icons.mark_email_read_rounded, size: 48, color: AppDesign.teal),
        ),
        const SizedBox(height: 16),
        Text('Validation à 2 étapes', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Text(
          'Code envoyé à ${_otpEmailHint.isNotEmpty ? _otpEmailHint : 'votre e-mail'}',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 8),
        Text(
          'Vérifiez votre boîte de réception et le dossier Spam. Le code expire dans 10 minutes.',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey.shade600, height: 1.4),
        ),
        const SizedBox(height: 4),
        Text(
          'Compte : ${_usernameController.text}',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey.shade600),
        ),
        const SizedBox(height: 20),
        TextField(
          controller: _otpController,
          keyboardType: TextInputType.number,
          maxLength: 6,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 32, letterSpacing: 12, fontWeight: FontWeight.w800, color: AppDesign.navy),
          decoration: const InputDecoration(counterText: '', hintText: '• • • • • •'),
        ),
        const SizedBox(height: 20),
        ProButton(label: 'Valider le code', loading: _loading, onPressed: _loading ? null : _submitOtp),
        TextButton(
          onPressed: (_resendLoading || _resendCooldown > 0) ? null : _resendOtp,
          child: Text(
            _resendCooldown > 0 ? 'Renvoyer dans ${_resendCooldown}s' : (_resendLoading ? 'Envoi...' : 'Renvoyer le code'),
            style: const TextStyle(color: AppDesign.teal, fontWeight: FontWeight.w600),
          ),
        ),
        TextButton(
          onPressed: () => setState(() {
            _otpStep = false;
            _error = '';
            _otpController.clear();
          }),
          child: const Text('← Retour'),
        ),
        if (_error.isNotEmpty) ...[const SizedBox(height: 12), ProErrorBanner(message: _error)],
      ],
    );
  }

  Widget _mfaForm() {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(gradient: LinearGradient(colors: [AppDesign.teal.withValues(alpha: 0.1), AppDesign.mint.withValues(alpha: 0.15)]), borderRadius: BorderRadius.circular(20)),
          child: const Icon(Icons.shield_rounded, size: 48, color: AppDesign.teal),
        ),
        const SizedBox(height: 16),
        Text('Authentification MFA', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Text('Entrez le code à 6 chiffres', style: Theme.of(context).textTheme.bodyMedium),
        const SizedBox(height: 20),
        TextField(
          controller: _mfaController,
          keyboardType: TextInputType.number,
          maxLength: 6,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 32, letterSpacing: 12, fontWeight: FontWeight.w800, color: AppDesign.navy),
          decoration: const InputDecoration(counterText: '', hintText: '• • • • • •'),
        ),
        const SizedBox(height: 20),
        ProButton(label: 'Valider', loading: _loading, onPressed: () => _login(mfaToken: _mfaController.text)),
        TextButton(onPressed: () => setState(() => _mfaStep = false), child: const Text('← Retour')),
        if (_error.isNotEmpty) ...[const SizedBox(height: 12), ProErrorBanner(message: _error)],
      ],
    );
  }
}
