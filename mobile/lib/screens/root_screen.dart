import 'package:flutter/material.dart';

import '../session.dart';
import 'home_screen.dart';
import 'admin_home_screen.dart';

/// Decides which home to show after login based on the signed-in role:
/// admins get the management panel, leaders get the operational screens.
class RootScreen extends StatelessWidget {
  const RootScreen({super.key});

  @override
  Widget build(BuildContext context) =>
      Session.instance.isAdmin ? const AdminHomeScreen() : const HomeScreen();
}
