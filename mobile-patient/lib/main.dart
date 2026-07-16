import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'config/app_config.dart';
import 'theme/app_design.dart';
import 'services/push_service.dart';
import 'screens/welcome_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/home_screen.dart';
import 'screens/staff_home_screen.dart';
import 'utils/auth_navigation.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('fr_FR', null);
  await PushNotificationService.instance.initialize();
  runApp(const SghiPatientApp());
}

class SghiPatientApp extends StatelessWidget {
  const SghiPatientApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '${AppConfig.appName} ${AppConfig.appSubtitle}',
      debugShowCheckedModeBanner: false,
      theme: AppDesign.theme,
      locale: const Locale('fr', 'FR'),
      supportedLocales: const [Locale('fr', 'FR')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      initialRoute: '/',
      routes: {
        '/': (context) => const WelcomeScreen(),
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/home': (context) => const HomeScreen(),
        '/staff': (context) {
          final role = ModalRoute.of(context)?.settings.arguments as String? ?? AppRoles.medecin;
          return StaffHomeScreen(role: role);
        },
      },
    );
  }
}
