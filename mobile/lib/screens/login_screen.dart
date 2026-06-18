import 'package:flutter/material.dart';

import '../api.dart';
import '../session.dart';
import '../theme.dart';
import 'root_screen.dart';

const _defaultServer = 'https://bsgapi.rmoffice.online';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _mobile = TextEditingController();
  final _password = TextEditingController();
  bool _loading = false;
  String? _error;

  Future<void> _submit() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      Session.instance.serverUrl = _defaultServer;
      await Session.instance.save();
      await Api.login(_mobile.text.trim(), _password.text);
      if (mounted) {
        Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (_) => const RootScreen()));
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: Image.asset('assets/brand/banner.png', fit: BoxFit.contain),
                ),
                const SizedBox(height: 28),
                Text('Attendance Portal',
                    textAlign: TextAlign.center,
                    style: bold(20, AppColors.gold)),
                const SizedBox(height: 4),
                const Text('Sign in to continue',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppColors.textMuted)),
                const SizedBox(height: 24),
                TextField(
                  controller: _mobile,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Mobile number',
                    prefixIcon: Icon(Icons.phone_outlined),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _password,
                  obscureText: true,
                  onSubmitted: (_) => _submit(),
                  decoration: const InputDecoration(
                    labelText: 'Password',
                    prefixIcon: Icon(Icons.lock_outline),
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: AppColors.danger)),
                ],
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: _loading ? null : _submit,
                  child: Text(_loading ? 'Signing in…' : 'Sign in'),
                ),
                const SizedBox(height: 16),
                const Text('Resurrection Ministries BSG',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
