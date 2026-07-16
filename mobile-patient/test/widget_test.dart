import 'package:flutter_test/flutter_test.dart';
import 'package:sghi_patient/main.dart';

void main() {
  testWidgets('Portail patient affiche le titre SGHI', (WidgetTester tester) async {
    await tester.pumpWidget(const SghiPatientApp());
    await tester.pumpAndSettle();

    expect(find.text('SGHI Patient'), findsWidgets);
    expect(find.text('Se connecter'), findsOneWidget);
  });
}
