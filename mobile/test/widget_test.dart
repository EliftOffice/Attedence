import 'package:flutter_test/flutter_test.dart';

import 'package:bsg_attendance/main.dart';

void main() {
  testWidgets('App boots to the login screen', (WidgetTester tester) async {
    await tester.pumpWidget(const BsgApp());
    await tester.pump();
    expect(find.text('BSG Attendance'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
  });
}
