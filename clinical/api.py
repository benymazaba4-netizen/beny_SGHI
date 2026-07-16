from ninja import Router, Schema
from typing import List, Optional
from datetime import date
from .models import Patient, Admission, Consultation, ConstanteVitale, PlanSoin
from .services import (
    creer_admission,
    sortir_patient,
    transferer_patient,
    verifier_admission_pour_soins,
    serialiser_admission,
    HospitalisationError,
)
from common.permissions import (
    auth_bearer, role_required, enforce_patient_scope,
    ROLE_ADMIN, ROLE_MEDECIN, ROLE_INFIRMIER, ROLE_SECRETAIRE, ROLE_PATIENT,
)
from governance.services import journaliser_acces
from common.audit_utils import audit_log, get_authenticated_user
from .qr_access import generate_patient_qr, verify_patient_qr_token

router = Router(auth=auth_bearer)


class PatientSchema(Schema):
    nom: str
    prenom: str
    date_naissance: date
    telephone: str
    adresse: str
    email: Optional[str] = ''
    mutuelle: Optional[str] = ''
    civilite: str = 'M'
    consentement_donnees: bool = True


class PatientResponse(Schema):
    id: int
    nom: str
    prenom: str
    numero_dossier: str
    telephone: str
    email: str


class AdmissionSchema(Schema):
    patient_id: int
    service_id: int
    lit_id: int
    medecin_referent_id: int
    motif_hospitalisation: str
    date_previsionnelle_sortie: date
    type_admission: str = 'PROGRAMMEE'
    lit_version: Optional[int] = None


class SortieSchema(Schema):
    statut: str = 'SORTI'
    notes: Optional[str] = ''
    version: int


class TransfertSchema(Schema):
    nouveau_service_id: int
    nouveau_lit_id: int
    motif: Optional[str] = ''
    version: int


class ConsultationSchema(Schema):
    patient_id: int
    medecin_id: int
    service_id: int
    motif: str
    diagnostic: str = ''
    diagnostic_cim10: str = ''
    admission_id: Optional[int] = None


class ConstanteSchema(Schema):
    patient_id: int
    admission_id: int
    tension_arterielle: str = ''
    frequence_cardiaque: Optional[int] = None
    temperature: Optional[float] = None
    saturation_o2: Optional[int] = None


class QRAccessVerifySchema(Schema):
    token: str


# --- Patients ---

@router.post("/patients", response={201: PatientResponse, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_SECRETAIRE])
def create_patient(request, payload: PatientSchema):
    try:
        patient = Patient.objects.create(**payload.dict())
        audit_log(request, 'CREATE', patient, new_value=str(payload.dict()))
        return 201, {
            "id": patient.id,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "numero_dossier": patient.numero_dossier,
            "telephone": patient.telephone,
            "email": patient.email,
        }
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/patients", response={200: dict, 401: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_SECRETAIRE])
def list_patients(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Patient.objects.filter(est_actif=True).order_by('nom', 'prenom')
    patients, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {
            'id': p.id,
            'nom': p.nom,
            'prenom': p.prenom,
            'numero_dossier': p.numero_dossier,
            'telephone': p.telephone,
            'email': p.email,
        }
        for p in patients
    ]
    return 200, paginated_response(items, meta)


@router.get("/patients/{patient_id}", response={200: dict, 404: dict, 401: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_SECRETAIRE])
def get_patient(request, patient_id: int):
    try:
        patient = Patient.objects.get(id=patient_id)
        admission = patient.admission_active()
        return 200, {
            "id": patient.id,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "date_naissance": patient.date_naissance,
            "telephone": patient.telephone,
            "adresse": patient.adresse,
            "email": patient.email,
            "numero_dossier": patient.numero_dossier,
            "mutuelle": patient.mutuelle,
            "admission_active_id": admission.id if admission else None,
        }
    except Patient.DoesNotExist:
        return 404, {"error": "Patient non trouvé"}


