import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'session.dart';
import 'theme.dart';
import 'screens/login_screen.dart';
import 'screens/root_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));
  await Session.instance.load();
  runApp(const BsgApp());
}

class BsgApp extends StatelessWidget {
  const BsgApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Resurrection BSG',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: Session.instance.isLoggedIn ? const RootScreen() : const LoginScreen(),
    );
  }
}
