import 'package:flutter/material.dart';

/// Resurrection Ministries BSG palette — gold accents on a warm near-black,
/// drawn from the logo/banner. Typeface: Poppins.
class AppColors {
  static const gold = Color(0xFFC9A24B); // primary metallic gold
  static const goldBright = Color(0xFFE6BE5A); // highlight gold (banner text)
  static const goldDeep = Color(0xFF8C6E2A); // deep bronze
  static const bg = Color(0xFF15110C); // app background
  static const surface = Color(0xFF211B12); // cards / sheets
  static const surfaceAlt = Color(0xFF2A2217); // inputs
  static const textMain = Color(0xFFF3ECDD); // primary text (warm white)
  static const textMuted = Color(0xFFA99B7E); // secondary text
  static const border = Color(0xFF3A301F);
  static const danger = Color(0xFFE0726B);
  static const ok = Color(0xFF7BD49B);
  static const onGold = Color(0xFF1A1206); // text on gold buttons
}

/// Poppins-bold text style helper used across screens.
TextStyle bold(double size, [Color? color]) => TextStyle(
      fontFamily: 'Poppins',
      fontWeight: FontWeight.w700,
      fontSize: size,
      color: color ?? AppColors.textMain,
    );

ThemeData buildAppTheme() {
  const scheme = ColorScheme(
    brightness: Brightness.dark,
    primary: AppColors.gold,
    onPrimary: AppColors.onGold,
    secondary: AppColors.goldBright,
    onSecondary: AppColors.onGold,
    surface: AppColors.surface,
    onSurface: AppColors.textMain,
    error: AppColors.danger,
    onError: Colors.white,
  );

  final base = ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    fontFamily: 'Poppins',
    scaffoldBackgroundColor: AppColors.bg,
    dividerColor: AppColors.border,
  );

  return base.copyWith(
    appBarTheme: AppBarTheme(
      backgroundColor: AppColors.bg,
      foregroundColor: AppColors.gold,
      centerTitle: false,
      elevation: 0,
      titleTextStyle: bold(20, AppColors.gold),
    ),
    cardTheme: CardThemeData(
      color: AppColors.surface,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.border),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.gold,
        foregroundColor: AppColors.onGold,
        textStyle: const TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 15),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 18),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.gold,
        foregroundColor: AppColors.onGold,
        elevation: 0,
        textStyle: const TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.gold,
        side: const BorderSide(color: AppColors.goldDeep),
        textStyle: const TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(foregroundColor: AppColors.goldBright),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surfaceAlt,
      hintStyle: const TextStyle(color: AppColors.textMuted),
      labelStyle: const TextStyle(color: AppColors.textMuted),
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.gold, width: 1.6),
      ),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: AppColors.surface,
      indicatorColor: AppColors.gold.withValues(alpha: 0.18),
      labelTextStyle: WidgetStatePropertyAll(
        const TextStyle(fontFamily: 'Poppins', fontSize: 12, fontWeight: FontWeight.w500, color: AppColors.textMuted),
      ),
      iconTheme: WidgetStateProperty.resolveWith((states) => IconThemeData(
            color: states.contains(WidgetState.selected) ? AppColors.gold : AppColors.textMuted,
          )),
    ),
    snackBarTheme: const SnackBarThemeData(
      backgroundColor: AppColors.surfaceAlt,
      contentTextStyle: TextStyle(fontFamily: 'Poppins', color: AppColors.textMain),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(color: AppColors.gold),
    chipTheme: const ChipThemeData(backgroundColor: AppColors.surfaceAlt, labelStyle: TextStyle(color: AppColors.textMain)),
  );
}