@router.put("/patients/{patient_id}", response={200: PatientResponse, 400: dict, 404: dict, 403: dict})
@role_required([ROLE_SECRETAIRE])
def update_patient(request, patient_id: int, payload: PatientSchema):
    try:
        patient = Patient.objects.get(id=patient_id, est_actif=True)
        for field, value in payload.dict().items():
            setattr(patient, field, value)
        patient.save()
        audit_log(request, 'UPDATE', patient, new_value=str(payload.dict()))
        return 200, {
            "id": patient.id,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "numero_dossier": patient.numero_dossier,
            "telephone": patient.telephone,
            "email": patient.email,
        }
    except Patient.DoesNotExist:
        return 404, {"error": "Patient non trouvé"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.post("/patients/{patient_id}/qr-access", response={200: dict, 401: dict, 403: dict, 404: dict})
@role_required([ROLE_MEDECIN, ROLE_INFIRMIER, ROLE_SECRETAIRE, ROLE_PATIENT])
def generate_patient_qr_access(request, patient_id: int):
    try:
        patient = Patient.objects.get(id=patient_id, est_actif=True)
    except Patient.DoesNotExist:
        return 404, {"error": "Patient non trouvé"}

    user = get_authenticated_user(request)
    if user.role == ROLE_PATIENT and (not hasattr(user, 'patient') or user.patient.id != patient.id):
        return 403, {"error": "Accès refusé"}
    journaliser_acces(request, patient_id, 'QR_ACCESS_GENERATION')
    payload = generate_patient_qr(patient.id, user.id)
    return 200, {
        "patient_id": patient.id,
        "numero_dossier": patient.numero_dossier,
        **payload,
    }


@router.post("/patients/qr-access/verify", response={200: dict, 400: dict, 401: dict, 403: dict, 404: dict})
@role_required([ROLE_MEDECIN, ROLE_INFIRMIER])
def verify_patient_qr_access(request, payload: QRAccessVerifySchema):
    from django.core import signing
    try:
        data = verify_patient_qr_token(payload.token)
        patient = Patient.objects.get(id=data['patient_id'], est_actif=True)
    except signing.SignatureExpired:
        return 403, {"error": "Accès QR expiré"}
    except (signing.BadSignature, ValueError, KeyError):
        return 403, {"error": "Token QR invalide"}
    except Patient.DoesNotExist:
        return 404, {"error": "Patient non trouvé"}

    journaliser_acces(request, patient.id, 'QR_ACCESS_GRANTED')
    admission = patient.admission_active()
    return 200, {
        "authorized": True,
        "expires_at": data['exp'],
        "patient": {
            "id": patient.id,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "numero_dossier": patient.numero_dossier,
            "date_naissance": patient.date_naissance.isoformat(),
            "telephone": patient.telephone,
            "email": patient.email,
            "admission_active_id": admission.id if admission else None,
        },
    }


# --- Admissions ---

@router.post("/admissions", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_SECRETAIRE, ROLE_MEDECIN])
def create_admission_endpoint(request, payload: AdmissionSchema):
    try:
        admission = creer_admission(**payload.dict())
        audit_log(request, 'CREATE', admission, new_value=str(payload.dict()))
        try:
            from billing.secretariat_services import creer_invoice_consultation
            creer_invoice_consultation(
                patient_id=admission.patient_id,
                admission_id=admission.id,
            )
        except Exception:
            pass
        return 201, {
            "id": admission.id,
            "message": "Admission créée avec succès",
            "admission": serialiser_admission(admission),
        }
    except HospitalisationError as e:
        if "Conflit de version" in str(e):
            return 409, {"error": str(e)}
        return 400, {"error": str(e)}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/admissions/actives", response={200: dict, 401: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_SECRETAIRE])
