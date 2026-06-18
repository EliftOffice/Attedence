import 'package:flutter/material.dart';

import '../session.dart';
import 'login_screen.dart';
import 'admin/groups_screen.dart';
import 'admin/leaders_screen.dart';
import 'admin/locations_screen.dart';
import 'admin/settings_screen.dart';

/// Admin management panel — distinct from the leader operational screens.
/// Lets the admin manage groups, leaders, address lookups, and runtime settings.
class AdminHomeScreen extends StatefulWidget {
  const AdminHomeScreen({super.key});
  @override
  State<AdminHomeScreen> createState() => _AdminHomeScreenState();
}

class _AdminHomeScreenState extends State<AdminHomeScreen> {
  int _index = 0;

  final _tabs = const [
    _Tab('Groups', Icons.church, GroupsScreen()),
    _Tab('Leaders', Icons.badge, LeadersScreen()),
    _Tab('Locations', Icons.location_city, LocationsScreen()),
    _Tab('Settings', Icons.settings, SettingsScreen()),
  ];

  Future<void> _logout() async {
    await Session.instance.clear();
    if (mounted) {
      Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const LoginScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    final tab = _tabs[_index];
    return Scaffold(
      appBar: AppBar(
        title: Text(tab.label),
        actions: [
          IconButton(onPressed: _logout, icon: const Icon(Icons.logout)),
        ],
      ),
      body: KeyedSubtree(key: ValueKey(tab.label), child: tab.screen),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: _tabs
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
  const _Tab(this.label, this.icon, this.screen);
}
