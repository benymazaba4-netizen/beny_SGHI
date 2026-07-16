"""Contexte requête thread-local pour audit automatique."""
import threading

_local = threading.local()


def set_current_request(request):
    _local.request = request


def get_current_request():
    return getattr(_local, 'request', None)


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        try:
            return self.get_response(request)
        finally:
            set_current_request(None)
