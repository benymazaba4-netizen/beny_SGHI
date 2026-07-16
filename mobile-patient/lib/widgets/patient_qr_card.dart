import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../theme/app_design.dart';

class PatientQrCard extends StatelessWidget {
  const PatientQrCard({
    super.key,
    required this.qrCodeBase64,
    required this.expiresAt,
    required this.loading,
    required this.onGenerate,
  });

  final String? qrCodeBase64;
  final String? expiresAt;
  final bool loading;
  final VoidCallback onGenerate;

  Uint8List? get _imageBytes {
    final raw = qrCodeBase64;
    if (raw == null || raw.isEmpty) return null;
    return base64Decode(raw);
  }

  @override
  Widget build(BuildContext context) {
    final bytes = _imageBytes;
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.white, AppDesign.teal.withValues(alpha: 0.08)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppDesign.teal.withValues(alpha: 0.18)),
        boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.06), blurRadius: 18, offset: const Offset(0, 8))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                backgroundColor: AppDesign.teal.withValues(alpha: 0.12),
                child: Icon(Icons.qr_code_2_rounded, color: AppDesign.teal),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('QR dossier sécurisé', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                    Text('Token temporaire signé et chiffré', style: TextStyle(color: Colors.black54, fontSize: 12)),
                  ],
                ),
              ),
            ],
          ),
          if (bytes != null) ...[
            const SizedBox(height: 16),
            Center(
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                child: Image.memory(bytes, width: 180, height: 180, fit: BoxFit.contain),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'Expiration : ${expiresAt ?? 'fenêtre courte'}',
              style: TextStyle(color: AppDesign.navy.withValues(alpha: 0.72), fontWeight: FontWeight.w700),
            ),
          ],
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: loading ? null : onGenerate,
              icon: loading
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.shield_rounded),
              label: Text(bytes == null ? 'Générer le QR sécurisé' : 'Régénérer le QR sécurisé'),
            ),
          ),
        ],
      ),
    );
  }
}
