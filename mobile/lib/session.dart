import 'package:shared_preferences/shared_preferences.dart';

/// Holds the logged-in session: server URL, JWT, role, name, and (for admins)
/// the currently selected group. Persisted via SharedPreferences.
class Session {
  static final Session instance = Session._();
  Session._();

  String serverUrl = 'http://10.0.2.2:8000'; // Android emulator -> host machine
  String? token;
  String? role; // admin | leader
  String? name;
  int? leaderBsgId; // leaders: their own group
  int? selectedBsgId; // admins: the group they're viewing

  bool get isLoggedIn => token != null;
  bool get isAdmin => role == 'admin';

  /// The group id to use for queries (admin's selection, or the leader's group).
  int? get activeBsgId => isAdmin ? selectedBsgId : leaderBsgId;

  Future<void> load() async {
    final p = await SharedPreferences.getInstance();
    serverUrl = p.getString('serverUrl') ?? serverUrl;
    token = p.getString('token');
    role = p.getString('role');
    name = p.getString('name');
    leaderBsgId = p.getInt('leaderBsgId');
  }

  Future<void> save() async {
    final p = await SharedPreferences.getInstance();
    await p.setString('serverUrl', serverUrl);
    if (token != null) await p.setString('token', token!);
    if (role != null) await p.setString('role', role!);
    if (name != null) await p.setString('name', name!);
    if (leaderBsgId != null) {
      await p.setInt('leaderBsgId', leaderBsgId!);
    } else {
      await p.remove('leaderBsgId');
    }
  }

  Future<void> clear() async {
    final p = await SharedPreferences.getInstance();
    final url = serverUrl;
    await p.clear();
    await p.setString('serverUrl', url); // keep server URL for next login
    token = role = name = null;
    leaderBsgId = selectedBsgId = null;
  }

  Map<String, String> get authHeaders =>
      token == null ? {} : {'Authorization': 'Bearer $token'};
}
