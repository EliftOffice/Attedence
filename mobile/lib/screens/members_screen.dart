import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../api.dart';
import '../session.dart';
import '../widgets/auth_image.dart';

/// Register members and build their facial profile (upload reference photos).
/// Leader works in their own group; admin in the group chosen in the app bar.
class MembersScreen extends StatefulWidget {
  const MembersScreen({super.key});
  @override
  State<MembersScreen> createState() => _MembersScreenState();
}

class _MembersScreenState extends State<MembersScreen> {
  List<dynamic> _members = [];
  bool _loading = true;
  String? _error;
  int? _busyMemberId;

  int? get _bsg => Session.instance.activeBsgId;

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
      final m = await Api.members(bsgId: _bsg);
      setState(() => _members = m);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _register() async {
    if (_bsg == null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('No group selected.')));
      return;
    }
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _RegisterSheet(bsgId: _bsg!),
    );
    if (created == true) _load();
  }

  Future<void> _addPhotos(dynamic member) async {
    final picked = await ImagePicker().pickMultiImage(imageQuality: 90);
    if (picked.isEmpty) return;
    setState(() => _busyMemberId = member['id']);
    try {
      await Api.addMemberPhotos(member['id'], picked.map((x) => File(x.path)).toList());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Added ${picked.length} photo(s) to ${member['name']}.')));
      }
      await _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _busyMemberId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _body(),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _register,
        icon: const Icon(Icons.person_add),
        label: const Text('Register'),
      ),
    );
  }

  Widget _body() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: Colors.red)));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: _members.isEmpty
          ? ListView(children: const [
              SizedBox(height: 160),
              Center(child: Text('No members yet. Tap Register to add one.')),
            ])
          : ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: _members.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (_, i) {
                final m = _members[i];
                final count = m['photo_count'] ?? 0;
                final inactive = m['status'] != 'active';
                return ListTile(
                  leading: count > 0
                      ? AuthImage(url: '/api/v1/members/${m['id']}/photo', size: 48)
                      : const CircleAvatar(child: Icon(Icons.person)),
                  title: Text('${m['name']} ${m['surname'] ?? ''}'.trim()),
                  subtitle: Text([
                    if (m['mobile_number'] != null) m['mobile_number'],
                    '$count photo(s)',
                    if (inactive) 'inactive',
                  ].join(' · ')),
                  trailing: _busyMemberId == m['id']
                      ? const SizedBox(
                          width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                      : IconButton(
                          icon: const Icon(Icons.add_a_photo),
                          tooltip: 'Add reference photos',
                          onPressed: () => _addPhotos(m),
                        ),
                );
              },
            ),
    );
  }
}

class _RegisterSheet extends StatefulWidget {
  final int bsgId;
  const _RegisterSheet({required this.bsgId});
  @override
  State<_RegisterSheet> createState() => _RegisterSheetState();
}

class _RegisterSheetState extends State<_RegisterSheet> {
  final _name = TextEditingController();
  final _surname = TextEditingController();
  final _mobile = TextEditingController();
  List<dynamic> _cities = [];
  List<dynamic> _streets = [];
  int? _cityId;
  int? _streetId;
  final List<File> _photos = [];
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    Api.cities().then((c) => setState(() => _cities = c)).catchError((_) {});
  }

  @override
  void dispose() {
    _name.dispose();
    _surname.dispose();
    _mobile.dispose();
    super.dispose();
  }

  Future<void> _onCity(int? id) async {
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

  Future<void> _pickPhotos() async {
    final picked = await ImagePicker().pickMultiImage(imageQuality: 90);
    if (picked.isNotEmpty) {
      setState(() => _photos.addAll(picked.map((x) => File(x.path))));
    }
  }

  Future<void> _submit() async {
    setState(() => _busy = true);
    try {
      final m = await Api.createMember(
        name: _name.text.trim(),
        surname: _surname.text.trim().isEmpty ? null : _surname.text.trim(),
        mobile: _mobile.text.trim().isEmpty ? null : _mobile.text.trim(),
        cityId: _cityId,
        streetId: _streetId,
        bsgId: widget.bsgId,
      );
      String msg = 'Member created.';
      if (_photos.isNotEmpty) {
        try {
          final res = await Api.addMemberPhotos(m['id'], _photos);
          msg = 'Member created with ${res['photo_count']} reference photo(s).';
        } catch (e) {
          msg = 'Member created, but photo upload failed: $e';
        }
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
        Navigator.pop(context, true);
      }
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
            const Text('Register member',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const Text('Only name is required.',
                style: TextStyle(fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 12),
            TextField(
              controller: _name,
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(labelText: 'Name *', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _surname,
              decoration: const InputDecoration(labelText: 'Surname', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _mobile,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'Mobile', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _cityId,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'City', border: OutlineInputBorder()),
              items: _cities
                  .map((c) => DropdownMenuItem<int>(value: c['id'] as int, child: Text(c['name'])))
                  .toList(),
              onChanged: _onCity,
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _streetId,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Street', border: OutlineInputBorder()),
              items: _streets
                  .map((s) => DropdownMenuItem<int>(value: s['id'] as int, child: Text(s['name'])))
                  .toList(),
              onChanged: _cityId == null ? null : (v) => setState(() => _streetId = v),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _pickPhotos,
              icon: const Icon(Icons.add_a_photo),
              label: Text(_photos.isEmpty
                  ? 'Add reference photos (optional)'
                  : '${_photos.length} photo(s) selected'),
            ),
            if (_photos.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: SizedBox(
                  height: 64,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: _photos
                        .map((f) => Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(8),
                                child: Image.file(f, width: 64, height: 64, fit: BoxFit.cover),
                              ),
                            ))
                        .toList(),
                  ),
                ),
              ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _busy || _name.text.trim().isEmpty ? null : _submit,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Text(_busy ? 'Saving…' : 'Create member'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
