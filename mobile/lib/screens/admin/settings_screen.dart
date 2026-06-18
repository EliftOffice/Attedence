import 'package:flutter/material.dart';

import '../../api.dart';
import '../../theme.dart';
import 'admin_ui.dart';

/// Runtime settings the admin can change without a redeploy: the Telegram bot
/// token + behaviour, the face-recognition quality knobs, and the max age
/// allowed for an uploaded group photo.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _loading = true;
  bool _saving = false;
  String? _error;

  // Telegram
  final _token = TextEditingController();
  bool _tokenSet = false;
  String? _tokenMask;
  String? _matchField;
  String? _replyMode;

  // Face recognition
  final _matchThreshold = TextEditingController();
  final _detScoreMin = TextEditingController();
  final _minPixels = TextEditingController();
  final _maxYaw = TextEditingController();
  final _blurMin = TextEditingController();
  bool _discardLowQuality = false;

  // Photos
  final _maxPhotoAge = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in [
      _token, _matchThreshold, _detScoreMin, _minPixels, _maxYaw, _blurMin, _maxPhotoAge
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  String _s(dynamic v) => v == null ? '' : '$v';

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final s = await Api.getSettings();
      setState(() {
        _tokenSet = s['telegram_token_set'] == true;
        _tokenMask = s['telegram_bot_token'];
        _matchField = s['telegram_match_field'];
        _replyMode = s['telegram_reply_mode'];
        _matchThreshold.text = _s(s['face_match_threshold']);
        _detScoreMin.text = _s(s['face_det_score_min']);
        _minPixels.text = _s(s['face_min_pixels']);
        _maxYaw.text = _s(s['face_max_yaw_deg']);
        _blurMin.text = _s(s['face_blur_var_min']);
        _discardLowQuality = s['discard_low_quality'] == true;
        _maxPhotoAge.text = _s(s['max_photo_age_days']);
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    final body = <String, dynamic>{
      if (_matchField != null) 'telegram_match_field': _matchField,
      if (_replyMode != null) 'telegram_reply_mode': _replyMode,
      'discard_low_quality': _discardLowQuality,
    };
    // Token only sent if the admin typed a new one (empty is ignored server-side).
    if (_token.text.trim().isNotEmpty) {
      body['telegram_bot_token'] = _token.text.trim();
    }
    void num(String key, TextEditingController c) {
      final v = double.tryParse(c.text.trim());
      if (v != null) body[key] = v;
    }
    void int_(String key, TextEditingController c) {
      final v = int.tryParse(c.text.trim());
      if (v != null) body[key] = v;
    }
    num('face_match_threshold', _matchThreshold);
    num('face_det_score_min', _detScoreMin);
    int_('face_min_pixels', _minPixels);
    num('face_max_yaw_deg', _maxYaw);
    num('face_blur_var_min', _blurMin);
    int_('max_photo_age_days', _maxPhotoAge);

    try {
      await Api.updateSettings(body);
      _token.clear();
      await _load();
      if (mounted) toast(context, 'Settings saved.');
    } catch (e) {
      if (mounted) toast(context, e.toString());
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: AppColors.danger)));
    }
    return Stack(
      children: [
        ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
          children: [
            _header('Telegram'),
            Text(
              _tokenSet
                  ? 'A bot token is set (${_tokenMask ?? 'hidden'}). Enter a new one only to change it.'
                  : 'No bot token set yet.',
              style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _token,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Bot token (leave blank to keep)'),
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              value: _matchField,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Match field'),
              items: const [
                DropdownMenuItem(value: 'user_id', child: Text('user_id')),
                DropdownMenuItem(value: 'chat_id', child: Text('chat_id')),
              ],
              onChanged: (v) => setState(() => _matchField = v),
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              value: _replyMode,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Reply mode'),
              items: const [
                DropdownMenuItem(value: 'minimal', child: Text('minimal')),
                DropdownMenuItem(value: 'silent', child: Text('silent')),
                DropdownMenuItem(value: 'private', child: Text('private')),
              ],
              onChanged: (v) => setState(() => _replyMode = v),
            ),

            const SizedBox(height: 24),
            _header('Face recognition'),
            const Text(
              'Higher threshold = stricter matching. Quality gates reject blurry, '
              'small, or angled faces.',
              style: TextStyle(color: AppColors.textMuted, fontSize: 12),
            ),
            const SizedBox(height: 10),
            _numField(_matchThreshold, 'Match threshold (0–1)'),
            _numField(_detScoreMin, 'Detection score min (0–1)'),
            _numField(_minPixels, 'Min face size (pixels)'),
            _numField(_maxYaw, 'Max head turn (degrees)'),
            _numField(_blurMin, 'Min sharpness (blur variance)'),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Discard low-quality faces'),
              subtitle: const Text('If off, low-quality faces still go to Visitors for review',
                  style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
              value: _discardLowQuality,
              onChanged: (v) => setState(() => _discardLowQuality = v),
            ),

            const SizedBox(height: 24),
            _header('Group photos'),
            const SizedBox(height: 10),
            _numField(_maxPhotoAge, 'Max photo age (days)'),
          ],
        ),
        Positioned(
          left: 16,
          right: 16,
          bottom: 16,
          child: FilledButton(
            onPressed: _saving ? null : _save,
            child: Text(_saving ? 'Saving…' : 'Save settings'),
          ),
        ),
      ],
    );
  }

  Widget _header(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Text(t, style: bold(16, AppColors.gold)),
      );

  Widget _numField(TextEditingController c, String label) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextField(
          controller: c,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(labelText: label),
        ),
      );
}
