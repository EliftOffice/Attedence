import 'package:flutter/material.dart';

import '../api.dart';
import '../session.dart';
import '../widgets/auth_image.dart';

class TodayScreen extends StatefulWidget {
  const TodayScreen({super.key});
  @override
  State<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen> {
  Map<String, dynamic>? _data;
  String? _error;
  bool _loading = true;

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
      final d = await Api.today(bsgId: Session.instance.activeBsgId);
      setState(() => _data = d);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (Session.instance.isAdmin && Session.instance.selectedBsgId == null) {
      return const Center(child: Text('Select a group (top-right) to view today.'));
    }
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return _ErrorView(message: _error!, onRetry: _load);
    }
    final d = _data!;
    final present = (d['present'] as List);
    final absent = (d['absent'] as List);
    final visitors = (d['new_visitors'] as List);

    return DefaultTabController(
      length: 3,
      child: Column(
        children: [
          Material(
            color: Theme.of(context).colorScheme.surface,
            child: TabBar(
              tabs: [
                Tab(text: 'Present (${present.length})'),
                Tab(text: 'Absent (${absent.length})'),
                Tab(text: 'New Visitors (${visitors.length})'),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            child: Row(
              children: [
                Text('${d['bsg_name']} · ${d['meeting_date']}',
                    style: const TextStyle(color: Colors.grey)),
                const Spacer(),
                IconButton(onPressed: _load, icon: const Icon(Icons.refresh)),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: [
                _MemberGrid(items: present, emptyText: 'No one marked present yet.'),
                _MemberGrid(items: absent, emptyText: 'Everyone is present 🎉'),
                _VisitorGrid(items: visitors),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MemberGrid extends StatelessWidget {
  final List items;
  final String emptyText;
  const _MemberGrid({required this.items, required this.emptyText});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return Center(child: Text(emptyText));
    return GridView.count(
      crossAxisCount: 3,
      padding: const EdgeInsets.all(12),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 0.68,
      children: items.map((m) {
        final guest = m['is_guest'] == true;
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Stack(
              children: [
                AuthImage(url: m['photo_url'], size: 86),
                if (guest)
                  Positioned(
                    right: 0,
                    top: 0,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                          color: Colors.orange, borderRadius: BorderRadius.circular(8)),
                      child: const Text('guest',
                          style: TextStyle(color: Colors.white, fontSize: 10)),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Flexible(
              child: Text(
                '${m['name']} ${m['surname'] ?? ''}'.trim(),
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 13),
              ),
            ),
          ],
        );
      }).toList(),
    );
  }
}

class _VisitorGrid extends StatelessWidget {
  final List items;
  const _VisitorGrid({required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const Center(child: Text('No new visitors today.'));
    return Column(
      children: [
        const Padding(
          padding: EdgeInsets.all(12),
          child: Text('Resolve these in the Visitors tab — map to a member, register, or keep.',
              style: TextStyle(color: Colors.grey)),
        ),
        Expanded(
          child: GridView.count(
            crossAxisCount: 3,
            padding: const EdgeInsets.all(12),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            children: items
                .map((v) => AuthImage(url: v['crop_url'], size: 96))
                .toList(),
          ),
        ),
      ],
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 12),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
