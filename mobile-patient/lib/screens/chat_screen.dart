import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_design.dart';
import '../widgets/empty_placeholder.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _api = ApiService();
  final _controller = TextEditingController();
  List<dynamic> _conversations = [];
  Map<String, dynamic>? _activeConv;
  List<dynamic> _messages = [];
  int? _userId;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final user = await _api.getCurrentUser();
    _userId = user?['id'] as int?;
    await _loadConversations();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _loadConversations() async {
    setState(() => _loading = true);
    try {
      final data = await _api.get('/messaging/conversations');
      setState(() {
        _conversations = data as List<dynamic>;
        if (_conversations.isNotEmpty && _activeConv == null) {
          _activeConv = _conversations.first as Map<String, dynamic>;
        }
      });
      if (_activeConv != null) await _loadMessages(_activeConv!['id'] as int);
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _loadMessages(int convId) async {
    final data = await _api.get('/messaging/conversations/$convId/messages');
    if (mounted) setState(() => _messages = data as List<dynamic>);
  }

  Future<void> _send() async {
    if (_activeConv == null || _controller.text.trim().isEmpty) return;
    await _api.post(
      '/messaging/conversations/${_activeConv!['id']}/messages',
      {'contenu': _controller.text.trim()},
    );
    _controller.clear();
    await _loadMessages(_activeConv!['id'] as int);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: AppDesign.teal, strokeWidth: 2.5));
    }
    if (_conversations.isEmpty) {
      return const EmptyPlaceholder(
        icon: Icons.chat_bubble_rounded,
        title: 'Aucune conversation',
        subtitle: 'Votre médecin pourra vous contacter après une consultation.',
      );
    }

    return Column(
      children: [
        if (_activeConv != null)
          Container(
            width: double.infinity,
            margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              gradient: AppDesign.primaryGradient,
              borderRadius: BorderRadius.circular(18),
              boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.2), blurRadius: 12, offset: const Offset(0, 4))],
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(12)),
                  child: const Icon(Icons.medical_services_rounded, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_activeConv!['medecin'] as String? ?? 'Médecin', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
                      Text('Messagerie sécurisée', style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 11)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        if (_conversations.length > 1)
          SizedBox(
            height: 52,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: _conversations.length,
              itemBuilder: (context, i) {
                final c = _conversations[i] as Map<String, dynamic>;
                final selected = _activeConv?['id'] == c['id'];
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(c['medecin'] as String? ?? 'Médecin'),
                    selected: selected,
                    onSelected: (_) {
                      setState(() => _activeConv = c);
                      _loadMessages(c['id'] as int);
                    },
                    selectedColor: AppDesign.teal.withValues(alpha: 0.15),
                    checkmarkColor: AppDesign.teal,
                    labelStyle: TextStyle(fontWeight: selected ? FontWeight.w700 : FontWeight.w500, color: selected ? AppDesign.teal : AppDesign.textSecondary),
                  ),
                );
              },
            ),
          ),
        Expanded(
          child: _messages.isEmpty
              ? const EmptyPlaceholder(
                  icon: Icons.forum_outlined,
                  title: 'Démarrez la conversation',
                  subtitle: 'Envoyez un message à votre médecin.',
                )
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
                  itemCount: _messages.length,
                  itemBuilder: (context, i) {
                    final m = _messages[i] as Map<String, dynamic>;
                    final isMine = _userId != null && m['expediteur_id'] == _userId;
                    return Align(
                      alignment: isMine ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        constraints: const BoxConstraints(maxWidth: 300),
                        decoration: BoxDecoration(
                          gradient: isMine
                              ? AppDesign.cardGradient
                              : const LinearGradient(colors: [Colors.white, AppDesign.surface]),
                          borderRadius: BorderRadius.only(
                            topLeft: Radius.circular(isMine ? 20 : 4),
                            topRight: Radius.circular(isMine ? 4 : 20),
                            bottomLeft: const Radius.circular(20),
                            bottomRight: const Radius.circular(20),
                          ),
                          border: Border.all(color: isMine ? Colors.transparent : AppDesign.teal.withValues(alpha: 0.12)),
                          boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.05), blurRadius: 8, offset: const Offset(0, 2))],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (!isMine)
                              Text(
                                '${m['expediteur']}',
                                style: const TextStyle(fontWeight: FontWeight.w700, color: AppDesign.teal, fontSize: 11),
                              ),
                            if (!isMine) const SizedBox(height: 4),
                            Text(
                              '${m['contenu']}',
                              style: TextStyle(color: isMine ? Colors.white : AppDesign.textPrimary, height: 1.4),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
        Container(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border(top: BorderSide(color: AppDesign.teal.withValues(alpha: 0.1))),
            boxShadow: [BoxShadow(color: AppDesign.navy.withValues(alpha: 0.06), blurRadius: 12, offset: const Offset(0, -4))],
          ),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  decoration: InputDecoration(
                    hintText: 'Votre message...',
                    filled: true,
                    fillColor: AppDesign.surface,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                  ),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 10),
              DecoratedBox(
                decoration: BoxDecoration(
                  gradient: AppDesign.cardGradient,
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: AppDesign.teal.withValues(alpha: 0.35), blurRadius: 8)],
                ),
                child: IconButton(
                  onPressed: _send,
                  icon: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
