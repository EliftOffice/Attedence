import 'package:flutter/material.dart';

import '../api.dart';
import '../widgets/auth_image.dart';

class VisitorsScreen extends StatefulWidget {
  const VisitorsScreen({super.key});
  @override
  State<VisitorsScreen> createState() => _VisitorsScreenState();
}

class _VisitorsScreenState extends State<VisitorsScreen> {
  List<dynamic> _visitors = [];
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
      final v = await Api.visitors();
      setState(() => _visitors = v);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _openResolve(dynamic visitor) async {
    final changed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _ResolveSheet(visitor: visitor),
    );
    if (changed == true) _load();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: Colors.red)));
    }
    if (_visitors.isEmpty) {
      return RefreshIndicator(
        onRefresh: _load,
        child: ListView(children: const [
          SizedBox(height: 200),
          Center(child: Text('No pending visitors 🎉')),
        ]),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: GridView.count(
        crossAxisCount: 2,
        padding: const EdgeInsets.all(12),
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
        childAspectRatio: 0.82,
        children: _visitors.map((v) {
          return Card(
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: () => _openResolve(v),
              child: Column(
                children: [
                  Expanded(
                    child: SizedBox(
                      width: double.infinity,
                      child: AuthImage(url: v['crop_url'], size: 160, radius: 0),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(8),
                    child: Text('Meeting ${v['meeting_date']}',
                        style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ),
                  const Padding(
                    padding: EdgeInsets.only(bottom: 8),
                    child: Text('Tap to resolve',
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _ResolveSheet extends StatefulWidget {
  final dynamic visitor;
  const _ResolveSheet({required this.visitor});
  @override
  State<_ResolveSheet> createState() => _ResolveSheetState();
}

class _ResolveSheetState extends State<_ResolveSheet> {
  List<dynamic> _suggestions = [];
  bool _loading = true;
  bool _busy = false;
  final _newName = TextEditingController();
  final _newSurname = TextEditingController();
  final _newMobile = TextEditingController();
  List<dynamic> _cities = [];
  List<dynamic> _streets = [];
  int? _cityId;
  int? _streetId;

  int get _id => widget.visitor['id'];

  @override
  void initState() {
    super.initState();
    Api.suggestions(_id).then((s) {
      setState(() {
        _suggestions = s;
        _loading = false;
      });
    }).catchError((_) {
      setState(() => _loading = false);
    });
    Api.cities().then((c) => setState(() => _cities = c)).catchError((_) {});
  }

  Future<void> _onCityChanged(int? id) async {
    setState(() {
      _cityId = id;
      _streetId = null;
      _streets = [];
    });
    if (id != null) {
      try {
        final s = await Api.streets(id);
        setState(() => _streets = s);
      } catch (_) {}
    }
  }

  @override
  void dispose() {
    _newName.dispose();
    _newSurname.dispose();
    _newMobile.dispose();
    super.dispose();
  }

  Future<void> _do(Future<void> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() => _busy = false);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
          left: 16, right: 16, top: 8,
          bottom: MediaQuery.of(context).viewInsets.bottom + 16),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                AuthImage(url: widget.visitor['crop_url'], size: 84),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text('Who is this?',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Text('Suggested members (compare faces):',
                style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 8),
            if (_loading)
              const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()))
            else if (_suggestions.isEmpty)
              const Text('No similar members found.')
            else
              ..._suggestions.map((s) => _suggestionRow(s)),
            const Divider(height: 28),
            const Text('Register as NEW member (your group):',
                style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            const Text('Only name is required.',
                style: TextStyle(fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 8),
            TextField(
              controller: _newName,
              // Rebuild on every keystroke so the Create button enables.
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(
                  labelText: 'Name *', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _newSurname,
              decoration: const InputDecoration(
                  labelText: 'Surname', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _newMobile,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                  labelText: 'Mobile', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _cityId,
              isExpanded: true,
              decoration: const InputDecoration(
                  labelText: 'City', border: OutlineInputBorder()),
              items: _cities
                  .map((c) => DropdownMenuItem<int>(
                      value: c['id'] as int, child: Text(c['name'])))
                  .toList(),
              onChanged: _onCityChanged,
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _streetId,
              isExpanded: true,
              decoration: const InputDecoration(
                  labelText: 'Street', border: OutlineInputBorder()),
              items: _streets
                  .map((s) => DropdownMenuItem<int>(
                      value: s['id'] as int, child: Text(s['name'])))
                  .toList(),
              onChanged: _cityId == null ? null : (v) => setState(() => _streetId = v),
            ),
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _busy || _newName.text.trim().isEmpty
                    ? null
                    : () => _do(() => Api.promoteVisitor(
                          _id,
                          _newName.text.trim(),
                          surname: _newSurname.text.trim().isEmpty ? null : _newSurname.text.trim(),
                          mobile: _newMobile.text.trim().isEmpty ? null : _newMobile.text.trim(),
                          cityId: _cityId,
                          streetId: _streetId,
                        )),
                child: const Text('Create & mark present'),
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _busy ? null : () => _do(() => Api.keepVisitor(_id)),
              icon: const Icon(Icons.person_outline),
              label: const Text('Keep as one-time visitor'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _suggestionRow(dynamic s) {
    final sameGroup = s['same_group'] == true;
    final pct = ((s['similarity'] ?? 0) * 100).round();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          AuthImage(url: s['photo_url'], size: 56),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(s['name'], style: const TextStyle(fontWeight: FontWeight.w600)),
                Text(
                  sameGroup ? 'your group · match $pct%' : '${s['bsg_name']} · match $pct%',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
          ),
          if (sameGroup)
            FilledButton(
              onPressed: _busy ? null : () => _do(() => Api.mapVisitor(_id, s['member_id'], false)),
              child: const Text('Map'),
            )
          else
            Wrap(
              spacing: 4,
              children: [
                OutlinedButton(
                  onPressed: _busy ? null : () => _do(() => Api.mapVisitor(_id, s['member_id'], false)),
                  child: const Text('Guest'),
                ),
                FilledButton(
                  onPressed: _busy ? null : () => _do(() => Api.mapVisitor(_id, s['member_id'], true)),
                  child: const Text('Move'),
                ),
              ],
            ),
        ],
      ),
    );
  }
}
