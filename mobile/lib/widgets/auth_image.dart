import 'package:flutter/material.dart';
import '../api.dart';
import '../session.dart';

/// Displays a protected backend image (member photo / visitor crop). Plain
/// Image.network can't send the JWT, so we pass the auth header explicitly.
class AuthImage extends StatelessWidget {
  final String? url; // relative (/api/...) or absolute; null => placeholder
  final double size;
  final double radius;
  const AuthImage({super.key, required this.url, this.size = 96, this.radius = 12});

  @override
  Widget build(BuildContext context) {
    final placeholder = Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(radius),
      ),
      child: Icon(Icons.person, size: size * 0.5, color: Colors.grey.shade400),
    );
    if (url == null) return placeholder;
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: Image.network(
        Api.abs(url!),
        headers: Session.instance.authHeaders,
        width: size,
        height: size,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => placeholder,
        loadingBuilder: (ctx, child, progress) =>
            progress == null ? child : SizedBox(width: size, height: size, child: const Center(child: CircularProgressIndicator(strokeWidth: 2))),
      ),
    );
  }
}
