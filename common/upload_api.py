"""
API endpoints pour la gestion des uploads de fichiers et images.
"""

from typing import Optional
from ninja import Router, File, Form
from ninja.files import UploadedFile
from ninja.errors import HttpError
from pydantic import BaseModel
import uuid

from authentication.api import auth_bearer
from common.audit_utils import audit_log, get_authenticated_user
from .models import Upload
from .uploads import (
    upload_image,
    upload_document,
    upload_pdf,
    UploadValidationError,
    get_file_url,
)

router = Router()


def _auth_user(request):
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentification requise")
    return user


class UploadResponseSchema(BaseModel):
    id: int
    uuid: str
    nom_original: str
    nom_stocke: str
    type_fichier: str
    mime_type: str
    taille_octets: int
    hash_sha256: str
    chemin_stockage: str
    url: str
    date_upload: str


class UploadListSchema(BaseModel):
    id: int
    uuid: str
    nom_original: str
    type_fichier: str
    taille_octets: int
    date_upload: str
    uploade_par_username: Optional[str] = None


class DeleteUploadSchema(BaseModel):
    success: bool
    message: str


def _save_upload(request, file, storage_path, file_hash, type_fichier, contenu_type, contenu_id):
    user = _auth_user(request)
    upload_obj = Upload.objects.create(
        uuid=uuid.uuid4().hex[:16],
        type_fichier=type_fichier,
        nom_original=file.name,
        nom_stocke=storage_path.split('/')[-1],
        chemin_stockage=storage_path,
        mime_type=file.content_type,
        taille_octets=file.size,
        hash_sha256=file_hash,
        uploade_par=user,
        contenu_type=contenu_type,
        contenu_id=contenu_id,
    )
    audit_log(request, 'CREATE', upload_obj, new_value=f"Upload {type_fichier}: {file.name}")
    return UploadResponseSchema(
        id=upload_obj.id,
        uuid=upload_obj.uuid,
        nom_original=upload_obj.nom_original,
        nom_stocke=upload_obj.nom_stocke,
        type_fichier=upload_obj.type_fichier,
        mime_type=upload_obj.mime_type,
        taille_octets=upload_obj.taille_octets,
        hash_sha256=upload_obj.hash_sha256,
        chemin_stockage=upload_obj.chemin_stockage,
        url=get_file_url(storage_path),
        date_upload=upload_obj.date_upload.isoformat(),
    )


@router.post("/upload/image", response=UploadResponseSchema, auth=auth_bearer, tags=["uploads"])
def upload_image_endpoint(
    request,
    file: UploadedFile = File(...),
    contenu_type: str = Form("general"),
    contenu_id: Optional[int] = Form(None),
):
    try:
        storage_path, file_hash = upload_image(file)
        return _save_upload(request, file, storage_path, file_hash, 'IMAGE', contenu_type, contenu_id)
    except UploadValidationError as e:
        raise HttpError(400, str(e))
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"Erreur upload: {str(e)}")


@router.post("/upload/pdf", response=UploadResponseSchema, auth=auth_bearer, tags=["uploads"])
def upload_pdf_endpoint(
    request,
    file: UploadedFile = File(...),
    contenu_type: str = Form("general"),
    contenu_id: Optional[int] = Form(None),
):
    try:
        storage_path, file_hash = upload_pdf(file)
        return _save_upload(request, file, storage_path, file_hash, 'PDF', contenu_type, contenu_id)
    except UploadValidationError as e:
        raise HttpError(400, str(e))
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"Erreur upload: {str(e)}")


@router.post("/upload/document", response=UploadResponseSchema, auth=auth_bearer, tags=["uploads"])
def upload_document_endpoint(
    request,
    file: UploadedFile = File(...),
    contenu_type: str = Form("general"),
    contenu_id: Optional[int] = Form(None),
):
    try:
        storage_path, file_hash = upload_document(file)
        return _save_upload(request, file, storage_path, file_hash, 'DOCUMENT', contenu_type, contenu_id)
    except UploadValidationError as e:
        raise HttpError(400, str(e))
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"Erreur upload: {str(e)}")


@router.get("/uploads", response={200: dict}, auth=auth_bearer, tags=["uploads"])
def list_uploads(
    request,
    contenu_type: Optional[str] = None,
    contenu_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 50,
):
    from common.pagination import paginate_queryset, paginated_response
    user = _auth_user(request)
    queryset = Upload.objects.filter(
        uploade_par=user,
        est_actif=True,
        est_supprime_logiquement=False,
    ).order_by('-date_upload')
    if contenu_type:
        queryset = queryset.filter(contenu_type=contenu_type)
    if contenu_id:
        queryset = queryset.filter(contenu_id=contenu_id)
    rows, meta = paginate_queryset(queryset, page, page_size, max_page_size=200)
    items = [
        {
            'id': u.id,
            'uuid': str(u.uuid),
            'nom_original': u.nom_original,
            'type_fichier': u.type_fichier,
            'taille_octets': u.taille_octets,
            'date_upload': u.date_upload.isoformat(),
            'uploade_par_username': u.uploade_par.username if u.uploade_par else None,
        }
        for u in rows
    ]
    return 200, paginated_response(items, meta)


@router.get("/uploads/{upload_id}", response=UploadResponseSchema, auth=auth_bearer, tags=["uploads"])
def get_upload(request, upload_id: int):
    user = _auth_user(request)
    try:
        upload_obj = Upload.objects.get(id=upload_id)
    except Upload.DoesNotExist:
        raise HttpError(404, "Upload non trouvé")
    if upload_obj.uploade_par_id != user.id and user.role != 'ADMIN':
        raise HttpError(403, "Accès refusé")
    upload_obj.enregistrer_acces()
    audit_log(request, 'READ', upload_obj, new_value='Consultation upload')
    return UploadResponseSchema(
        id=upload_obj.id,
        uuid=upload_obj.uuid,
        nom_original=upload_obj.nom_original,
        nom_stocke=upload_obj.nom_stocke,
        type_fichier=upload_obj.type_fichier,
        mime_type=upload_obj.mime_type,
        taille_octets=upload_obj.taille_octets,
        hash_sha256=upload_obj.hash_sha256,
        chemin_stockage=upload_obj.chemin_stockage,
        url=get_file_url(upload_obj.chemin_stockage),
        date_upload=upload_obj.date_upload.isoformat(),
    )


@router.delete("/uploads/{upload_id}", response=DeleteUploadSchema, auth=auth_bearer, tags=["uploads"])
def delete_upload(request, upload_id: int):
    user = _auth_user(request)
    try:
        upload_obj = Upload.objects.get(id=upload_id)
    except Upload.DoesNotExist:
        raise HttpError(404, "Upload non trouvé")
    if upload_obj.uploade_par_id != user.id and user.role != 'ADMIN':
        raise HttpError(403, "Accès refusé")
    upload_obj.supprimer_logiquement()
    audit_log(request, 'DELETE', upload_obj, old_value=upload_obj.nom_original)
    return DeleteUploadSchema(success=True, message=f"Upload {upload_id} supprimé")
