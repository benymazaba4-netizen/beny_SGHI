from ninja import Router, Schema
from typing import List, Optional
from decimal import Decimal
import os
from datetime import date as date_type

from django.http import FileResponse
from django.conf import settings
from django.utils import timezone

from .models import Facture, LigneFacture, TransactionPaiement, Assurance, PriseEnChargeAssurance, JournalComptable, EcheancePaiement, BillingError
from .services import (
    serialiser_facture,
    generer_facture_automatique,
    appliquer_tiers_payant,
    emettre_facture,
)
from common.permissions import (
    auth_bearer, role_required,
    ROLE_ADMIN, ROLE_COMPTABLE, ROLE_SECRETAIRE, ROLE_PATIENT, ROLE_MEDECIN,
)
from common.audit_utils import audit_log, get_authenticated_user

router = Router(auth=auth_bearer)


class FactureSchema(Schema):
    patient_id: int
    admission_id: Optional[int] = None


class GenererFactureSchema(Schema):
    patient_id: int
    admission_id: int


class LigneFactureSchema(Schema):
    facture_id: int
    type_ligne: str
    description: str
    quantite: int = 1
    prix_unitaire: Decimal


class PaiementSchema(Schema):
    facture_id: int
    mode_paiement: str
    montant: Decimal
    numero_telephone: str = ''
    operateur: str = ''


class EcheanceIn(Schema):
    date_echeance: str
    montant: Decimal
    notes: str = ''


class EcheancierIn(Schema):
    echeances: List[EcheanceIn]


class AssuranceSchema(Schema):
    nom: str
    code: str
    taux_prise_en_charge: int = 70
    contact: str = ''
    telephone: str = ''


class PriseEnChargeSchema(Schema):
    patient_id: int
    assurance_id: int
    numero_contrat: str
    date_debut: str
    date_fin: str


# --- Génération automatique ---

@router.post("/factures/generer-automatique", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_SECRETAIRE])
def generer_facture_auto(request, payload: GenererFactureSchema):
    """Moteur de calcul : nuitées + consultations + examens + médicaments."""
    try:
        user_id = request.auth_payload['id']
        facture = generer_facture_automatique(
            payload.patient_id, payload.admission_id, user_id,
        )
        audit_log(request, 'CREATE', facture, new_value="Facture auto-générée")
        return 201, {
            "message": "Facture brouillon générée automatiquement",
            "facture": serialiser_facture(facture),
        }
    except BillingError as e:
        return 400, {"error": str(e)}
    except Exception as e:
        return 400, {"error": str(e)}


@router.post("/factures/{facture_id}/tiers-payant", response={200: dict, 400: dict, 404: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE])
def appliquer_tiers_payant_endpoint(request, facture_id: int):
    try:
        facture, prise = appliquer_tiers_payant(facture_id)
        audit_log(request, 'UPDATE', facture, new_value="Tiers-payant appliqué")
        return 200, {
            "message": "Tiers-payant appliqué" if prise else "Aucune assurance active",
            "facture": serialiser_facture(facture),
            "assurance": prise.assurance.nom if prise else None,
        }
    except Facture.DoesNotExist:
        return 404, {"error": "Facture non trouvée"}
    except BillingError as e:
        return 400, {"error": str(e)}


@router.post("/factures/{facture_id}/emettre", response={200: dict, 400: dict, 404: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE])
def emettre_facture_endpoint(request, facture_id: int):
    try:
        user_id = request.auth_payload['id']
        facture = emettre_facture(facture_id, user_id)
        audit_log(request, 'UPDATE', facture, new_value="Facture émise + PDF")
        return 200, {
            "message": "Facture émise — PDF généré — journal comptable enregistré",
            "facture": serialiser_facture(facture),
        }
    except Facture.DoesNotExist:
        return 404, {"error": "Facture non trouvée"}
    except BillingError as e:
        return 400, {"error": str(e)}


@router.get("/factures/{facture_id}", response={200: dict, 403: dict, 404: dict, 401: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_SECRETAIRE, ROLE_MEDECIN, ROLE_PATIENT])
def get_facture(request, facture_id: int):
    try:
        facture = Facture.objects.select_related('patient').prefetch_related('lignes').get(id=facture_id)
        user = get_authenticated_user(request)
        if user.role == ROLE_PATIENT:
            if not hasattr(user, 'patient') or facture.patient_id != user.patient.id:
                return 403, {"error": "Accès refusé"}
        return 200, serialiser_facture(facture)
    except Facture.DoesNotExist:
        return 404, {"error": "Facture non trouvée"}


