import 'package:flutter/material.dart';

import '../api.dart';
import '../session.dart';
import 'login_screen.dart';
import 'today_screen.dart';
import 'visitors_screen.dart';
import 'members_screen.dart';
import 'test_recognition_screen.dart';
import 'reports_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final s = Session.instance;
  int _index = 0;
  List<dynamic> _groups = [];

  @override
  void initState() {
    super.initState();
    if (s.isAdmin) {
      Api.groups().then((g) {
        setState(() {
          _groups = g;
          if (g.isNotEmpty && s.selectedBsgId == null) s.selectedBsgId = g.first['id'];
        });
      }).catchError((_) {});
    }
  }

  List<_Tab> get _tabs => [
        _Tab('Today', Icons.today, const TodayScreen()),
        if (!s.isAdmin) _Tab('Visitors', Icons.how_to_reg, const VisitorsScreen()),
        _Tab('Members', Icons.group_add, const MembersScreen()),
        _Tab('Test', Icons.camera_alt, const TestRecognitionScreen()),
        _Tab('Reports', Icons.bar_chart, const ReportsScreen()),
      ];

  Future<void> _logout() async {
    await s.clear();
    if (mounted) {
      Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const LoginScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    final tabs = _tabs;
    if (_index >= tabs.length) _index = 0;
    // Keyed so children reload when the admin switches group.
    final body = KeyedSubtree(
      key: ValueKey('${tabs[_index].label}-${s.activeBsgId}'),
      child: tabs[_index].screen,
    );

    return Scaffold(
      appBar: AppBar(
        title: Text(tabs[_index].label),
        actions: [
          if (s.isAdmin && _groups.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: DropdownButton<int>(
                value: s.selectedBsgId,
                underline: const SizedBox(),
                onChanged: (v) => setState(() => s.selectedBsgId = v),
                items: _groups
                    .map((g) => DropdownMenuItem<int>(
                        value: g['id'], child: Text(g['name'])))
                    .toList(),
              ),
            ),
          IconButton(onPressed: _logout, icon: const Icon(Icons.logout)),
        ],
      ),
      body: body,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: tabs
            .map((t) => NavigationDestination(icon: Icon(t.icon), label: t.label))
            .toList(),
      ),
    );
  }
}

class _Tab {
  final String label;
  final IconData icon;
  final Widget screen;
  _Tab(this.label, this.icon, this.screen);
}
