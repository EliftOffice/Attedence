import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

import 'session.dart';

/// Thin API client over the FastAPI backend. All calls use the saved server URL
/// and attach the JWT. Image URLs are returned as absolute and loaded by widgets
/// with the auth header (see AuthImage).
class Api {
  static final s = Session.instance;

  static String _u(String path) => '${s.serverUrl}$path';
  static String abs(String relativeOrNull) =>
      relativeOrNull.startsWith('http') ? relativeOrNull : '${s.serverUrl}$relativeOrNull';

  static Map<String, String> get _jsonHeaders =>
      {'Content-Type': 'application/json', ...s.authHeaders};

  static dynamic _decode(http.Response r) {
    if (r.statusCode >= 200 && r.statusCode < 300) {
      return r.body.isEmpty ? null : jsonDecode(r.body);
    }
    String detail;
    try {
      final body = jsonDecode(r.body);
      detail = body is Map && body['detail'] != null ? body['detail'].toString() : r.body;
    } catch (_) {
      detail = r.body;
    }
    throw ApiException(r.statusCode, detail);
  }

  // ---- Auth ----
  static Future<void> login(String mobile, String password) async {
    final r = await http.post(
      Uri.parse(_u('/api/v1/auth/login')),
      body: {'username': mobile, 'password': password},
    );
    final data = _decode(r);
    s.token = data['access_token'];
    s.role = data['role'];
    s.name = data['name'];
    await s.save();
    await me();
  }

  static Future<void> me() async {
    final r = await http.get(Uri.parse(_u('/api/v1/auth/me')), headers: s.authHeaders);
    final data = _decode(r);
    s.role = data['role'];
    s.name = data['name'];
    s.leaderBsgId = data['leader_bsg_id'];
    await s.save();
  }

