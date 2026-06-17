import 'package:flutter/material.dart';

import 'session.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Session.instance.load();
  runApp(const BsgApp());
}

class BsgApp extends StatelessWidget {
  const BsgApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BSG Attendance',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF2C5282),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(centerTitle: false),
      ),
      home: Session.instance.isLoggedIn ? const HomeScreen() : const LoginScreen(),
    );
  }
}
