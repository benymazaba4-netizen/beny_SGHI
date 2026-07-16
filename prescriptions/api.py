from ninja import Router, Schema
from typing import List, Optional
from datetime import date

from .models import Medicament, Prescription, LignePrescription, AdministrationMedicament, PrescriptionError
from .services import (
    serialiser_prescription,
    valider_prescription,
    enregistrer_dose_omise,
    lister_alertes_doses,
)
from pharmacy.services import StockError
from common.permissions import (
    auth_bearer, role_required, enforce_patient_scope,
    ROLE_ADMIN, ROLE_MEDECIN, ROLE_INFIRMIER, ROLE_PHARMACIEN, ROLE_PATIENT,
)
from common.audit_utils import audit_log

router = Router(auth=auth_bearer)


class MedicamentSchema(Schema):
    code: str
    nom: str
    forme: str = 'COMPRIME'
    dosage: str = ''
    prix_unitaire: float = 0


class PrescriptionSchema(Schema):
    patient_id: int
    medecin_id: int
    consultation_id: int
    date_debut: date
    instructions: str = ''


class LignePrescriptionSchema(Schema):
    prescription_id: int
    medicament_id: int
    quantite_prescitee: int
    frequence: str
    duree_jours: int


class AdministrationSchema(Schema):
    ligne_prescription_id: int
    quantite_administree: int
    commentaire: str = ''


class DoseOmiseSchema(Schema):
    commentaire: str = ''


# --- Médicaments ---

@router.post("/medicaments", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_PHARMACIEN])
def create_medicament(request, payload: MedicamentSchema):
    try:
        medicament = Medicament.objects.create(**payload.dict())
        audit_log(request, 'CREATE', medicament, new_value=str(payload.dict()))
        return 201, {"id": medicament.id, "message": "Médicament créé"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/medicaments", response={200: dict, 401: dict})
@role_required([ROLE_MEDECIN, ROLE_PHARMACIEN, ROLE_INFIRMIER, ROLE_ADMIN])
def list_medicaments(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Medicament.objects.filter(est_actif=True).order_by('nom')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            'id': m.id,
            'code': m.code,
            'nom': m.nom,
            'forme': m.forme,
            'dosage': m.dosage,
            'prix_unitaire': float(m.prix_unitaire),
        }
        for m in rows
    ]
    return 200, paginated_response(items, meta)


# --- Prescriptions ---

@router.post("/prescriptions", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN])
def create_prescription(request, payload: PrescriptionSchema):
    try:
        prescription = Prescription.objects.create(**payload.dict(), statut='BROUILLON')
        audit_log(request, 'CREATE', prescription, new_value=str(payload.dict()))
        return 201, {
            "id": prescription.id,
            "message": "Prescription créée (brouillon)",
            "prescription": serialiser_prescription(prescription),
        }
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/prescriptions/{prescription_id}", response={200: dict, 404: dict, 401: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_PHARMACIEN])
def get_prescription(request, prescription_id: int):
    try:
        prescription = Prescription.objects.select_related('patient', 'medecin').get(id=prescription_id)
        return 200, serialiser_prescription(prescription)
    except Prescription.DoesNotExist:
        return 404, {"error": "Prescription non trouvée"}