  // ---- Groups (admin) ----
  static Future<List<dynamic>> groups() async {
    final r = await http.get(Uri.parse(_u('/api/v1/setup/groups')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  // ---- Today (present / absent / new visitors) ----
  static Future<Map<String, dynamic>> today({int? bsgId}) async {
    final q = bsgId != null ? '?bsg_id=$bsgId' : '';
    final r = await http.get(Uri.parse(_u('/api/v1/attendance/today$q')), headers: s.authHeaders);
    return _decode(r) as Map<String, dynamic>;
  }

  // ---- Visitors (leader) ----
  static Future<List<dynamic>> visitors() async {
    final r = await http.get(Uri.parse(_u('/api/v1/visitors')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  static Future<List<dynamic>> suggestions(int visitorId) async {
    final r = await http.get(
        Uri.parse(_u('/api/v1/visitors/$visitorId/suggestions')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  static Future<void> mapVisitor(int visitorId, int memberId, bool move) async {
    final r = await http.post(Uri.parse(_u('/api/v1/visitors/$visitorId/map')),
        headers: _jsonHeaders,
        body: jsonEncode({'member_id': memberId, 'move_to_my_group': move}));
    _decode(r);
  }

  static Future<void> promoteVisitor(
    int visitorId,
    String name, {
    String? surname,
    String? mobile,
    int? cityId,
    int? streetId,
  }) async {
    final r = await http.post(Uri.parse(_u('/api/v1/visitors/$visitorId/promote')),
        headers: _jsonHeaders,
        body: jsonEncode({
          'name': name,
          'surname': surname,
          'mobile_number': mobile,
          'city_id': cityId,
          'street_id': streetId,
        }));
    _decode(r);
  }

  // ---- Lookups (City / Street) ----
  static Future<List<dynamic>> cities() async {
    final r = await http.get(Uri.parse(_u('/api/v1/lookups/cities')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  static Future<List<dynamic>> streets(int cityId) async {
    final r = await http.get(
        Uri.parse(_u('/api/v1/lookups/streets?city_id=$cityId')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  // ---- Members ----
  static Future<List<dynamic>> members({int? bsgId}) async {
    final q = bsgId != null ? '?bsg_id=$bsgId' : '';
    final r = await http.get(Uri.parse(_u('/api/v1/members$q')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  static Future<Map<String, dynamic>> createMember({
    required String name,
    String? surname,
    String? mobile,
    int? cityId,
    int? streetId,
    int? bsgId,
  }) async {
    final r = await http.post(Uri.parse(_u('/api/v1/members')),
        headers: _jsonHeaders,
        body: jsonEncode({
          'name': name,
          'surname': surname,
          'mobile_number': mobile,
          'city_id': cityId,
          'street_id': streetId,
          'bsg_id': bsgId,
        }));
    return _decode(r) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> addMemberPhotos(int memberId, List<File> files) async {
    final req = http.MultipartRequest(
        'POST', Uri.parse(_u('/api/v1/members/$memberId/photos')));
    req.headers.addAll(s.authHeaders);
    for (final f in files) {
      req.files.add(await http.MultipartFile.fromPath('files', f.path));
    }
    final streamed = await req.send();
    final r = await http.Response.fromStream(streamed);
    return _decode(r) as Map<String, dynamic>;
  }

  static Future<void> keepVisitor(int visitorId) async {
    final r = await http.post(Uri.parse(_u('/api/v1/visitors/$visitorId/keep')),
        headers: _jsonHeaders, body: '{}');
    _decode(r);
  }

  // ---- Test recognition ----
  static Future<Map<String, dynamic>> testRecognition(
      int bsgId, File file, bool persist) async {
    final req = http.MultipartRequest('POST', Uri.parse(_u('/api/v1/recognition/test')));
    req.headers.addAll(s.authHeaders);
    req.fields['bsg_id'] = '$bsgId';
    req.fields['persist'] = '$persist';
    req.files.add(await http.MultipartFile.fromPath('file', file.path));
    final streamed = await req.send();
    final r = await http.Response.fromStream(streamed);
    return _decode(r) as Map<String, dynamic>;
  }

  // ---- Reports ----
  static Future<List<dynamic>> memberAttendance({int? bsgId}) async {
    final q = bsgId != null ? '?bsg_id=$bsgId' : '';
    final r = await http.get(
        Uri.parse(_u('/api/v1/reports/member-attendance$q')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  static Future<Map<String, dynamic>> visitorStats({int? bsgId}) async {
    final q = bsgId != null ? '?bsg_id=$bsgId' : '';
    final r = await http.get(
        Uri.parse(_u('/api/v1/reports/visitor-stats$q')), headers: s.authHeaders);
    return _decode(r) as Map<String, dynamic>;
  }

  static Future<List<dynamic>> absentees({int? bsgId}) async {
    final q = bsgId != null ? '?bsg_id=$bsgId' : '';
    final r = await http.get(
        Uri.parse(_u('/api/v1/reports/absentees$q')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  // ==================== Admin management ====================

  // ---- Churches ----
  static Future<List<dynamic>> churches() async {
    final r = await http.get(Uri.parse(_u('/api/v1/setup/churches')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  static Future<Map<String, dynamic>> createChurch(String name) async {
    final r = await http.post(Uri.parse(_u('/api/v1/setup/churches')),
        headers: _jsonHeaders, body: jsonEncode({'name': name}));
    return _decode(r) as Map<String, dynamic>;
  }

  // ---- Groups (create; list via groups()) ----
  static Future<Map<String, dynamic>> createGroup(
      {required int churchId, required String name, String? meetingDay}) async {
    final r = await http.post(Uri.parse(_u('/api/v1/setup/groups')),
        headers: _jsonHeaders,
        body: jsonEncode(
            {'church_id': churchId, 'name': name, 'meeting_day': meetingDay}));
    return _decode(r) as Map<String, dynamic>;
  }

  // ---- Leaders ----
  static Future<List<dynamic>> leaders() async {
    final r = await http.get(Uri.parse(_u('/api/v1/setup/leaders')), headers: s.authHeaders);
    return _decode(r) as List<dynamic>;
  }

  static Future<Map<String, dynamic>> createLeader(
      {required int bsgId,
      required String name,
      required String mobile,
      required String password}) async {
    final r = await http.post(Uri.parse(_u('/api/v1/setup/leaders')),
        headers: _jsonHeaders,
        body: jsonEncode({
          'bsg_id': bsgId,
          'name': name,
          'mobile_number': mobile,
          'password': password,
        }));
    return _decode(r) as Map<String, dynamic>;
  }

  static Future<void> deactivateLeader(int leaderId) async {
    final r = await http.post(
        Uri.parse(_u('/api/v1/setup/leaders/$leaderId/deactivate')),
        headers: _jsonHeaders,
        body: '{}');
    _decode(r);
  }

  static Future<Map<String, dynamic>> leaderLinkCode(int leaderId) async {
    final r = await http.post(
        Uri.parse(_u('/api/v1/setup/leaders/$leaderId/telegram-link-code')),
        headers: _jsonHeaders,
        body: '{}');
    return _decode(r) as Map<String, dynamic>;
  }

  // ---- Locations (cities / streets) ----
  static Future<Map<String, dynamic>> createCity(String name) async {
    final r = await http.post(Uri.parse(_u('/api/v1/lookups/cities')),
        headers: _jsonHeaders, body: jsonEncode({'name': name}));
    return _decode(r) as Map<String, dynamic>;
  }

  static Future<void> deleteCity(int id) async {
    final r = await http.delete(Uri.parse(_u('/api/v1/lookups/cities/$id')),
        headers: s.authHeaders);
    _decode(r);
  }

  static Future<Map<String, dynamic>> createStreet(int cityId, String name) async {
    final r = await http.post(Uri.parse(_u('/api/v1/lookups/streets')),
        headers: _jsonHeaders, body: jsonEncode({'city_id': cityId, 'name': name}));
    return _decode(r) as Map<String, dynamic>;
  }

  static Future<void> deleteStreet(int id) async {
    final r = await http.delete(Uri.parse(_u('/api/v1/lookups/streets/$id')),
        headers: s.authHeaders);
    _decode(r);
  }

  // ---- Runtime settings ----
  static Future<Map<String, dynamic>> getSettings() async {
    final r = await http.get(Uri.parse(_u('/api/v1/setup/settings')), headers: s.authHeaders);
    return _decode(r) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> body) async {
    final r = await http.put(Uri.parse(_u('/api/v1/setup/settings')),
        headers: _jsonHeaders, body: jsonEncode(body));
    return _decode(r) as Map<String, dynamic>;
  }
}

class ApiException implements Exception {
  final int status;
  final String detail;
  ApiException(this.status, this.detail);
  @override
  String toString() => detail;
}
