import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../api.dart';
import '../session.dart';

class TestRecognitionScreen extends StatefulWidget {
  const TestRecognitionScreen({super.key});
  @override
  State<TestRecognitionScreen> createState() => _TestRecognitionScreenState();
}

class _TestRecognitionScreenState extends State<TestRecognitionScreen> {
  File? _file;
  bool _persist = false;
  bool _busy = false;
  String? _error;
  Map<String, dynamic>? _result;

  Future<void> _pick(ImageSource source) async {
    final picked = await ImagePicker().pickImage(source: source, imageQuality: 90);
    if (picked != null) setState(() => _file = File(picked.path));
  }

  Future<void> _run() async {
    final bsg = Session.instance.activeBsgId;
    if (bsg == null) {
      setState(() => _error = 'No group selected.');
      return;
    }
    if (_file == null) return;
    setState(() {
      _busy = true;
      _error = null;
      _result = null;
    });
    try {
      final r = await Api.testRecognition(bsg, _file!, _persist);
      setState(() => _result = r);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Run recognition on a photo without Telegram. Tick "Save" to record attendance.',
            style: TextStyle(color: Colors.grey)),
        const SizedBox(height: 12),
        if (_file != null)
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.file(_file!, height: 220, width: double.infinity, fit: BoxFit.cover),
          ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => _pick(ImageSource.camera),
                icon: const Icon(Icons.camera_alt),
                label: const Text('Camera'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => _pick(ImageSource.gallery),
                icon: const Icon(Icons.photo_library),
                label: const Text('Gallery'),
              ),
            ),
          ],
        ),
        SwitchListTile(
          value: _persist,
          onChanged: (v) => setState(() => _persist = v),
          title: const Text('Save attendance & visitors'),
          subtitle: const Text('Off = dry run'),
          contentPadding: EdgeInsets.zero,
        ),
        FilledButton(
          onPressed: (_file == null || _busy) ? null : _run,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Text(_busy ? 'Running…' : 'Run recognition'),
          ),
        ),
        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!, style: const TextStyle(color: Colors.red)),
        ],
        if (_result != null) ...[
          const SizedBox(height: 16),
          _resultCard(_result!),
        ],
      ],
    );
  }

  Widget _resultCard(Map<String, dynamic> r) {
    final members = (r['recognized_members'] as List);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(r['bsg_name'] ?? '',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('Faces: ${r['faces_detected']}  ·  Recognized: ${members.length}  ·  '
                'Visitors: ${r['visitors']}  ·  ${r['saved'] == true ? 'Saved ✓' : 'Dry-run'}'),
            const Divider(),
            if (members.isEmpty)
              const Text('No members recognized.')
            else
              ...members.map((m) => ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.check_circle, color: Colors.green),
                    title: Text(m['name']),
                    trailing: Text('${((m['confidence'] ?? 0) * 100).round()}%'),
                  )),
            if ((r['visitors'] ?? 0) > 0)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text('${r['visitors']} unmatched face(s) sent to Visitors for review.',
                    style: const TextStyle(color: Colors.orange)),
              ),
          ],
        ),
      ),
    );
  }
}
