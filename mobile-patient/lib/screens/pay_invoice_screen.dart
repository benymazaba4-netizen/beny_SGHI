import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_design.dart';
import '../utils/formatters.dart';
import '../widgets/pro_components.dart';

class PayInvoiceScreen extends StatefulWidget {
  const PayInvoiceScreen({super.key, required this.facture});

  final Map<String, dynamic> facture;

  @override
  State<PayInvoiceScreen> createState() => _PayInvoiceScreenState();
}

class _PayInvoiceScreenState extends State<PayInvoiceScreen> {
  final _api = ApiService();
  final _phoneController = TextEditingController();
  final _amountController = TextEditingController();
  String _mode = 'MTN';
  bool _submitting = false;
  String _message = '';
  bool _success = false;

  @override
  void initState() {
    super.initState();
    final reste = widget.facture['montant_restant'];
    if (reste != null) {
      _amountController.text = '${(reste as num).toInt()}';
    }
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _amountController.dispose();
    super.dispose();
  }

  Future<void> _payer() async {
    setState(() {
      _submitting = true;
      _message = '';
    });
    try {
      final endpoint = _mode == 'ESPECES' || _mode == 'CARTE'
          ? '/billing/paiements'
          : '/billing/paiements/mobile-money';
      final res = await _api.post(endpoint, {
        'facture_id': widget.facture['id'],
        'mode_paiement': _mode,
        'montant': num.parse(_amountController.text),
        'numero_telephone': _phoneController.text.trim(),
        'operateur': _mode,
      });
      setState(() {
        _success = true;
        _message = res['message']?.toString() ?? 'Paiement enregistré';
      });
      if (mounted) {
        await Future.delayed(const Duration(milliseconds: 800));
        Navigator.pop(context, true);
      }
    } catch (e) {
      setState(() {
        _success = false;
        _message = '$e';
      });
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final f = widget.facture;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Payer ma facture'),
        backgroundColor: AppDesign.navy,
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          ProGlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(f['numero_facture']?.toString() ?? 'Facture', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
                const SizedBox(height: 8),
                Text('Statut : ${f['statut']}', style: const TextStyle(color: AppDesign.textSecondary)),
                Text('Part patient : ${formatFcfa(f['montant_patient'])}', style: const TextStyle(color: AppDesign.textSecondary)),
                Text('Reste à payer : ${formatFcfa(f['montant_restant'])}', style: TextStyle(fontWeight: FontWeight.w700, color: Colors.orange.shade800)),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Text('Mode de paiement', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: ['MTN', 'AIRTEL', 'CARTE', 'ESPECES'].map((m) {
              final selected = _mode == m;
              return ChoiceChip(
                label: Text(m),
                selected: selected,
                onSelected: (_) => setState(() => _mode = m),
                selectedColor: AppDesign.teal.withValues(alpha: 0.2),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _amountController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Montant (FCFA)', border: OutlineInputBorder()),
          ),
          if (_mode == 'MTN' || _mode == 'AIRTEL') ...[
            const SizedBox(height: 12),
            TextField(
              controller: _phoneController,
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(labelText: 'Numéro $_mode', border: const OutlineInputBorder()),
            ),
          ],
          if (_message.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(_message, style: TextStyle(color: _success ? Colors.green.shade700 : Colors.red.shade700)),
          ],
          const SizedBox(height: 24),
          ProButton(
            label: _submitting ? 'Traitement...' : 'Confirmer le paiement',
            icon: Icons.payment_rounded,
            onPressed: _submitting ? null : _payer,
          ),
          const SizedBox(height: 12),
          Text(
            'Simulation Mobile Money — aucun débit réel. Référence générée côté serveur.',
            style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
