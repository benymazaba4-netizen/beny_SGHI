import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/push_service.dart';
import '../theme/app_design.dart';
import '../widgets/pro_components.dart';
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _api = ApiService();
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;
  String _error = '';
  bool _consent = true;

  final _username = TextEditingController();
  final _password = TextEditingController();
  final _firstName = TextEditingController();
  final _lastName = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _address = TextEditingController();
  DateTime? _birthDate;

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    _firstName.dispose();
    _lastName.dispose();
    _email.dispose();
    _phone.dispose();
    _address.dispose();
    super.dispose();
  }

  Future<void> _pickBirthDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime(now.year - 30),
      firstDate: DateTime(1920),
      lastDate: now,
      locale: const Locale('fr', 'FR'),
    );
    if (picked != null) setState(() => _birthDate = picked);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _birthDate == null) {
      setState(() => _error = _birthDate == null ? 'Date de naissance requise' : '');
      return;
    }
    setState(() {
      _loading = true;
      _error = '';
    });

    try {
      final result = await _api.register({
        'username': _username.text.trim(),
        'password': _password.text,
        'first_name': _firstName.text.trim(),
        'last_name': _lastName.text.trim(),
        'email': _email.text.trim(),
        'telephone': _phone.text.trim(),
        'adresse': _address.text.trim(),
        'date_naissance': _birthDate!.toIso8601String().split('T').first,
        'consentement_donnees': _consent,
      });

      if (!mounted) return;
      if (result['success'] == true) {
        await PushNotificationService.instance.registerAfterLogin();
        Navigator.pushReplacementNamed(context, '/home');
      } else {
        setState(() => _error = result['error']?.toString() ?? 'Erreur inscription');
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (e) {
      if (mounted) setState(() => _error = 'Erreur inattendue : $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: AppDesign.meshBackground),
        child: CustomScrollView(
          slivers: [
            SliverAppBar(
              expandedHeight: 180,
              pinned: true,
              flexibleSpace: FlexibleSpaceBar(
                title: const Text('Inscription patient', style: TextStyle(fontWeight: FontWeight.w800)),
                background: Stack(
                  fit: StackFit.expand,
                  children: [
                    const DecoratedBox(decoration: BoxDecoration(gradient: AppDesign.heroPremiumGradient)),
                    Positioned(
                      right: 20,
                      bottom: 30,
                      child: Icon(Icons.person_add_rounded, size: 80, color: Colors.white.withValues(alpha: 0.18)),
                    ),
                    Container(decoration: const BoxDecoration(gradient: AppDesign.heroOverlay)),
                  ],
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: ProGlassCard(
                  padding: const EdgeInsets.all(24),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text('Créer votre compte', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 22)),
                        const SizedBox(height: 6),
                        Text('Accédez à votre dossier médical en ligne.', style: Theme.of(context).textTheme.bodyMedium),
                        const SizedBox(height: 20),
                        Row(
                          children: [
                            Expanded(child: TextFormField(controller: _firstName, decoration: const InputDecoration(labelText: 'Prénom *'), validator: _req)),
                            const SizedBox(width: 12),
                            Expanded(child: TextFormField(controller: _lastName, decoration: const InputDecoration(labelText: 'Nom *'), validator: _req)),
                          ],
                        ),
                        const SizedBox(height: 12),
                        TextFormField(controller: _username, decoration: const InputDecoration(labelText: 'Nom d\'utilisateur *'), validator: _req),
                        const SizedBox(height: 12),
                        TextFormField(controller: _password, obscureText: true, decoration: const InputDecoration(labelText: 'Mot de passe * (8+)'), validator: (v) => (v == null || v.length < 8) ? '8 caractères minimum' : null),
                        const SizedBox(height: 12),
                        TextFormField(
                          controller: _email,
                          keyboardType: TextInputType.emailAddress,
                          decoration: const InputDecoration(labelText: 'Email *'),
                          validator: (v) {
                            if (v == null || v.trim().isEmpty) return 'E-mail requis pour les codes OTP';
                            if (!v.contains('@')) return 'E-mail invalide';
                            return null;
                          },
                        ),
                        const SizedBox(height: 12),
                        TextFormField(controller: _phone, decoration: const InputDecoration(labelText: 'Téléphone *'), validator: _req),
                        const SizedBox(height: 12),
                        ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(_birthDate == null ? 'Date de naissance *' : 'Né(e) le ${_birthDate!.day}/${_birthDate!.month}/${_birthDate!.year}'),
                          trailing: const Icon(Icons.calendar_today_rounded, color: AppDesign.teal),
                          onTap: _pickBirthDate,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: Colors.grey.shade200)),
                        ),
                        const SizedBox(height: 12),
                        TextFormField(controller: _address, maxLines: 2, decoration: const InputDecoration(labelText: 'Adresse *'), validator: _req),
                        const SizedBox(height: 12),
                        CheckboxListTile(
                          contentPadding: EdgeInsets.zero,
                          value: _consent,
                          onChanged: (v) => setState(() => _consent = v ?? false),
                          title: const Text('J\'accepte le traitement sécurisé de mes données médicales.', style: TextStyle(fontSize: 13)),
                          controlAffinity: ListTileControlAffinity.leading,
                          activeColor: AppDesign.teal,
                        ),
                        if (_error.isNotEmpty) ...[const SizedBox(height: 12), ProErrorBanner(message: _error)],
                        const SizedBox(height: 20),
                        ProButton(label: 'Créer mon compte', icon: Icons.person_add_rounded, loading: _loading, onPressed: _loading ? null : _submit),
                        TextButton(
                          onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
                          child: const Text('Déjà inscrit ? Se connecter'),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String? _req(String? v) => (v == null || v.trim().isEmpty) ? 'Requis' : null;
}
