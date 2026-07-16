import json
import time

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


SENSITIVE_PATH_LIMITS = {
    '/api/v1/auth/login': (10, 60),
    '/api/v1/auth/verify-otp': (20, 60),
    '/api/v1/auth/login/otp': (20, 60),
    '/api/v1/auth/login/otp/resend': (5, 60),
    '/api/v1/auth/login/mfa': (15, 60),
    '/api/v1/auth/register': (5, 300),
    '/api/v1/auth/refresh': (30, 60),
    '/api/v1/files/upload/pdf': (20, 60),
    '/api/v1/files/upload/image': (20, 60),
    '/api/v1/files/upload/document': (15, 60),
    '/api/v1/prescriptions/prescriptions': (40, 60),
}

LOGIN_PATHS = frozenset({
    '/api/v1/auth/login',
})


def extract_login_username(request, path: str) -> str | None:
    if path not in LOGIN_PATHS or request.method != 'POST':
        return None
    try:
        body = request.body.decode('utf-8') if request.body else ''
        if not body:
            return None
        data = json.loads(body)
        username = (data.get('username') or '').strip().lower()
        return username or None
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
        return None


def build_sensitive_rate_key(ip: str, path: str, username: str | None) -> str:
    if path in LOGIN_PATHS and username:
        return f'rate_sensitive_{ip}_{path}_{username}'
    return f'rate_sensitive_{ip}_{path}'


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting global par IP + renforcement IP+username sur le login."""

    def __init__(self, get_response):
        super().__init__(get_response)
        self.rate_limit = 100
        self.time_window = 60

    def process_request(self, request):
        ip = self.get_client_ip(request)
        path = request.path.rstrip('/') or '/'
        current_time = time.time()

        sensitive = SENSITIVE_PATH_LIMITS.get(path)
        if sensitive:
            max_req, window = sensitive
            username = extract_login_username(request, path)
            key = build_sensitive_rate_key(ip, path, username)
            hits = cache.get(key, [])
            hits = [t for t in hits if current_time - t < window]
            if len(hits) >= max_req:
                return JsonResponse(
                    {"error": "Trop de tentatives sur cette route. Réessayez plus tard."},
                    status=429,
                )
            hits.append(current_time)
            cache.set(key, hits, window)

        cache_key = f'rate_limit_{ip}'
        requests = cache.get(cache_key, [])
        requests = [t for t in requests if current_time - t < self.time_window]

        if len(requests) >= self.rate_limit:
            return JsonResponse(
                {"error": "Trop de requêtes. Veuillez réessayer plus tard."},
                status=429,
            )

        requests.append(current_time)
        cache.set(cache_key, requests, self.time_window)
        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