def get_admissions_actives(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Admission.objects.filter(statut='EN_COURS').select_related(
        'patient', 'service', 'lit', 'medecin_referent',
    ).order_by('-date_entree')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([serialiser_admission(a) for a in rows], meta)


@router.get("/admissions/{admission_id}", response={200: dict, 404: dict, 401: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_SECRETAIRE])
def get_admission_detail(request, admission_id: int):
    try:
        admission = Admission.objects.select_related(
            'patient', 'service', 'lit', 'medecin_referent'
        ).get(id=admission_id)
        return 200, serialiser_admission(admission)
    except Admission.DoesNotExist:
        return 404, {"error": "Admission non trouvée"}


@router.get("/admissions/patient/{patient_id}", response={200: dict, 401: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_SECRETAIRE])
def get_admissions_patient(request, patient_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Admission.objects.filter(patient_id=patient_id).select_related(
        'patient', 'service', 'lit', 'medecin_referent',
    ).order_by('-date_entree')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([serialiser_admission(a) for a in rows], meta)


@router.post("/admissions/{admission_id}/sortie", response={200: dict, 400: dict, 409: dict, 404: dict})
@role_required([ROLE_MEDECIN, ROLE_SECRETAIRE])
def sortie_admission(request, admission_id: int, payload: SortieSchema):
    try:
        old = serialiser_admission(Admission.objects.get(id=admission_id))
        admission = sortir_patient(
            admission_id,
            statut=payload.statut,
            notes=payload.notes or '',
            version=payload.version,
        )
        audit_log(
            request, 'UPDATE', admission,
            old_value=str(old),
            new_value=f"Sortie — statut {payload.statut}",
        )
        return 200, {
            "message": "Sortie enregistrée, lit libéré",
            "admission": serialiser_admission(admission),
        }
    except Admission.DoesNotExist:
        return 404, {"error": "Admission non trouvée"}
    except ValueError as e:
        if "Conflit de version" in str(e):
            return 409, {"error": str(e)}
        return 400, {"error": str(e)}
    except HospitalisationError as e:
        if "Conflit de version" in str(e):
            return 409, {"error": str(e)}
        return 400, {"error": str(e)}


@router.post("/admissions/{admission_id}/transfert", response={200: dict, 400: dict, 409: dict, 404: dict})
@role_required([ROLE_MEDECIN, ROLE_SECRETAIRE])
def transfert_admission(request, admission_id: int, payload: TransfertSchema):
    try:
        old = serialiser_admission(Admission.objects.get(id=admission_id))
        admission = transferer_patient(
            admission_id,
            payload.nouveau_service_id,
            payload.nouveau_lit_id,
            motif=payload.motif or '',
            version=payload.version,
        )
        audit_log(
            request, 'UPDATE', admission,
            old_value=str(old),
            new_value=f"Transfert vers service {payload.nouveau_service_id}",
        )
        return 200, {
            "message": "Transfert effectué avec succès",
            "admission": serialiser_admission(admission),
        }
    except Admission.DoesNotExist:
        return 404, {"error": "Admission non trouvée"}
    except ValueError as e:
        if "Conflit de version" in str(e):
            return 409, {"error": str(e)}
        return 400, {"error": str(e)}
    except HospitalisationError as e:
        if "Conflit de version" in str(e):
            return 409, {"error": str(e)}
        return 400, {"error": str(e)}


# --- Consultations ---

@router.post("/consultations", response={201: dict, 400: dict, 401: dict, 403: dict, 402: dict})
@role_required([ROLE_MEDECIN])
def create_consultation(request, payload: ConsultationSchema):
    try:
        data = payload.dict()
        admission_id = data.pop('admission_id', None)

        if admission_id:
            admission = verifier_admission_pour_soins(admission_id)
            if admission.patient_id != data['patient_id']:
                return 400, {"error": "L'admission ne correspond pas au patient"}
            data['admission_id'] = admission_id
        elif Patient.objects.get(id=data['patient_id']).admission_active():
            return 400, {
                "error": "Patient hospitalisé : une admission active doit être liée à la consultation",
            }

        from billing.secretariat_services import verifier_paiement_consultation
        erreur_paiement = verifier_paiement_consultation(
            patient_id=data['patient_id'],
            admission_id=admission_id,
        )
        if erreur_paiement:
            return 402, {"error": erreur_paiement, "code": "PAYMENT_REQUIRED"}

        consultation = Consultation.objects.create(**data)
        audit_log(request, 'CREATE', consultation, new_value=str(payload.dict()))
        return 201, {"id": consultation.id, "message": "Consultation enregistrée"}
    except Patient.DoesNotExist:
        return 404, {"error": "Patient non trouvé"}
    except HospitalisationError as e:
        if "Conflit de version" in str(e):
            return 409, {"error": str(e)}
        return 400, {"error": str(e)}
    except Exception as e:
        return 400, {"error": str(e)}


class PlanSoinSchema(Schema):
    patient_id: int
    admission_id: int
    prescription_id: Optional[int] = None
    infirmier_responsable_id: Optional[int] = None
    medecin_prescripteur_id: Optional[int] = None
    titre: str
    description: str
    frequence: str = ''
    date_debut: date
    date_fin: Optional[date] = None


@router.get("/consultations/patient/{patient_id}", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_PATIENT])
def get_consultations_patient(request, patient_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    denied = enforce_patient_scope(request, patient_id)
    if denied:
        return denied
    journaliser_acces(request, patient_id, 'LECTURE_CONSULTATIONS')
    qs = Consultation.objects.filter(patient_id=patient_id).select_related('medecin').order_by('-date_consultation')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {
            'id': c.id,
            'date_consultation': c.date_consultation.isoformat(),
            'motif': c.motif,
            'diagnostic': c.diagnostic,
            'diagnostic_cim10': c.diagnostic_cim10,
            'medecin__username': c.medecin.username,
            'admission_id': c.admission_id,
        }
        for c in rows
    ]
    return 200, paginated_response(items, meta)


@router.get("/constantes/patient/{patient_id}", response={200: dict, 403: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_PATIENT])
def get_constantes_patient(request, patient_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    denied = enforce_patient_scope(request, patient_id)
    if denied:
        return denied
    qs = ConstanteVitale.objects.filter(patient_id=patient_id).order_by('-date_saisie')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            'id': c.id,
            'date_saisie': c.date_saisie.isoformat(),
            'tension_arterielle': c.tension_arterielle,
            'frequence_cardiaque': c.frequence_cardiaque,
            'temperature': float(c.temperature) if c.temperature else None,
            'saturation_o2': c.saturation_o2,
            'poids': float(c.poids) if c.poids else None,
        }
        for c in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/plans-soins", response={201: dict, 400: dict, 403: dict})
@role_required([ROLE_MEDECIN, ROLE_INFIRMIER])
def create_plan_soin(request, payload: PlanSoinSchema):
    try:
        admission = verifier_admission_pour_soins(payload.admission_id)
        if admission.patient_id != payload.patient_id:
            return 400, {"error": "L'admission ne correspond pas au patient"}
        plan = PlanSoin.objects.create(**payload.dict())
        audit_log(request, 'CREATE', plan, new_value=str(payload.dict()))
        return 201, {"id": plan.id, "message": "Plan de soins créé"}
    except HospitalisationError as e:
        if "Conflit de version" in str(e):
            return 409, {"error": str(e)}
        return 400, {"error": str(e)}


@router.get("/plans-soins/patient/{patient_id}", response={200: dict, 403: dict})
@role_required([ROLE_MEDECIN, ROLE_INFIRMIER, ROLE_ADMIN, ROLE_PATIENT])
def list_plans_soins(request, patient_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    denied = enforce_patient_scope(request, patient_id)
    if denied:
        return denied
    qs = PlanSoin.objects.filter(patient_id=patient_id).order_by('-date_creation')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {
            'id': p.id,
            'titre': p.titre,
            'description': p.description,
            'frequence': p.frequence,
            'date_debut': p.date_debut.isoformat(),
            'date_fin': p.date_fin.isoformat() if p.date_fin else None,
            'statut': p.statut,
        }
        for p in rows
    ]
    return 200, paginated_response(items, meta)


# --- Constantes vitales ---

@router.post("/constantes", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_INFIRMIER])
def create_constante(request, payload: ConstanteSchema):
    try:
        admission = verifier_admission_pour_soins(payload.admission_id)
        if admission.patient_id != payload.patient_id:
            return 400, {"error": "L'admission ne correspond pas au patient"}

        user_id = request.auth_payload['id']
        constante = ConstanteVitale.objects.create(
            **payload.dict(),
            infirmier_id=user_id,
        )
        audit_log(request, 'CREATE', constante, new_value=str(payload.dict()))
        return 201, {"id": constante.id, "message": "Constantes enregistrées"}
    except HospitalisationError as e:
        if "Conflit de version" in str(e):
            return 409, {"error": str(e)}
        return 400, {"error": str(e)}
    except Exception as e:
        return 400, {"error": str(e)}
