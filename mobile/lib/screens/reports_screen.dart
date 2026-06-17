import 'package:flutter/material.dart';

import '../api.dart';
import '../session.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});
  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  List<dynamic> _members = [];
  List<dynamic> _absentees = [];
  Map<String, dynamic>? _visitorStats;
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
    final bsg = Session.instance.activeBsgId;
    try {
      final results = await Future.wait([
        Api.memberAttendance(bsgId: bsg),
        Api.absentees(bsgId: bsg),
        Api.visitorStats(bsgId: bsg),
      ]);
      setState(() {
        _members = results[0] as List;
        _absentees = results[1] as List;
        _visitorStats = results[2] as Map<String, dynamic>;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (Session.instance.isAdmin && Session.instance.selectedBsgId == null) {
      return const Center(child: Text('Select a group (top-right).'));
    }
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: Colors.red)));
    }
    final vs = _visitorStats ?? {};
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Visitors', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  Text('Total ${vs['total_visitor_entries'] ?? 0} · '
                      'Pending ${vs['pending'] ?? 0} · Kept ${vs['kept'] ?? 0} · '
                      'Promoted ${vs['promoted'] ?? 0} · Mapped ${vs['mapped'] ?? 0}'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          const Text('Attendance %', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ..._members.map((m) => Card(
                child: ListTile(
                  leading: const Icon(Icons.person),
                  title: Text(m['name']),
                  subtitle: Text('${m['meetings_attended']}/${m['meetings_held']} meetings'),
                  trailing: Text('${(m['attendance_pct'] as num).toStringAsFixed(0)}%',
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                ),
              )),
          const SizedBox(height: 16),
          const Text('Long-term absentees', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          if (_absentees.isEmpty)
            const Text('None 🎉', style: TextStyle(color: Colors.grey))
          else
            ..._absentees.map((a) => Card(
                  child: ListTile(
                    leading: const Icon(Icons.warning_amber, color: Colors.orange),
                    title: Text(a['name']),
                    subtitle: Text('Last attended: ${a['last_attended'] ?? '—'}'),
                    trailing: Text('${a['meetings_missed_in_row']} missed'),
                  ),
                )),
        ],
      ),
    );
  }
}
