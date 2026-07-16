import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../theme/app_design.dart';
import '../widgets/pro_components.dart';

class CreateAppointmentScreen extends StatefulWidget {
  const CreateAppointmentScreen({super.key, required this.patientId});

  final int patientId;

  @override
  State<CreateAppointmentScreen> createState() => _CreateAppointmentScreenState();
}

class _CreateAppointmentScreenState extends State<CreateAppointmentScreen> {
  final _api = ApiService();
  final _motifController = TextEditingController();
  List<dynamic> _medecins = [];
  List<dynamic> _services = [];
  int? _medecinId;
  int? _serviceId;
  DateTime? _dateTime;
  bool _loading = true;
  bool _submitting = false;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _loadLookups();
  }

  @override
  void dispose() {
    _motifController.dispose();
    super.dispose();
  }

  Future<void> _loadLookups() async {
    try {
      final results = await Future.wait([
        _api.getPaginated('/auth/medecins'),
        _api.getPaginated('/hospital/services'),
      ]);
      setState(() {
        _medecins = results[0].items;
        _services = results[1].items;
      });
    } catch (e) {
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _pickDateTime() async {
    HapticFeedback.selectionClick();
    final now = DateTime.now();
    final date = await showDatePicker(
      context: context,
      initialDate: now.add(const Duration(days: 1)),
      firstDate: now,
      lastDate: now.add(const Duration(days: 180)),
    );
    if (date == null || !mounted) return;
    HapticFeedback.selectionClick();
    final time = await showTimePicker(context: context, initialTime: const TimeOfDay(hour: 9, minute: 0));
    if (time == null) return;
    HapticFeedback.selectionClick();
    setState(() => _dateTime = DateTime(date.year, date.month, date.day, time.hour, time.minute));
  }

  Future<void> _submit() async {
    if (_medecinId == null || _serviceId == null || _dateTime == null || _motifController.text.trim().isEmpty) {
      HapticFeedback.lightImpact();
      setState(() => _error = 'Veuillez remplir tous les champs');
      return;
    }
    setState(() {
      _submitting = true;
      _error = '';
    });
    try {
      await _api.post('/appointments/rendez-vous', {
        'patient_id': widget.patientId,
        'medecin_id': _medecinId,
        'service_id': _serviceId,
        'date_heure': _dateTime!.toUtc().toIso8601String(),
        'motif': _motifController.text.trim(),
      });
      HapticFeedback.mediumImpact();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Rendez-vous confirmé avec succès'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppDesign.teal,
          ),
        );
        await Future<void>.delayed(const Duration(milliseconds: 400));
        Navigator.pop(context, true);
      }
    } catch (e) {
      HapticFeedback.lightImpact();
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: AppDesign.meshBackground),
        child: CustomScrollView(
          slivers: [
            const ProHeroSliverAppBar(title: 'Nouveau RDV', icon: Icons.event_available_rounded),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: _loading
                    ? const Padding(padding: EdgeInsets.all(48), child: Center(child: CircularProgressIndicator(color: AppDesign.teal)))
                    : ProGlassCard(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text('Planifier un rendez-vous', style: Theme.of(context).textTheme.titleLarge),
                            const SizedBox(height: 6),
                            Text('Choisissez un médecin, un service et un créneau.', style: Theme.of(context).textTheme.bodyMedium),
                            const SizedBox(height: 20),
                            DropdownButtonFormField<int>(
                              initialValue: _medecinId,
                              decoration: const InputDecoration(labelText: 'Médecin *', prefixIcon: Icon(Icons.person_rounded, color: AppDesign.teal)),
                              items: _medecins.map((m) {
                                final map = m as Map<String, dynamic>;
                                final label = map['first_name'] != null
                                    ? 'Dr ${map['first_name']} ${map['last_name']}'
                                    : map['username']?.toString() ?? 'Médecin';
                                return DropdownMenuItem(value: map['id'] as int, child: Text(label));
                              }).toList(),
                              onChanged: (v) {
                                HapticFeedback.selectionClick();
                                setState(() => _medecinId = v);
                              },
                            ),
                            const SizedBox(height: 14),
                            DropdownButtonFormField<int>(
                              initialValue: _serviceId,
                              decoration: const InputDecoration(labelText: 'Service *', prefixIcon: Icon(Icons.local_hospital_rounded, color: AppDesign.teal)),
                              items: _services.map((s) {
                                final map = s as Map<String, dynamic>;
                                return DropdownMenuItem(
                                  value: map['id'] as int,
                                  child: Text('${map['code']} — ${map['nom']}'),
                                );
                              }).toList(),
                              onChanged: (v) {
                                HapticFeedback.selectionClick();
                                setState(() => _serviceId = v);
                              },
                            ),
                            const SizedBox(height: 14),
                            ListTile(
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: Colors.grey.shade200)),
                              tileColor: AppDesign.surface,
                              title: Text(
                                _dateTime == null
                                    ? 'Date et heure *'
                                    : '${_dateTime!.day}/${_dateTime!.month}/${_dateTime!.year} à ${_dateTime!.hour}:${_dateTime!.minute.toString().padLeft(2, '0')}',
                                style: const TextStyle(fontWeight: FontWeight.w600),
                              ),
                              trailing: const Icon(Icons.calendar_month_rounded, color: AppDesign.teal),
                              onTap: _pickDateTime,
                            ),
                            const SizedBox(height: 14),
                            TextField(
                              controller: _motifController,
                              maxLines: 3,
                              decoration: const InputDecoration(
                                labelText: 'Motif *',
                                alignLabelWithHint: true,
                                prefixIcon: Icon(Icons.notes_rounded, color: AppDesign.teal),
                              ),
                            ),
                            if (_error.isNotEmpty) ...[const SizedBox(height: 14), ProErrorBanner(message: _error)],
                            const SizedBox(height: 24),
                            ProButton(
                              label: 'Confirmer le rendez-vous',
                              icon: Icons.check_circle_rounded,
                              loading: _submitting,
                              onPressed: _submitting ? null : _submit,
                            ),
                          ],
                        ),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
