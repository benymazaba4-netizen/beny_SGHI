from ninja import Router, Schema
from typing import List, Optional
from django.http import FileResponse, Http404
from django.conf import settings
import os

from .models import ExamenType, DemandeExamen, Prelevement, ResultatExamen, HistoriqueModificationResultat, LISError
from .services import (
    serialiser_demande,
    serialiser_resultat,
    creer_demande,
    enregistrer_prelevement,
    affecter_demande,
    saisir_resultat,
    modifier_resultat,
    valider_et_publier,
)
from authentication.models import Utilisateur
from common.permissions import (
    auth_bearer, role_required,
    ROLE_BIOLOGISTE, ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER,
    ROLE_CLINICAL, ROLE_PATIENT,
)
from common.audit_utils import audit_log, get_authenticated_user

router = Router(auth=auth_bearer)


class ExamenTypeSchema(Schema):
    code: str
    nom: str
    categorie: str = 'AUTRE'
    prix: float = 0
    jeun_requis: bool = False


class DemandeExamenSchema(Schema):
    patient_id: int
    medecin_prescripteur_id: int
    consultation_id: int
    examen_type_id: int
    urgence: bool = False
    notes_prescripteur: str = ''


class PrelevementSchema(Schema):
    demande_id: int
    type_prelevement: str = 'SANG'
    tube_type: str = ''
    conditions: str = ''


class AffectationSchema(Schema):
    biologiste_id: int


class ResultatSchema(Schema):
    demande_id: int
    resultats: str
    interpretation: str = ''


class ResultatUpdateSchema(Schema):
    resultats: str
    interpretation: str = ''


# --- Types d'examens ---

@router.post("/examens-types", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_BIOLOGISTE])
def create_examen_type(request, payload: ExamenTypeSchema):
    try:
        examen = ExamenType.objects.create(**payload.dict())
        audit_log(request, 'CREATE', examen, new_value=str(payload.dict()))
        return 201, {"id": examen.id, "message": "Type d'examen créé"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/examens-types", response={200: dict, 401: dict})
@role_required(ROLE_CLINICAL + [ROLE_BIOLOGISTE])
def list_examens_types(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = ExamenType.objects.filter(est_actif=True).order_by('code')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {'id': e.id, 'code': e.code, 'nom': e.nom, 'categorie': e.categorie, 'prix': float(e.prix), 'jeun_requis': e.jeun_requis}
        for e in rows
    ]
    return 200, paginated_response(items, meta)


# --- Demandes ---

@router.post("/demandes", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_MEDECIN])
def create_demande(request, payload: DemandeExamenSchema):
    try:
        demande = creer_demande(
            patient_id=payload.patient_id,
            medecin_prescripteur_id=payload.medecin_prescripteur_id,
            consultation_id=payload.consultation_id,
            examen_type_id=payload.examen_type_id,
            urgence=payload.urgence,
            notes_prescripteur=payload.notes_prescripteur,
        )
        audit_log(request, 'CREATE', demande, new_value=str(payload.dict()))
        return 201, {
            "id": demande.id,
            "message": "Demande d'examen créée",
            "demande": serialiser_demande(demande),
        }
    except LISError as e:
        return 400, {"error": str(e)}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/demandes/{demande_id}", response={200: dict, 404: dict, 401: dict})
@role_required(ROLE_CLINICAL + [ROLE_BIOLOGISTE])
def get_demande(request, demande_id: int):
    try:
        demande = DemandeExamen.objects.select_related(
            'patient', 'examen_type', 'medecin_prescripteur', 'affecte_a', 'valide_par',
        ).get(id=demande_id)
        data = serialiser_demande(demande)
        if hasattr(demande, 'resultat'):
            data['resultat'] = serialiser_resultat(demande.resultat)
        return 200, data
    except DemandeExamen.DoesNotExist:
        return 404, {"error": "Demande non trouvée"}


