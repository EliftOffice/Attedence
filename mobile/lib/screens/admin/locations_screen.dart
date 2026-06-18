import 'package:flutter/material.dart';

import '../../api.dart';
import '../../theme.dart';
import 'admin_ui.dart';

/// Manage the address lookups used in the member form: cities, and the streets
/// under each city (cascading). Admin can add and delete.
class LocationsScreen extends StatefulWidget {
  const LocationsScreen({super.key});
  @override
  State<LocationsScreen> createState() => _LocationsScreenState();
}

class _LocationsScreenState extends State<LocationsScreen> {
  List<dynamic> _cities = [];
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
      final c = await Api.cities();
      setState(() => _cities = c);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _addCity() async {
    final name = await promptText(context, title: 'New city', label: 'City name');
    if (name == null) return;
    try {
      await Api.createCity(name);
      await _load();
    } catch (e) {
      if (mounted) toast(context, e.toString());
    }
  }

  Future<void> _deleteCity(dynamic city) async {
    final ok = await confirm(context,
        title: 'Delete city?',
        message: 'Delete “${city['name']}” and its streets from the lookups?');
    if (!ok) return;
    try {
      await Api.deleteCity(city['id']);
      await _load();
    } catch (e) {
      if (mounted) toast(context, e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _body(),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addCity,
        icon: const Icon(Icons.add_location_alt),
        label: const Text('Add city'),
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
      child: _cities.isEmpty
          ? ListView(children: const [
              SizedBox(height: 160),
              Center(child: Text('No cities yet. Tap “Add city”.')),
            ])
          : ListView(
              padding: const EdgeInsets.all(12),
              children: [
                ..._cities.map((c) => Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: _CityTile(
                        city: c,
                        onDeleteCity: () => _deleteCity(c),
                      ),
                    )),
                const SizedBox(height: 80),
              ],
            ),
    );
  }
}

/// A city as an expandable tile; loads its streets on first expansion.
class _CityTile extends StatefulWidget {
  final dynamic city;
  final VoidCallback onDeleteCity;
  const _CityTile({required this.city, required this.onDeleteCity});
  @override
  State<_CityTile> createState() => _CityTileState();
}

class _CityTileState extends State<_CityTile> {
  List<dynamic>? _streets;
  bool _loading = false;

  Future<void> _loadStreets() async {
    setState(() => _loading = true);
    try {
      final s = await Api.streets(widget.city['id']);
      setState(() => _streets = s);
    } catch (e) {
      if (mounted) toast(context, e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _addStreet() async {
    final name = await promptText(context, title: 'New street', label: 'Street name');
    if (name == null) return;
    try {
      await Api.createStreet(widget.city['id'], name);
      await _loadStreets();
    } catch (e) {
      if (mounted) toast(context, e.toString());
    }
  }

  Future<void> _deleteStreet(dynamic street) async {
    final ok = await confirm(context,
        title: 'Delete street?', message: 'Delete “${street['name']}”?');
    if (!ok) return;
    try {
      await Api.deleteStreet(street['id']);
      await _loadStreets();
    } catch (e) {
      if (mounted) toast(context, e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      shape: const Border(),
      collapsedShape: const Border(),
      leading: const Icon(Icons.location_city, color: AppColors.gold),
      title: Text(widget.city['name']),
      onExpansionChanged: (open) {
        if (open && _streets == null) _loadStreets();
      },
      children: [
        if (_loading)
          const Padding(
            padding: EdgeInsets.all(12),
            child: Center(child: CircularProgressIndicator()),
          )
        else ...[
          if ((_streets ?? []).isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8, horizontal: 16),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text('No streets yet.', style: TextStyle(color: AppColors.textMuted)),
              ),
            )
          else
            ...(_streets ?? []).map((s) => ListTile(
                  dense: true,
                  leading: const Icon(Icons.signpost_outlined, size: 20),
                  title: Text(s['name']),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete_outline, color: AppColors.danger),
                    onPressed: () => _deleteStreet(s),
                  ),
                )),
          OverflowBar(
            alignment: MainAxisAlignment.spaceBetween,
            children: [
              TextButton.icon(
                onPressed: _addStreet,
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Add street'),
              ),
              TextButton.icon(
                onPressed: widget.onDeleteCity,
                icon: const Icon(Icons.delete_outline, size: 18, color: AppColors.danger),
                label: const Text('Delete city',
                    style: TextStyle(color: AppColors.danger)),
              ),
            ],
          ),
        ],
      ],
    );
  }
}
