import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});
  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ApiListResult {
  ApiListResult({required this.items, this.pagination});

  final List<dynamic> items;
  final Map<String, dynamic>? pagination;

  bool get hasNext => pagination?['has_next'] == true;
  int get page => (pagination?['page'] as int?) ?? 1;
}

class ApiService {
  ApiService._();
  static final ApiService instance = ApiService._();
  factory ApiService() => instance;

  static String get baseUrl => AppConfig.apiBaseUrl;
  static const Duration _timeout = Duration(seconds: 20);
  static const _otpSessionKey = 'pending_otp_session';
  static const _otpHintKey = 'pending_otp_email_hint';
  static const _otpUsernameKey = 'pending_otp_username';

  final http.Client _client = http.Client();
  String? _mfaSession;
  String? _otpSession;
  String? _otpEmailHint;
  String? _otpUsername;

  Future<Map<String, String>> _getHeaders({bool json = true}) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    return {
      if (json) 'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token') != null;
  }

  Future<http.Response> _safeRequest(Future<http.Response> Function() call) async {
    try {
      return await call().timeout(_timeout);
    } on TimeoutException {
      throw ApiException(
        'Délai dépassé — le serveur ne répond pas.\n'
        'Lancez : python manage.py runserver 127.0.0.1:8000',
      );
    } catch (e) {
      if (e is ApiException) rethrow;
      final msg = e.toString();
      if (msg.contains('Failed host lookup') || msg.contains('Connection refused') || msg.contains('Failed to fetch')) {
        throw ApiException(
          'Serveur API injoignable ($baseUrl).\n'
          'Démarrez Django : python manage.py runserver 127.0.0.1:8000',
        );
      }
      throw ApiException('Connexion impossible au serveur API ($baseUrl).\nVérifiez que Django est démarré.');
    }
  }

  Future<bool> _refreshTokenIfNeeded() async {
    final prefs = await SharedPreferences.getInstance();
    final refresh = prefs.getString('refresh_token');
    if (refresh == null) return false;

    final response = await _safeRequest(() => _client.post(
          Uri.parse('$baseUrl/auth/refresh'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh_token': refresh}),
        ));

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    await prefs.setString('token', data['token'] as String);
    if (data['refresh_token'] != null) {
      await prefs.setString('refresh_token', data['refresh_token'] as String);
    }
    if (data['user'] != null) {
      await prefs.setString('user', jsonEncode(data['user']));
    }
    return true;
  }

  Future<http.Response> _request(Future<http.Response> Function() call) async {
    var response = await _safeRequest(call);
    if (response.statusCode == 401) {
      final refreshed = await _refreshTokenIfNeeded();
      if (refreshed) response = await _safeRequest(call);
    }
    return response;
  }

  String _extractError(http.Response response) {
    try {
      final data = jsonDecode(response.body);
      if (data is Map && data['error'] != null) return data['error'].toString();
      if (data is Map && data['detail'] != null) {
        final detail = data['detail'];
        if (detail is String) return detail;
        if (detail is List && detail.isNotEmpty) {
          return detail.map((e) => e is Map ? (e['msg'] ?? e).toString() : e.toString()).join(' — ');
        }
      }
    } catch (_) {}
    if (response.statusCode == 422) {
      return 'Données OTP invalides — reconnectez-vous et réessayez.';
    }
    return 'Erreur API ${response.statusCode}';
  }

  Future<void> _persistOtpSession(String? session, {String? hint, String? username}) async {
    _otpSession = session;
    if (hint != null) _otpEmailHint = hint;
    if (username != null) _otpUsername = username;
    final prefs = await SharedPreferences.getInstance();
    if (session != null && session.isNotEmpty) {
      await prefs.setString(_otpSessionKey, session);
      if (hint != null) await prefs.setString(_otpHintKey, hint);
      if (username != null) await prefs.setString(_otpUsernameKey, username);
    } else {
      await prefs.remove(_otpSessionKey);
      await prefs.remove(_otpHintKey);
      await prefs.remove(_otpUsernameKey);
      _otpUsername = null;
    }
  }

  Future<String?> _resolveOtpUsername() async {
    if (_otpUsername != null && _otpUsername!.isNotEmpty) return _otpUsername;
    final prefs = await SharedPreferences.getInstance();
    _otpUsername = prefs.getString(_otpUsernameKey);
    return _otpUsername;
  }

  Future<String?> _resolveOtpSession() async {
    if (_otpSession != null && _otpSession!.isNotEmpty) return _otpSession;
    final prefs = await SharedPreferences.getInstance();
    _otpSession = prefs.getString(_otpSessionKey);
    _otpEmailHint = prefs.getString(_otpHintKey);
    _otpUsername = prefs.getString(_otpUsernameKey);
    return _otpSession;
  }

  Future<Map<String, dynamic>> login(
    String username,
    String password, {
    String? mfaToken,
  }) async {
    if (kDebugMode) {
      debugPrint('[SGHI] POST $baseUrl/auth/login');
    }

    if (mfaToken != null && _mfaSession != null) {
      final response = await _safeRequest(() => _client.post(
            Uri.parse('$baseUrl/auth/login/mfa'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'mfa_session': _mfaSession, 'totp_token': mfaToken}),
          ));
      return _handleLoginResponse(response);
    }

    final response = await _safeRequest(() => _client.post(
          Uri.parse('$baseUrl/auth/login'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'username': username.trim(), 'password': password}),
        ));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      if (data['mfa_required'] == true) {
        _mfaSession = data['mfa_session'] as String?;
        _otpSession = null;
        return {'success': false, 'mfa_required': true};
      }
      if (data['otp_required'] == true) {
        final session = data['otp_session'] as String?;
        final hint = data['otp_email_hint'] as String?;
        await _persistOtpSession(session, hint: hint, username: username.trim());
        _mfaSession = null;
        return {
          'success': false,
          'otp_required': true,
          'otp_email_hint': hint ?? _otpEmailHint,
        };
      }
    }

    if (response.statusCode == 400 || response.statusCode == 401) {
      return {'success': false, 'error': _extractError(response)};
    }

    return _handleLoginResponse(response);
  }

  /// Valide le code OTP reçu par e-mail (2e étape de connexion).
  Future<Map<String, dynamic>> loginOtp(String otpCode) async {
    final username = await _resolveOtpUsername();
    if (username == null || username.isEmpty) {
      return {'success': false, 'error': 'Session OTP expirée — reconnectez-vous.'};
    }
    final code = otpCode.trim().replaceAll(' ', '');
    if (code.length != 6) {
      return {'success': false, 'error': 'Le code OTP doit contenir 6 chiffres.'};
    }
    final response = await _safeRequest(() => _client.post(
          Uri.parse('$baseUrl/auth/verify-otp'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'username': username, 'otp_code': code}),
        ));
    if (response.statusCode == 401 || response.statusCode == 400 || response.statusCode == 422) {
      return {'success': false, 'error': _extractError(response)};
    }
    return _handleLoginResponse(response);
  }

  /// Renvoie un nouveau code OTP par e-mail.
  Future<Map<String, dynamic>> resendOtp() async {
    final session = await _resolveOtpSession();
    if (session == null || session.isEmpty) {
      return {'success': false, 'error': 'Session OTP expirée — reconnectez-vous.'};
    }
    final response = await _safeRequest(() => _client.post(
          Uri.parse('$baseUrl/auth/login/otp/resend'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'otp_session': session}),
        ));
    if (response.statusCode == 400) {
      return {'success': false, 'error': _extractError(response)};
    }
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final newSession = data['otp_session'] as String?;
      final hint = data['otp_email_hint'] as String?;
      await _persistOtpSession(newSession ?? session, hint: hint);
      return {'success': true, 'otp_email_hint': hint ?? _otpEmailHint};
    }
    return {'success': false, 'error': _extractError(response)};
  }

  Future<Map<String, dynamic>> _handleLoginResponse(http.Response response) async {
    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      if (data['token'] == null) {
        return {'success': false, 'error': 'Réponse serveur invalide (token manquant)'};
      }
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('token', data['token'] as String);
      if (data['refresh_token'] != null) {
        await prefs.setString('refresh_token', data['refresh_token'] as String);
      }
      if (data['user'] != null) {
        await prefs.setString('user', jsonEncode(data['user']));
      }
      _mfaSession = null;
      await _persistOtpSession(null);
      return {'success': true, 'data': data};
    }
    return {'success': false, 'error': _extractError(response)};
  }

  Future<Map<String, dynamic>> register(Map<String, dynamic> payload) async {
    final response = await _safeRequest(() => _client.post(
          Uri.parse('$baseUrl/auth/register'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(payload),
        ));
    if (response.statusCode == 201) {
      return _handleLoginResponse(response);
    }
    return {'success': false, 'error': _extractError(response)};
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    final refresh = prefs.getString('refresh_token');
    if (refresh != null) {
      try {
        await _safeRequest(() => _client.post(
              Uri.parse('$baseUrl/auth/logout'),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({'refresh_token': refresh}),
            ));
      } catch (_) {}
    }
    await prefs.remove('token');
    await prefs.remove('refresh_token');
    await prefs.remove('user');
    _mfaSession = null;
    await _persistOtpSession(null);
  }

  Future<dynamic> get(String endpoint, {Map<String, dynamic>? params}) async {
    final uri = _buildUri(endpoint, params);
    final response = await _request(() async {
      final headers = await _getHeaders();
      return _client.get(uri, headers: headers);
    });
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic> && decoded.containsKey('items')) {
        return decoded['items'];
      }
      return decoded;
    }
    throw ApiException(_extractError(response), statusCode: response.statusCode);
  }

  Future<ApiListResult> getPaginated(String endpoint, {int page = 1, int pageSize = 100}) async {
    final uri = _buildUri(endpoint, {'page': page, 'page_size': pageSize});
    final response = await _request(() async {
      final headers = await _getHeaders();
      return _client.get(uri, headers: headers);
    });
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic> && decoded.containsKey('items')) {
        return ApiListResult(
          items: List<dynamic>.from(decoded['items'] as List),
          pagination: decoded['pagination'] != null
              ? Map<String, dynamic>.from(decoded['pagination'] as Map)
              : null,
        );
      }
      if (decoded is List) {
        return ApiListResult(items: decoded);
      }
    }
    throw ApiException(_extractError(response), statusCode: response.statusCode);
  }

  Future<List<dynamic>> getAllPages(String endpoint, {int pageSize = 100}) async {
    final all = <dynamic>[];
    var page = 1;
    while (true) {
      final result = await getPaginated(endpoint, page: page, pageSize: pageSize);
      all.addAll(result.items);
      if (!result.hasNext) break;
      page += 1;
      if (page > 50) break;
    }
    return all;
  }

  Uri _buildUri(String endpoint, [Map<String, dynamic>? params]) {
    final base = endpoint.startsWith('http') ? endpoint : '$baseUrl$endpoint';
    final uri = Uri.parse(base);
    if (params == null || params.isEmpty) return uri;
    final query = Map<String, String>.from(uri.queryParameters);
    params.forEach((key, value) {
      if (value != null) query[key] = '$value';
    });
    return uri.replace(queryParameters: query);
  }

  Future<dynamic> post(String endpoint, Map<String, dynamic> data) async {
    final response = await _request(() async {
      final headers = await _getHeaders();
      return _client.post(
        Uri.parse('$baseUrl$endpoint'),
        headers: headers,
        body: jsonEncode(data),
      );
    });
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return {};
      return jsonDecode(response.body);
    }
    throw ApiException(_extractError(response), statusCode: response.statusCode);
  }

  Future<Uint8List> downloadBytes(String endpoint) async {
    final response = await _request(() async {
      final headers = await _getHeaders(json: false);
      return _client.get(Uri.parse('$baseUrl$endpoint'), headers: headers);
    });
    if (response.statusCode == 200) {
      return response.bodyBytes;
    }
    throw ApiException(_extractError(response), statusCode: response.statusCode);
  }

  Future<Map<String, dynamic>?> getCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString('user');
    if (userJson == null) return null;
    return Map<String, dynamic>.from(jsonDecode(userJson) as Map);
  }

  Future<void> registerDevice(String token, {String plateforme = 'ANDROID'}) async {
    await post('/notifications/devices', {'token': token, 'plateforme': plateforme});
  }

  Future<void> unregisterDevice(String token) async {
    final prefix = token.length > 20 ? token.substring(0, 20) : token;
    final response = await _request(() async {
      final headers = await _getHeaders();
      return _client.delete(Uri.parse('$baseUrl/notifications/devices/$prefix'), headers: headers);
    });
    if (response.statusCode != 200 && response.statusCode != 404) {
      throw ApiException(_extractError(response), statusCode: response.statusCode);
    }
  }
}
