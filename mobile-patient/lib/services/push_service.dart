import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import '../firebase_options.dart';
import 'api_service.dart';

const _androidChannelId = 'sghi_patient_high';
const _androidChannelName = 'SGHI Patient';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  if (!DefaultFirebaseOptions.isConfigured) return;
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
}

/// Notifications push FCM — Android / iOS (désactivé sur web et si Firebase non configuré).
class PushNotificationService {
  PushNotificationService._();
  static final PushNotificationService instance = PushNotificationService._();

  FirebaseMessaging? _messaging;
  final FlutterLocalNotificationsPlugin _local = FlutterLocalNotificationsPlugin();
  final ApiService _api = ApiService();

  bool _ready = false;
  String? _lastToken;

  Future<void> initialize() async {
    if (_ready || kIsWeb) return;
    if (!DefaultFirebaseOptions.isConfigured) {
      debugPrint('[SGHI Push] Firebase non configuré — exécutez: dart pub global activate flutterfire_cli && flutterfire configure');
      return;
    }

    try {
      await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
      _messaging = FirebaseMessaging.instance;
      FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
      await _initLocalNotifications();
      await _requestPermission();
      FirebaseMessaging.onMessage.listen(_onForegroundMessage);
      FirebaseMessaging.onMessageOpenedApp.listen(_onMessageOpened);
      _messaging!.onTokenRefresh.listen((token) => _registerToken(token));
      _ready = true;
      debugPrint('[SGHI Push] Initialisé');
    } catch (e) {
      debugPrint('[SGHI Push] Échec initialisation: $e');
    }
  }

  Future<void> registerAfterLogin() async {
    if (!_ready) return;
    try {
      final token = await _messaging!.getToken();
      if (token != null) await _registerToken(token);
    } catch (e) {
      debugPrint('[SGHI Push] Token: $e');
    }
  }

  Future<void> unregister() async {
    if (!_ready) return;
    try {
      if (_lastToken != null && _lastToken!.length >= 8) {
        await _api.unregisterDevice(_lastToken!);
      }
      await _messaging!.deleteToken();
      _lastToken = null;
    } catch (e) {
      debugPrint('[SGHI Push] Désenregistrement: $e');
    }
  }

  Future<void> _registerToken(String token) async {
    _lastToken = token;
    final plateforme = defaultTargetPlatform == TargetPlatform.iOS ? 'IOS' : 'ANDROID';
    try {
      await _api.registerDevice(token, plateforme: plateforme);
      debugPrint('[SGHI Push] Appareil enregistré ($plateforme)');
    } catch (e) {
      debugPrint('[SGHI Push] API devices: $e');
    }
  }

  Future<void> _requestPermission() async {
    final settings = await _messaging!.requestPermission(alert: true, badge: true, sound: true);
    debugPrint('[SGHI Push] Permission: ${settings.authorizationStatus}');
  }

  Future<void> _initLocalNotifications() async {
    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings();
    await _local.initialize(
      settings: const InitializationSettings(android: android, iOS: ios),
      onDidReceiveNotificationResponse: (_) {},
    );

    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      await _local
          .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(
            const AndroidNotificationChannel(
              _androidChannelId,
              _androidChannelName,
              description: 'Alertes santé et rendez-vous SGHI',
              importance: Importance.high,
            ),
          );
    }
  }

  Future<void> _onForegroundMessage(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;

    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        _androidChannelId,
        _androidChannelName,
        importance: Importance.high,
        priority: Priority.high,
        icon: '@mipmap/ic_launcher',
      ),
      iOS: DarwinNotificationDetails(),
    );

    await _local.show(
      id: notification.hashCode,
      title: notification.title,
      body: notification.body,
      notificationDetails: details,
    );
  }

  void _onMessageOpened(RemoteMessage message) {
    debugPrint('[SGHI Push] Ouverture: ${message.notification?.title}');
  }
}