@router.get("/prescriptions/patient/{patient_id}", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_PHARMACIEN, ROLE_PATIENT])
def get_prescriptions_patient(request, patient_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    denied = enforce_patient_scope(request, patient_id)
    if denied:
        return denied
    qs = Prescription.objects.filter(
        patient_id=patient_id,
    ).select_related('patient', 'medecin').order_by('-date_prescription')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([serialiser_prescription(p) for p in rows], meta)


@router.post("/prescriptions/lignes", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN])
def add_ligne_prescription(request, payload: LignePrescriptionSchema):
    try:
        prescription = Prescription.objects.get(id=payload.prescription_id)
        if prescription.est_verrouillee:
            return 400, {"error": "Prescription verrouillée — ajout de ligne interdit"}

        ligne = LignePrescription.objects.create(**payload.dict())
        audit_log(request, 'CREATE', ligne, new_value=str(payload.dict()))
        return 201, {"id": ligne.id, "message": "Ligne ajoutée"}
    except PrescriptionError as e:
        return 400, {"error": str(e)}
    except Prescription.DoesNotExist:
        return 404, {"error": "Prescription non trouvée"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.post("/prescriptions/{prescription_id}/valider", response={200: dict, 400: dict, 403: dict, 404: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN])
def valider_prescription_endpoint(request, prescription_id: int):
    """Valide, verrouille la prescription et décrémente les stocks."""
    try:
        user_id = request.auth_payload['id']
        prescription, mouvements = valider_prescription(prescription_id, user_id)
        audit_log(
            request, 'VALIDATE', prescription,
            new_value=f"Validée — {len(mouvements)} mouvement(s) stock",
        )
        return 200, {
            "message": "Prescription validée et verrouillée — stocks décrémentés",
            "prescription": serialiser_prescription(prescription),
            "mouvements_stock": len(mouvements),
        }
    except Prescription.DoesNotExist:
        return 404, {"error": "Prescription non trouvée"}
    except PrescriptionError as e:
        return 400, {"error": str(e)}
    except StockError as e:
        return 400, {"error": str(e)}
    except PermissionError as e:
        return 403, {"error": str(e)}


@router.post("/prescriptions/{prescription_id}/annuler", response={200: dict, 400: dict, 404: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN])
def annuler_prescription(request, prescription_id: int):
    try:
        prescription = Prescription.objects.get(id=prescription_id)
        if prescription.est_verrouillee:
            return 400, {"error": "Prescription verrouillée — annulation impossible"}
        prescription.statut = 'ANNULEE'
        prescription.save(update_fields=['statut'])
        audit_log(request, 'UPDATE', prescription, new_value="Annulée")
        return 200, {"message": "Prescription annulée"}
    except Prescription.DoesNotExist:
        return 404, {"error": "Prescription non trouvée"}


# --- Administrations ---

@router.post("/administrations", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_INFIRMIER, ROLE_ADMIN])
def administrer_medicament(request, payload: AdministrationSchema):
    try:
        ligne = LignePrescription.objects.select_related('prescription').get(
            id=payload.ligne_prescription_id,
        )
        if not ligne.prescription.est_verrouillee:
            return 400, {"error": "Prescription non validée — administration interdite"}
        if payload.quantite_administree > ligne.quantite_restante():
            return 400, {
                "error": f"Quantité excessive — reste {ligne.quantite_restante()} dose(s)",
            }

        admin = AdministrationMedicament.objects.create(
            ligne_prescription_id=payload.ligne_prescription_id,
            quantite_administree=payload.quantite_administree,
            commentaire=payload.commentaire,
            infirmier_id=request.auth_payload['id'],
        )
        audit_log(request, 'CREATE', admin, new_value=str(payload.dict()))
        return 201, {
            "id": admin.id,
            "message": "Administration enregistrée",
            "quantite_restante": ligne.quantite_restante(),
        }
    except PrescriptionError as e:
        return 400, {"error": str(e)}
    except LignePrescription.DoesNotExist:
        return 404, {"error": "Ligne de prescription non trouvée"}
    except Exception as e:
        return 400, {"error": str(e)}


# --- Alertes doses omises ---

@router.get("/prescriptions/alertes-doses", response={200: dict, 401: dict})
@role_required([ROLE_INFIRMIER, ROLE_MEDECIN, ROLE_ADMIN])
def get_alertes_doses(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    alertes = lister_alertes_doses()
    total = len(alertes)
    page = max(1, int(page or 1))
    page_size = min(max(1, int(page_size or 20)), 100)
    offset = (page - 1) * page_size
    items = alertes[offset:offset + page_size]
    total_pages = (total + page_size - 1) // page_size if total else 0
    meta = {
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1,
    }
    return 200, paginated_response(items, meta)


@router.post("/prescriptions/lignes/{ligne_id}/dose-omise", response={200: dict, 400: dict, 404: dict})
@role_required([ROLE_INFIRMIER, ROLE_ADMIN])
def signaler_dose_omise(request, ligne_id: int, payload: DoseOmiseSchema):
    try:
        user_id = request.auth_payload['id']
        ligne, alerte = enregistrer_dose_omise(ligne_id, user_id, payload.commentaire)
        audit_log(request, 'CREATE', alerte, new_value=f"Dose omise ligne #{ligne_id}")
        return 200, {
            "message": "Dose omise enregistrée",
            "doses_omises": ligne.doses_omises,
            "alerte_id": alerte.id,
        }
    except LignePrescription.DoesNotExist:
        return 404, {"error": "Ligne non trouvée"}
    except PrescriptionError as e:
        return 400, {"error": str(e)}
