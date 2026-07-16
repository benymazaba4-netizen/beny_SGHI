"""
Chiffrement AES-256 (Fernet) pour données sensibles au repos.
"""
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet():
    key_material = getattr(settings, 'FIELD_ENCRYPTION_KEY', settings.SECRET_KEY)
    digest = hashlib.sha256(key_material.encode('utf-8')).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_value(plain_text: str) -> str:
    if not plain_text:
        return ''
    return _get_fernet().encrypt(plain_text.encode('utf-8')).decode('utf-8')


def decrypt_value(cipher_text: str) -> str:
    if not cipher_text:
        return ''
    try:
        return _get_fernet().decrypt(cipher_text.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return cipher_text


def is_encrypted_field(value: str) -> bool:
    """Détecte si une valeur est déjà chiffrée Fernet."""
    return bool(value and value.startswith('gAAAA'))
