import 'package:flutter/material.dart';
import '../utils/formatters.dart';

class PaymentGateBanner extends StatelessWidget {
  const PaymentGateBanner({
    super.key,
    required this.pendingCount,
    this.amount,
    this.onTap,
  });

  final int pendingCount;
  final num? amount;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    if (pendingCount <= 0) return const SizedBox.shrink();

    final amountLabel = amount != null ? ' · ${formatFcfa(amount)}' : '';
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Material(
        color: Colors.red.shade50,
        borderRadius: BorderRadius.circular(18),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(18),
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: Colors.red.shade200),
            ),
            child: Row(
              children: [
                Icon(Icons.account_balance_wallet_rounded, color: Colors.red.shade700, size: 28),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'En attente de règlement',
                        style: TextStyle(
                          fontWeight: FontWeight.w800,
                          color: Colors.red.shade900,
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '$pendingCount frais à régler au secrétariat avant consultation$amountLabel',
                        style: TextStyle(color: Colors.red.shade800, fontSize: 12, height: 1.35),
                      ),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right_rounded, color: Colors.red.shade400),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class PaymentStatusChip extends StatelessWidget {
  const PaymentStatusChip({super.key, required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final paid = status == 'PAID';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: paid ? Colors.green.shade50 : Colors.red.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: paid ? Colors.green.shade200 : Colors.red.shade200),
      ),
      child: Text(
        paid ? 'Payé' : 'À régler',
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w700,
          color: paid ? Colors.green.shade800 : Colors.red.shade800,
        ),
      ),
    );
  }
}