@router.get("/demandes/patient/{patient_id}", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_BIOLOGISTE, ROLE_INFIRMIER, ROLE_PATIENT])
def get_demandes_patient(request, patient_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    user = get_authenticated_user(request)
    if user and user.role == ROLE_PATIENT:
        if not hasattr(user, 'patient') or user.patient.id != patient_id:
            return 403, {"error": "Accès refusé"}

    qs = DemandeExamen.objects.filter(patient_id=patient_id).select_related(
        'patient', 'examen_type', 'medecin_prescripteur',
    ).order_by('-date_prescription')

    if user and user.role == ROLE_PATIENT:
        qs = qs.filter(statut='VALIDE', resultat__est_publie=True)

    demandes, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([serialiser_demande(d) for d in demandes], meta)


@router.get("/demandes/en-cours", response={200: dict, 401: dict})
@role_required([ROLE_BIOLOGISTE, ROLE_ADMIN])
def demandes_en_cours(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = DemandeExamen.objects.filter(
        statut__in=['PRELEVE', 'EN_COURS'],
    ).select_related('patient', 'examen_type').order_by('-date_prescription')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([serialiser_demande(d) for d in rows], meta)


@router.get("/demandes/attente-validation", response={200: dict, 401: dict})
@role_required([ROLE_BIOLOGISTE])
def demandes_attente_validation(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = DemandeExamen.objects.filter(statut='VALIDATION').select_related(
        'patient', 'examen_type',
    ).order_by('-date_prescription')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([serialiser_demande(d) for d in rows], meta)


# --- Workflow : Prélèvement ---

@router.post("/prelevements", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_INFIRMIER])
def create_prelevement(request, payload: PrelevementSchema):
    try:
        user_id = request.auth_payload['id']
        data = {
            'type_prelevement': payload.type_prelevement,
            'tube_type': payload.tube_type,
            'conditions': payload.conditions,
        }
        prelevement = enregistrer_prelevement(payload.demande_id, user_id, data)
        audit_log(request, 'CREATE', prelevement, new_value=str(payload.dict()))
        return 201, {
            "id": prelevement.id,
            "message": "Prélèvement enregistré — statut : PRELEVE",
            "demande": serialiser_demande(prelevement.demande),
        }
    except LISError as e:
        return 400, {"error": str(e)}
    except Exception as e:
        return 400, {"error": str(e)}


# --- Workflow : Affectation ---

@router.post("/demandes/{demande_id}/affecter", response={200: dict, 400: dict, 404: dict, 403: dict})
@role_required([ROLE_BIOLOGISTE])
def affecter_demande_endpoint(request, demande_id: int, payload: AffectationSchema):
    try:
        demande = affecter_demande(demande_id, payload.biologiste_id)
        audit_log(
            request, 'UPDATE', demande,
            new_value=f"Affecté au biologiste {payload.biologiste_id}",
        )
        return 200, {
            "message": "Demande affectée — statut : EN_COURS",
            "demande": serialiser_demande(demande),
        }
    except DemandeExamen.DoesNotExist:
        return 404, {"error": "Demande non trouvée"}
    except LISError as e:
        return 400, {"error": str(e)}
    except Utilisateur.DoesNotExist:
        return 400, {"error": "Biologiste introuvable"}


# --- Workflow : Saisie résultats ---

@router.post("/resultats", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_BIOLOGISTE])
def create_resultat(request, payload: ResultatSchema):
    try:
        user_id = request.auth_payload['id']
        resultat = saisir_resultat(
            payload.demande_id, user_id, payload.resultats, payload.interpretation,
        )
        audit_log(request, 'CREATE', resultat, new_value=str(payload.dict()))
        return 201, {
            "id": resultat.id,
            "message": "Résultat saisi — statut : VALIDATION",
            "resultat": serialiser_resultat(resultat),
        }
    except LISError as e:
        return 400, {"error": str(e)}
    except Exception as e:
        return 400, {"error": str(e)}


@router.put("/resultats/{resultat_id}", response={200: dict, 400: dict, 403: dict, 404: dict})
@role_required([ROLE_BIOLOGISTE])
def update_resultat(request, resultat_id: int, payload: ResultatUpdateSchema):
    try:
        user_id = request.auth_payload['id']
        old = serialiser_resultat(ResultatExamen.objects.get(id=resultat_id))
        resultat = modifier_resultat(
            resultat_id, user_id, payload.resultats, payload.interpretation, request,
        )
        audit_log(
            request, 'UPDATE', resultat,
            old_value=str(old),
            new_value=str(payload.dict()),
        )
        return 200, {
            "message": "Résultat modifié (audit enregistré)",
            "resultat": serialiser_resultat(resultat),
        }
    except ResultatExamen.DoesNotExist:
        return 404, {"error": "Résultat non trouvé"}
    except PermissionError as e:
        return 403, {"error": str(e)}
    except LISError as e:
        return 400, {"error": str(e)}


@router.get("/resultats/{resultat_id}", response={200: dict, 403: dict, 404: dict, 401: dict})
@role_required(ROLE_CLINICAL + [ROLE_BIOLOGISTE, ROLE_PATIENT])
def get_resultat(request, resultat_id: int):
    try:
        resultat = ResultatExamen.objects.select_related('demande__patient').get(id=resultat_id)
        user = get_authenticated_user(request)
        if user.role == ROLE_PATIENT:
            if not resultat.est_publie:
                return 403, {"error": "Résultat non encore publié"}
            if not hasattr(user, 'patient') or resultat.demande.patient_id != user.patient.id:
                return 403, {"error": "Accès refusé"}
        return 200, serialiser_resultat(resultat)
    except ResultatExamen.DoesNotExist:
        return 404, {"error": "Résultat non trouvé"}


@router.get("/resultats/{resultat_id}/historique", response={200: dict, 404: dict})
@role_required([ROLE_BIOLOGISTE, ROLE_ADMIN])
def get_historique_resultat(request, resultat_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    try:
        ResultatExamen.objects.get(id=resultat_id)
        qs = HistoriqueModificationResultat.objects.filter(
            resultat_id=resultat_id,
        ).select_related('modifie_par').order_by('-timestamp')
        rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
        items = [
            {
                "id": h.id,
                "modifie_par": h.modifie_par.get_full_name() if h.modifie_par else None,
                "timestamp": h.timestamp.isoformat(),
                "anciens_resultats": h.anciens_resultats,
                "nouveaux_resultats": h.nouveaux_resultats,
                "ip_adresse": h.ip_adresse,
            }
            for h in rows
        ]
        return 200, paginated_response(items, meta)
    except ResultatExamen.DoesNotExist:
        return 404, {"error": "Résultat non trouvé"}


# --- Workflow : Validation + Publication + PDF ---

@router.post("/resultats/{resultat_id}/valider", response={200: dict, 400: dict, 403: dict, 404: dict})
@role_required([ROLE_BIOLOGISTE])
def valider_resultat(request, resultat_id: int):
    try:
        user_id = request.auth_payload['id']
        resultat = valider_et_publier(resultat_id, user_id)
        audit_log(request, 'VALIDATE', resultat, new_value="Validé, PDF généré et publié")
        return 200, {
            "message": "Résultat validé, PDF généré et publié",
            "resultat": serialiser_resultat(resultat),
        }
    except ResultatExamen.DoesNotExist:
        return 404, {"error": "Résultat non trouvé"}
    except LISError as e:
        return 400, {"error": str(e)}
    except PermissionError as e:
        return 403, {"error": str(e)}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/resultats/{resultat_id}/pdf")
@role_required([ROLE_MEDECIN, ROLE_BIOLOGISTE, ROLE_ADMIN, ROLE_PATIENT])
def download_pdf(request, resultat_id: int):
    try:
        resultat = ResultatExamen.objects.select_related('demande__patient').get(id=resultat_id)
        user = get_authenticated_user(request)

        if not resultat.est_valide or not resultat.fichier_pdf:
            return 404, {"error": "PDF non disponible"}

        if user.role == ROLE_PATIENT:
            if not resultat.est_publie:
                return 403, {"error": "Accès refusé"}
            if not hasattr(user, 'patient') or resultat.demande.patient_id != user.patient.id:
                return 403, {"error": "Accès refusé"}

        filepath = os.path.join(settings.MEDIA_ROOT, str(resultat.fichier_pdf))
        if not os.path.exists(filepath):
            return 404, {"error": "Fichier PDF introuvable"}

        audit_log(request, 'READ', resultat, new_value="Téléchargement PDF")
        return FileResponse(
            open(filepath, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=os.path.basename(filepath),
        )
    except ResultatExamen.DoesNotExist:
        return 404, {"error": "Résultat non trouvé"}
