import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../api.dart';
import '../../theme.dart';
import 'admin_ui.dart';

/// Manage BSG leaders: list them with their group, register a new leader for a
/// group that has none, replace a leader (deactivate then add a new one), and
/// issue a Telegram link code.
class LeadersScreen extends StatefulWidget {
  const LeadersScreen({super.key});
  @override
  State<LeadersScreen> createState() => _LeadersScreenState();
}

class _LeadersScreenState extends State<LeadersScreen> {
  List<dynamic> _leaders = [];
  List<dynamic> _groups = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final g = await Api.groups();
      final l = await Api.leaders();
      setState(() {
        _groups = g;
        _leaders = l;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _groupName(int id) {
    final g = _groups.firstWhere((x) => x['id'] == id, orElse: () => null);
    return g == null ? '—' : g['name'];
  }

  /// Groups that don't yet have a leader (eligible for a new assignment).
  List<dynamic> get _freeGroups {
    final taken = _leaders.map((l) => l['bsg_id']).toSet();
    return _groups.where((g) => !taken.contains(g['id'])).toList();
  }

  Future<void> _addLeader() async {
    if (_freeGroups.isEmpty) {
      toast(context,
          _groups.isEmpty ? 'Add a group first.' : 'All groups already have a leader.');
      return;
    }
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _LeaderSheet(groups: _freeGroups),
    );
    if (created == true) _load();
  }

  Future<void> _deactivate(dynamic leader) async {
    final ok = await confirm(context,
        title: 'Deactivate leader?',
        message:
            '${leader['name']} will lose login access and their group (${_groupName(leader['bsg_id'])}) '
            'will be free for a new leader. The group and its members are not deleted.',
        confirmLabel: 'Deactivate');
    if (!ok) return;
    try {
      await Api.deactivateLeader(leader['id']);
      if (mounted) toast(context, 'Leader deactivated.');
      await _load();
    } catch (e) {
      if (mounted) toast(context, e.toString());
    }
  }

  Future<void> _linkCode(dynamic leader) async {
    try {
      final res = await Api.leaderLinkCode(leader['id']);
      if (!mounted) return;
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Telegram link code'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SelectableText(res['link_code'] ?? '',
                  style: bold(28, AppColors.gold)),
              const SizedBox(height: 8),
              Text(res['instructions'] ?? '',
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                Clipboard.setData(ClipboardData(text: res['link_code'] ?? ''));
                Navigator.pop(ctx);
                toast(context, 'Code copied.');
              },
              child: const Text('Copy'),
            ),
            FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('Done')),
          ],
        ),
      );
    } catch (e) {
      if (mounted) toast(context, e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _body(),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addLeader,
        icon: const Icon(Icons.person_add),
        label: const Text('Add leader'),
      ),
    );
  }

  Widget _body() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: AppColors.danger)));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: _leaders.isEmpty
          ? ListView(children: const [
              SizedBox(height: 160),
              Center(child: Text('No leaders yet. Tap “Add leader”.')),
            ])
          : ListView(
              padding: const EdgeInsets.all(12),
              children: [
                ..._leaders.map((l) {
                  final linked = l['telegram_user_id'] != null;
                  return Card(
                    child: ListTile(
                      leading: const CircleAvatar(child: Icon(Icons.person)),
                      title: Text(l['name']),
                      subtitle: Text([
                        _groupName(l['bsg_id']),
                        if (linked) 'Telegram linked',
                      ].join(' · ')),
                      trailing: PopupMenuButton<String>(
                        onSelected: (v) {
                          if (v == 'deactivate') _deactivate(l);
                          if (v == 'link') _linkCode(l);
                        },
                        itemBuilder: (_) => const [
                          PopupMenuItem(value: 'link', child: Text('Telegram link code')),
                          PopupMenuItem(value: 'deactivate', child: Text('Deactivate')),
                        ],
                      ),
                    ),
                  );
                }),
                const SizedBox(height: 80),
              ],
            ),
    );
  }
}

class _LeaderSheet extends StatefulWidget {
  final List<dynamic> groups;
  const _LeaderSheet({required this.groups});
  @override
  State<_LeaderSheet> createState() => _LeaderSheetState();
}

class _LeaderSheetState extends State<_LeaderSheet> {
  final _name = TextEditingController();
  final _mobile = TextEditingController();
  final _password = TextEditingController();
  int? _bsgId;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    if (widget.groups.length == 1) _bsgId = widget.groups.first['id'];
  }

  @override
  void dispose() {
    _name.dispose();
    _mobile.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _busy = true);
    try {
      await Api.createLeader(
        bsgId: _bsgId!,
        name: _name.text.trim(),
        mobile: _mobile.text.trim(),
        password: _password.text,
      );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() => _busy = false);
      if (mounted) toast(context, e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final valid = _bsgId != null &&
        _name.text.trim().isNotEmpty &&
        _mobile.text.trim().isNotEmpty &&
        _password.text.length >= 4;
    return Padding(
      padding: EdgeInsets.only(
          left: 16, right: 16, top: 8,
          bottom: MediaQuery.of(context).viewInsets.bottom + 16),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Register leader', style: bold(18)),
            const Text('Creates the leader’s login and assigns them to a group.',
                style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
            const SizedBox(height: 12),
            DropdownButtonFormField<int>(
              value: _bsgId,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Group *'),
              items: widget.groups
                  .map((g) => DropdownMenuItem<int>(value: g['id'] as int, child: Text(g['name'])))
                  .toList(),
              onChanged: (v) => setState(() => _bsgId = v),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _name,
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(labelText: 'Leader name *'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _mobile,
              keyboardType: TextInputType.phone,
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(labelText: 'Mobile number *'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _password,
              obscureText: true,
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(labelText: 'Password * (min 4 chars)'),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _busy || !valid ? null : _submit,
                child: Text(_busy ? 'Saving…' : 'Create leader'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
