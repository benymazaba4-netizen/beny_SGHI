import 'package:intl/intl.dart';

String formatFcfa(num? amount) {
  final value = amount ?? 0;
  return '${NumberFormat('#,###', 'fr_FR').format(value)} FCFA';
}

String formatDate(String? iso) {
  if (iso == null || iso.isEmpty) return '—';
  try {
    final dt = DateTime.parse(iso);
    return DateFormat('dd/MM/yyyy HH:mm', 'fr_FR').format(dt.toLocal());
  } catch (_) {
    return iso;
  }
}

String formatDateShort(String? iso) {
  if (iso == null || iso.isEmpty) return '—';
  try {
    final dt = DateTime.parse(iso);
    return DateFormat('dd/MM/yyyy', 'fr_FR').format(dt.toLocal());
  } catch (_) {
    return iso;
  }
}