@router.get("/factures/{facture_id}/pdf")
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_SECRETAIRE, ROLE_PATIENT])
def download_facture_pdf(request, facture_id: int):
    try:
        facture = Facture.objects.select_related('patient').get(id=facture_id)
        user = get_authenticated_user(request)
        if user.role == ROLE_PATIENT:
            if not hasattr(user, 'patient') or facture.patient_id != user.patient.id:
                return 403, {"error": "Accès refusé"}
        if not facture.fichier_pdf:
            return 404, {"error": "PDF non disponible — émettez la facture d'abord"}
        filepath = os.path.join(settings.MEDIA_ROOT, str(facture.fichier_pdf))
        if not os.path.exists(filepath):
            return 404, {"error": "Fichier introuvable"}
        return FileResponse(
            open(filepath, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"{facture.numero_facture}.pdf",
        )
    except Facture.DoesNotExist:
        return 404, {"error": "Facture non trouvée"}


@router.get("/journal", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE])
def get_journal_comptable(request, facture_id: Optional[int] = None, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = JournalComptable.objects.select_related('facture', 'utilisateur').order_by('-timestamp')
    if facture_id:
        qs = qs.filter(facture_id=facture_id)
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            "id": e.id,
            "facture": e.facture.numero_facture,
            "type_operation": e.type_operation,
            "montant": float(e.montant),
            "description": e.description,
            "timestamp": e.timestamp.isoformat(),
            "hash": e.hash_signature[:16] + "...",
        }
        for e in rows
    ]
    return 200, paginated_response(items, meta)


# --- CRUD manuel (conservé) ---

@router.post("/factures", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_SECRETAIRE])
def create_facture(request, payload: FactureSchema):
    try:
        user_id = request.auth_payload['id']
        facture = Facture.objects.create(**payload.dict(), emise_par_id=user_id)
        audit_log(request, 'CREATE', facture, new_value=str(payload.dict()))
        return 201, {"id": facture.id, "numero": facture.numero_facture}
    except Exception as e:
        return 400, {"error": str(e)}


