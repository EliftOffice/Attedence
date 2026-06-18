import 'package:flutter/material.dart';

/// Single-field text prompt dialog. Returns the trimmed text, or null if the
/// user cancelled or left it empty.
Future<String?> promptText(
  BuildContext context, {
  required String title,
  String label = 'Name',
  String? initial,
  TextInputType? keyboard,
}) async {
  final c = TextEditingController(text: initial ?? '');
  final result = await showDialog<String>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(title),
      content: TextField(
        controller: c,
        autofocus: true,
        keyboardType: keyboard,
        textCapitalization: TextCapitalization.words,
        decoration: InputDecoration(labelText: label),
        onSubmitted: (v) => Navigator.pop(ctx, v.trim()),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
        FilledButton(
            onPressed: () => Navigator.pop(ctx, c.text.trim()),
            child: const Text('Save')),
      ],
    ),
  );
  if (result == null || result.isEmpty) return null;
  return result;
}

/// Yes/no confirmation. Returns true only if confirmed.
Future<bool> confirm(BuildContext context,
    {required String title, required String message, String confirmLabel = 'Delete'}) async {
  final ok = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
        FilledButton(
            onPressed: () => Navigator.pop(ctx, true), child: Text(confirmLabel)),
      ],
    ),
  );
  return ok == true;
}

/// Shows an error/info message in a snackbar (no-op if widget is gone).
void toast(BuildContext context, String message) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
}
