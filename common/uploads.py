"""
Gestion sécurisée des uploads de fichiers et images.
- Validation MIME types
- Limite de taille
- Stockage avec UUID
- Antivirus scan (optionnel)
- Encryption (optionnel)
"""

import os
import hashlib
import uuid
from typing import Tuple, Optional
from django.conf import settings
from django.core.files.storage import default_storage
from pathlib import Path

# Fichier MIME autorisés
ALLOWED_IMAGE_MIMES = {
    'image/jpeg': ['jpg', 'jpeg'],
    'image/png': ['png'],
    'image/webp': ['webp'],
    'image/gif': ['gif'],
}

ALLOWED_PDF_MIMES = {
    'application/pdf': ['pdf'],
}

ALLOWED_DOCUMENT_MIMES = {
    **ALLOWED_PDF_MIMES,
    'application/msword': ['doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
    'application/vnd.ms-excel': ['xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
}

# Limites de taille (en octets)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB


class UploadValidationError(Exception):
    """Erreur de validation d'upload"""
    pass


def validate_mime_type(file_obj, allowed_mimes: dict) -> bool:
    """
    Valide le MIME type du fichier.
    
    Args:
        file_obj: Objet fichier Django
        allowed_mimes: Dict {mime_type: [extensions]}
    
    Returns:
        bool: True si valide
    
    Raises:
        UploadValidationError: Si MIME invalide
    """
    content_type = file_obj.content_type
    
    if content_type not in allowed_mimes:
        raise UploadValidationError(
            f"Type MIME non autorisé: {content_type}. "
            f"Types acceptés: {', '.join(allowed_mimes.keys())}"
        )
    
    return True


def validate_file_size(file_obj, max_size: int) -> bool:
    """
    Valide la taille du fichier.
    
    Args:
        file_obj: Objet fichier Django
        max_size: Taille maximale en octets
    
    Returns:
        bool: True si valide
    
    Raises:
        UploadValidationError: Si taille dépasse limite
    """
    if file_obj.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise UploadValidationError(
            f"Fichier trop volumineux. Maximum: {max_size_mb:.1f} MB, "
            f"Reçu: {file_obj.size / (1024 * 1024):.1f} MB"
        )
    
    return True


def calculate_file_hash(file_obj) -> str:
    """
    Calcule le hash SHA256 du fichier.
    Utile pour détecter les doublons et verifier l'intégrité.
    
    Args:
        file_obj: Objet fichier Django
    
    Returns:
        str: Hash SHA256 hexadécimal
    """
    file_obj.seek(0)
    sha256_hash = hashlib.sha256()
    
    for chunk in file_obj.chunks():
        sha256_hash.update(chunk)
    
    file_obj.seek(0)
    return sha256_hash.hexdigest()


def scan_antivirus(file_obj) -> bool:
    """
    Scan antivirus optionnel via ClamAV (clamd socket).
    Ignoré si CLAMAV_ENABLED=False ou si clamd indisponible.
    """
    from django.conf import settings
    if not getattr(settings, 'CLAMAV_ENABLED', False):
        return True

    try:
        import socket
        file_obj.seek(0)
        data = file_obj.read()
        file_obj.seek(0)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(getattr(settings, 'CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl'))
        sock.send(b'zINSTREAM\0')
        chunk_size = 2048
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            sock.send(len(chunk).to_bytes(4, 'big') + chunk)
        sock.send(b'\0\0\0\0')
        result = sock.recv(4096).decode('utf-8', errors='ignore')
        sock.close()
        if 'FOUND' in result:
            raise UploadValidationError(f"Menace détectée par antivirus: {result.strip()}")
        return True
    except UploadValidationError:
        raise
    except Exception:
        return True


def generate_safe_filename(original_filename: str, file_hash: str) -> str:
    """
    Génère un nom de fichier sécurisé avec UUID.
    
    Args:
        original_filename: Nom original du fichier
        file_hash: Hash SHA256 du fichier
    
    Returns:
        str: Nom de fichier sécurisé (uuid_hash.ext)
    """
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower()
    
    # Générer nom unique
    unique_name = f"{uuid.uuid4().hex[:8]}_{file_hash[:8]}{ext}"
    
    return unique_name


def upload_image(
    file_obj,
    folder: str = 'images',
    validate_mime: bool = True,
    validate_size: bool = True,
) -> Tuple[str, str]:
    """
    Upload une image avec validation.
    
    Args:
        file_obj: Objet fichier Django (request.FILES['file'])
        folder: Dossier de destination (par défaut 'images')
        validate_mime: Valider le MIME type
        validate_size: Valider la taille
    
    Returns:
        Tuple[str, str]: (chemin_stockage, hash_fichier)
    
    Raises:
        UploadValidationError: Si validation échoue
    """
    if validate_mime:
        validate_mime_type(file_obj, ALLOWED_IMAGE_MIMES)
    
    if validate_size:
        validate_file_size(file_obj, MAX_IMAGE_SIZE)

    scan_antivirus(file_obj)
    
    # Calculer hash
    file_hash = calculate_file_hash(file_obj)
    
    # Générer nom sécurisé
    safe_filename = generate_safe_filename(file_obj.name, file_hash)
    
    # Chemin de stockage
    storage_path = f"uploads/{folder}/{safe_filename}"
    
    # Sauvegarder
    path = default_storage.save(storage_path, file_obj)
    
    return path, file_hash


def upload_document(
    file_obj,
    folder: str = 'documents',
    validate_mime: bool = True,
    validate_size: bool = True,
) -> Tuple[str, str]:
    """
    Upload un document (PDF, Word, Excel) avec validation.
    
    Args:
        file_obj: Objet fichier Django
        folder: Dossier de destination
        validate_mime: Valider le MIME type
        validate_size: Valider la taille
    
    Returns:
        Tuple[str, str]: (chemin_stockage, hash_fichier)
    
    Raises:
        UploadValidationError: Si validation échoue
    """
    if validate_mime:
        validate_mime_type(file_obj, ALLOWED_DOCUMENT_MIMES)
    
    if validate_size:
        validate_file_size(file_obj, MAX_DOCUMENT_SIZE)

    scan_antivirus(file_obj)
    
    file_hash = calculate_file_hash(file_obj)
    safe_filename = generate_safe_filename(file_obj.name, file_hash)
    storage_path = f"uploads/{folder}/{safe_filename}"
    
    path = default_storage.save(storage_path, file_obj)
    
    return path, file_hash


def upload_pdf(
    file_obj,
    folder: str = 'pdfs',
    validate_mime: bool = True,
    validate_size: bool = True,
) -> Tuple[str, str]:
    """
    Upload un PDF avec validation.
    
    Args:
        file_obj: Objet fichier Django
        folder: Dossier de destination
        validate_mime: Valider le MIME type
        validate_size: Valider la taille
    
    Returns:
        Tuple[str, str]: (chemin_stockage, hash_fichier)
    
    Raises:
        UploadValidationError: Si validation échoue
    """
    if validate_mime:
        validate_mime_type(file_obj, ALLOWED_PDF_MIMES)
    
    if validate_size:
        validate_file_size(file_obj, MAX_PDF_SIZE)

    scan_antivirus(file_obj)
    
    file_hash = calculate_file_hash(file_obj)
    safe_filename = generate_safe_filename(file_obj.name, file_hash)
    storage_path = f"uploads/{folder}/{safe_filename}"
    
    path = default_storage.save(storage_path, file_obj)
    
    return path, file_hash


def delete_file(file_path: str) -> bool:
    """
    Supprime un fichier stocké.
    
    Args:
        file_path: Chemin du fichier
    
    Returns:
        bool: True si supprimé, False si non trouvé
    """
    if default_storage.exists(file_path):
        default_storage.delete(file_path)
        return True
    return False


def get_file_url(file_path: str) -> str:
    """
    Récupère l'URL publique d'un fichier.
    
    Args:
        file_path: Chemin du fichier
    
    Returns:
        str: URL complète du fichier
    """
    return default_storage.url(file_path)