@router.post("/factures/lignes", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE])
def add_ligne_facture(request, payload: LigneFactureSchema):
    try:
        facture = Facture.objects.get(id=payload.facture_id)
        if facture.statut != 'BROUILLON':
            return 400, {"error": "Modification impossible — facture déjà émise"}
        ligne = LigneFacture.objects.create(**payload.dict())
        audit_log(request, 'CREATE', ligne, new_value=str(payload.dict()))
        return 201, {"id": ligne.id, "montant": float(ligne.montant)}
    except Facture.DoesNotExist:
        return 404, {"error": "Facture non trouvée"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/factures/patient/{patient_id}", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_SECRETAIRE, ROLE_MEDECIN, ROLE_PATIENT])
def get_factures_patient(request, patient_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    user = get_authenticated_user(request)
    if user.role == ROLE_PATIENT:
        if not hasattr(user, 'patient') or user.patient.id != patient_id:
            return 403, {"error": "Accès refusé"}
    qs = Facture.objects.filter(patient_id=patient_id).select_related('patient').order_by('-date_emission')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([serialiser_facture(f) for f in rows], meta)


@router.post("/paiements", response={200: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_PATIENT])
def enregistrer_paiement(request, payload: PaiementSchema):
    import uuid as uuid_lib
    try:
        user = get_authenticated_user(request)
        user_id = request.auth_payload['id']
        facture = Facture.objects.select_related('patient').get(id=payload.facture_id)
        if user.role == ROLE_PATIENT:
            if not hasattr(user, 'patient') or facture.patient_id != user.patient.id:
                return 403, {"error": "Accès refusé à cette facture"}
        if payload.montant <= 0:
            return 400, {"error": "Montant invalide"}
        if payload.montant > facture.montant_restant:
            return 400, {"error": "Montant supérieur au solde restant"}

        mode = payload.mode_paiement
        if mode in ('MTN', 'AIRTEL') and not payload.numero_telephone:
            return 400, {"error": "Numéro de téléphone requis pour Mobile Money"}

        ref = f"MM-{uuid_lib.uuid4().hex[:12].upper()}"
        if mode in ('MTN', 'AIRTEL'):
            ref = f"{mode}-{ref}"

        transaction = TransactionPaiement.objects.create(
            facture=facture,
            mode_paiement=mode,
            montant=payload.montant,
            numero_telephone=payload.numero_telephone,
            operateur=payload.operateur or mode,
            statut='SUCCESS',
            effectue_par_id=user_id,
            transaction_id=ref,
            reference_externe=ref,
            api_response={
                'simulated': True,
                'provider': mode,
                'status': 'SUCCESS',
                'reference': ref,
            },
        )
        transaction.confirmer_paiement()

        # Marquer échéances couvertes par le montant
        reste = payload.montant
        for ech in facture.echeances.filter(est_payee=False).order_by('date_echeance'):
            if reste >= ech.montant:
                ech.est_payee = True
                ech.date_paiement = timezone.now()
                ech.save(update_fields=['est_payee', 'date_paiement'])
                reste -= ech.montant

        audit_log(request, 'CREATE', transaction, new_value=str(payload.dict()))
        return 200, {
            "status": "success",
            "transaction_id": transaction.id,
            "reference": ref,
            "montant_restant": float(transaction.facture.montant_restant),
            "statut_facture": transaction.facture.statut,
            "message": f"Paiement de {payload.montant} FCFA enregistré",
        }
    except Facture.DoesNotExist:
        return 404, {"error": "Facture non trouvée"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.post("/paiements/mobile-money", response={200: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_PATIENT])
def paiement_mobile_money(request, payload: PaiementSchema):
    data = payload.dict()
    if data['mode_paiement'] not in ('MTN', 'AIRTEL'):
        data['mode_paiement'] = data.get('operateur') or 'MTN'
    return enregistrer_paiement(request, PaiementSchema(**data))


@router.get("/factures/{facture_id}/echeancier", response={200: dict, 404: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_PATIENT])
def get_echeancier(request, facture_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    try:
        facture = Facture.objects.get(id=facture_id)
        user = get_authenticated_user(request)
        if user.role == ROLE_PATIENT:
            if not hasattr(user, 'patient') or facture.patient_id != user.patient.id:
                return 403, {"error": "Accès refusé"}
        qs = facture.echeances.all().order_by('date_echeance')
        rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
        items = [
            {
                'id': e.id,
                'date_echeance': e.date_echeance.isoformat(),
                'montant': float(e.montant),
                'est_payee': e.est_payee,
                'date_paiement': e.date_paiement.isoformat() if e.date_paiement else None,
            }
            for e in rows
        ]
        return 200, paginated_response(items, meta)
    except Facture.DoesNotExist:
        return 404, {"error": "Facture non trouvée"}


@router.post("/factures/{facture_id}/echeancier", response={201: dict, 400: dict, 404: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE])
def create_echeancier(request, facture_id: int, payload: EcheancierIn):
    try:
        facture = Facture.objects.get(id=facture_id)
        if not payload.echeances:
            return 400, {"error": "Au moins une échéance requise"}
        facture.echeances.all().delete()
        total = Decimal('0')
        created = []
        for ech in payload.echeances:
            obj = EcheancePaiement.objects.create(
                facture=facture,
                date_echeance=date_type.fromisoformat(ech.date_echeance),
                montant=ech.montant,
                notes=ech.notes,
            )
            total += ech.montant
            created.append(obj.id)
        audit_log(request, 'CREATE', facture, new_value=f"Échéancier {len(created)} échéance(s)")
        return 201, {
            "message": f"Échéancier créé ({len(created)} échéance(s))",
            "total_echeances": float(total),
            "montant_facture": float(facture.montant_patient),
        }
    except Facture.DoesNotExist:
        return 404, {"error": "Facture non trouvée"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.post("/assurances", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def create_assurance(request, payload: AssuranceSchema):
    try:
        assurance = Assurance.objects.create(**payload.dict())
        audit_log(request, 'CREATE', assurance, new_value=str(payload.dict()))
        return 201, {"id": assurance.id, "message": "Assurance enregistrée"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/assurances", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_SECRETAIRE])
def list_assurances(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Assurance.objects.filter(est_actif=True).order_by('nom')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {
            'id': a.id,
            'nom': a.nom,
            'code': a.code,
            'taux_prise_en_charge': float(a.taux_prise_en_charge),
            'telephone': a.telephone,
        }
        for a in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/prises-en-charge", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_SECRETAIRE])
def create_prise_en_charge(request, payload: PriseEnChargeSchema):
    try:
        from datetime import date as date_type
        prise = PriseEnChargeAssurance.objects.create(
            patient_id=payload.patient_id,
            assurance_id=payload.assurance_id,
            numero_contrat=payload.numero_contrat,
            date_debut=date_type.fromisoformat(payload.date_debut),
            date_fin=date_type.fromisoformat(payload.date_fin),
        )
        audit_log(request, 'CREATE', prise, new_value=str(payload.dict()))
        return 201, {"id": prise.id, "message": "Prise en charge enregistrée"}
    except Exception as e:
        return 400, {"error": str(e)}
