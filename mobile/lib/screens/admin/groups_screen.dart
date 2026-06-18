import 'package:flutter/material.dart';

import '../../api.dart';
import '../../theme.dart';
import 'admin_ui.dart';

/// Manage churches and the Bible study groups under them. A group must belong
/// to a church, so churches are created first.
class GroupsScreen extends StatefulWidget {
  const GroupsScreen({super.key});
  @override
  State<GroupsScreen> createState() => _GroupsScreenState();
}

class _GroupsScreenState extends State<GroupsScreen> {
  List<dynamic> _churches = [];
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
      final c = await Api.churches();
      final g = await Api.groups();
      setState(() {
        _churches = c;
        _groups = g;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _churchName(int id) {
    final c = _churches.firstWhere((x) => x['id'] == id, orElse: () => null);
    return c == null ? '—' : c['name'];
  }

  Future<void> _addChurch() async {
    final name = await promptText(context, title: 'New church', label: 'Church name');
    if (name == null) return;
    try {
      await Api.createChurch(name);
      await _load();
    } catch (e) {
      if (mounted) toast(context, e.toString());
    }
  }

  Future<void> _addGroup() async {
    if (_churches.isEmpty) {
      toast(context, 'Add a church first.');
      return;
    }
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _GroupSheet(churches: _churches),
    );
    if (created == true) _load();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: AppColors.danger)));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          _SectionHeader(
              title: 'Churches', actionLabel: 'Add', onAction: _addChurch),
          if (_churches.isEmpty)
            const _Empty('No churches yet.')
          else
            ..._churches.map((c) => Card(
                  child: ListTile(
                    leading: const Icon(Icons.church, color: AppColors.gold),
                    title: Text(c['name']),
                  ),
                )),
          const SizedBox(height: 20),
          _SectionHeader(title: 'Groups', actionLabel: 'Add', onAction: _addGroup),
          if (_groups.isEmpty)
            const _Empty('No groups yet.')
          else
            ..._groups.map((g) => Card(
                  child: ListTile(
                    leading: const Icon(Icons.groups, color: AppColors.gold),
                    title: Text(g['name']),
                    subtitle: Text([
                      _churchName(g['church_id']),
                      if (g['meeting_day'] != null) g['meeting_day'],
                    ].join(' · ')),
                  ),
                )),
          const SizedBox(height: 80),
        ],
      ),
    );
  }
}

class _GroupSheet extends StatefulWidget {
  final List<dynamic> churches;
  const _GroupSheet({required this.churches});
  @override
  State<_GroupSheet> createState() => _GroupSheetState();
}

class _GroupSheetState extends State<_GroupSheet> {
  final _name = TextEditingController();
  int? _churchId;
  String? _meetingDay;
  bool _busy = false;

  static const _days = [
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'
  ];

  @override
  void initState() {
    super.initState();
    if (widget.churches.length == 1) _churchId = widget.churches.first['id'];
  }

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _busy = true);
    try {
      await Api.createGroup(
        churchId: _churchId!,
        name: _name.text.trim(),
        meetingDay: _meetingDay,
      );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() => _busy = false);
      if (mounted) toast(context, e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final valid = _churchId != null && _name.text.trim().isNotEmpty;
    return Padding(
      padding: EdgeInsets.only(
          left: 16, right: 16, top: 8,
          bottom: MediaQuery.of(context).viewInsets.bottom + 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('New group', style: bold(18)),
          const SizedBox(height: 12),
          DropdownButtonFormField<int>(
            value: _churchId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Church *'),
            items: widget.churches
                .map((c) => DropdownMenuItem<int>(value: c['id'] as int, child: Text(c['name'])))
                .toList(),
            onChanged: (v) => setState(() => _churchId = v),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _name,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(labelText: 'Group name *'),
          ),
          const SizedBox(height: 10),
          DropdownButtonFormField<String>(
            value: _meetingDay,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Meeting day (optional)'),
            items: _days
                .map((d) => DropdownMenuItem<String>(value: d, child: Text(d)))
                .toList(),
            onChanged: (v) => setState(() => _meetingDay = v),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: _busy || !valid ? null : _submit,
              child: Text(_busy ? 'Saving…' : 'Create group'),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final String actionLabel;
  final VoidCallback onAction;
  const _SectionHeader(
      {required this.title, required this.actionLabel, required this.onAction});
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, left: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: bold(16, AppColors.gold)),
          TextButton.icon(
            onPressed: onAction,
            icon: const Icon(Icons.add, size: 18),
            label: Text(actionLabel),
          ),
        ],
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  final String text;
  const _Empty(this.text);
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        child: Text(text, style: const TextStyle(color: AppColors.textMuted)),
      );
}
