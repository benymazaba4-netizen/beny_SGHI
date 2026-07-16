from ninja import Router, Schema
from typing import List, Optional
from datetime import date, time, datetime
from django.utils import timezone
from .models import Personnel, PlanningGarde, Presence, Conge, FichePaie
from common.permissions import auth_bearer, role_required, ROLE_ADMIN
from common.audit_utils import audit_log, get_authenticated_user

router = Router(auth=auth_bearer)


class PersonnelOut(Schema):
    id: int
    matricule: str
    nom: str
    type_personnel: str
    service: str
    est_actif: bool


class PlanningOut(Schema):
    id: int
    personnel: str
    service: str
    type_garde: str
    date_debut: str
    date_fin: str
    est_effectuee: bool


class PresenceOut(Schema):
    id: int
    personnel: str
    date: str
    statut: str
    heure_arrivee: Optional[str] = None
    heure_depart: Optional[str] = None


class PresenceIn(Schema):
    personnel_id: int
    date: date
    statut: str = 'PRESENT'
    heure_arrivee: Optional[time] = None
    heure_depart: Optional[time] = None
    commentaire: str = ''


class CongeOut(Schema):
    id: int
    personnel: str
    type_conge: str
    statut: str
    date_debut: str
    date_fin: str
    nb_jours: int
    motif: str


class CongeIn(Schema):
    personnel_id: int
    type_conge: str
    date_debut: date
    date_fin: date
    motif: str


class CongeValidationIn(Schema):
    statut: str
    commentaire_validation: str = ''


class FichePaieOut(Schema):
    id: int
    personnel: str
    mois: int
    annee: int
    salaire_base: float
    primes: float
    deductions: float
    net_a_payer: float


class FichePaieIn(Schema):
    personnel_id: int
    mois: int
    annee: int
    salaire_base: float
    primes: float = 0
    deductions: float = 0
    nb_heures_sup: int = 0
    montant_heures_sup: float = 0


class PlanningGardeIn(Schema):
    personnel_id: int
    service_id: int
    type_garde: str
    date_debut: datetime
    date_fin: datetime
    commentaire: str = ''


@router.get("/personnel", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def list_personnel(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Personnel.objects.select_related('utilisateur', 'service').order_by('matricule')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            "id": p.id,
            "matricule": p.matricule,
            "nom": p.utilisateur.get_full_name() or p.utilisateur.username,
            "type_personnel": p.type_personnel,
            "service": p.service.nom if p.service else '—',
            "est_actif": p.est_actif,
        }
        for p in rows
    ]
    return 200, paginated_response(items, meta)


@router.get("/planning-gardes", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def list_planning_gardes(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = PlanningGarde.objects.select_related(
        'personnel__utilisateur', 'service',
    ).order_by('-date_debut')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            "id": g.id,
            "personnel": g.personnel.utilisateur.get_full_name() or g.personnel.matricule,
            "service": g.service.nom,
            "type_garde": g.type_garde,
            "date_debut": g.date_debut.isoformat(),
            "date_fin": g.date_fin.isoformat(),
            "est_effectuee": g.est_effectuee,
        }
        for g in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/planning-gardes", response={201: PlanningOut, 400: dict, 403: dict})
@role_required([ROLE_ADMIN])
def create_planning_garde(request, payload: PlanningGardeIn):
    if payload.date_fin <= payload.date_debut:
        return 400, {"error": "La date de fin doit être postérieure au début"}
    try:
        personnel = Personnel.objects.get(id=payload.personnel_id)
    except Personnel.DoesNotExist:
        return 400, {"error": "Personnel introuvable"}
    from hospital_structure.models import ServiceHospitalier
    try:
        service = ServiceHospitalier.objects.get(id=payload.service_id)
    except ServiceHospitalier.DoesNotExist:
        return 400, {"error": "Service introuvable"}

    user = get_authenticated_user(request)
    garde = PlanningGarde.objects.create(
        personnel=personnel,
        service=service,
        type_garde=payload.type_garde,
        date_debut=payload.date_debut,
        date_fin=payload.date_fin,
        commentaire=payload.commentaire,
        planifie_par=user,
    )
    audit_log(request, 'CREATE', garde)
    return 201, {
        "id": garde.id,
        "personnel": personnel.utilisateur.get_full_name() or personnel.matricule,
        "service": service.nom,
        "type_garde": garde.type_garde,
        "date_debut": garde.date_debut.isoformat(),
        "date_fin": garde.date_fin.isoformat(),
        "est_effectuee": garde.est_effectuee,
    }


@router.get("/presences", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def list_presences(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Presence.objects.select_related('personnel__utilisateur').order_by('-date')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            "id": p.id,
            "personnel": p.personnel.utilisateur.get_full_name() or p.personnel.matricule,
            "date": p.date.isoformat(),
            "statut": p.statut,
            "heure_arrivee": p.heure_arrivee.isoformat() if p.heure_arrivee else None,
            "heure_depart": p.heure_depart.isoformat() if p.heure_depart else None,
        }
        for p in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/presences", response={201: PresenceOut, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def create_presence(request, payload: PresenceIn):
    try:
        personnel = Personnel.objects.get(id=payload.personnel_id)
    except Personnel.DoesNotExist:
        return 400, {"error": "Personnel introuvable"}
    user = get_authenticated_user(request)
    presence = Presence.objects.create(
        personnel=personnel,
        date=payload.date,
        statut=payload.statut,
        heure_arrivee=payload.heure_arrivee,
        heure_depart=payload.heure_depart,
        commentaire=payload.commentaire,
        saisi_par=user,
    )
    audit_log(request, 'CREATE', presence)
    return 201, {
        "id": presence.id,
        "personnel": personnel.utilisateur.get_full_name() or personnel.matricule,
        "date": presence.date.isoformat(),
        "statut": presence.statut,
        "heure_arrivee": presence.heure_arrivee.isoformat() if presence.heure_arrivee else None,
        "heure_depart": presence.heure_depart.isoformat() if presence.heure_depart else None,
    }


@router.get("/conges", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def list_conges(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Conge.objects.select_related('personnel__utilisateur').order_by('-date_demande')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            "id": c.id,
            "personnel": c.personnel.utilisateur.get_full_name() or c.personnel.matricule,
            "type_conge": c.type_conge,
            "statut": c.statut,
            "date_debut": c.date_debut.isoformat(),
            "date_fin": c.date_fin.isoformat(),
            "nb_jours": c.nb_jours,
            "motif": c.motif,
        }
        for c in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/conges", response={201: CongeOut, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def create_conge(request, payload: CongeIn):
    try:
        personnel = Personnel.objects.get(id=payload.personnel_id)
    except Personnel.DoesNotExist:
        return 400, {"error": "Personnel introuvable"}
    user = get_authenticated_user(request)
    conge = Conge.objects.create(
        personnel=personnel,
        type_conge=payload.type_conge,
        date_debut=payload.date_debut,
        date_fin=payload.date_fin,
        motif=payload.motif,
        demande_par=user,
    )
    audit_log(request, 'CREATE', conge)
    return 201, {
        "id": conge.id,
        "personnel": personnel.utilisateur.get_full_name() or personnel.matricule,
        "type_conge": conge.type_conge,
        "statut": conge.statut,
        "date_debut": conge.date_debut.isoformat(),
        "date_fin": conge.date_fin.isoformat(),
        "nb_jours": conge.nb_jours,
        "motif": conge.motif,
    }


@router.post("/conges/{conge_id}/valider", response={200: CongeOut, 400: dict, 401: dict, 403: dict, 404: dict})
@role_required([ROLE_ADMIN])
def valider_conge(request, conge_id: int, payload: CongeValidationIn):
    try:
        conge = Conge.objects.select_related('personnel__utilisateur').get(id=conge_id)
    except Conge.DoesNotExist:
        return 404, {"error": "Congé introuvable"}
    if payload.statut not in ('VALIDE', 'REFUSE'):
        return 400, {"error": "Statut invalide"}
    user = get_authenticated_user(request)
    conge.statut = payload.statut
    conge.valide_par = user
    conge.date_validation = timezone.now()
    conge.commentaire_validation = payload.commentaire_validation
    conge.save()
    audit_log(request, 'UPDATE', conge, new_value=payload.statut)
    return 200, {
        "id": conge.id,
        "personnel": conge.personnel.utilisateur.get_full_name() or conge.personnel.matricule,
        "type_conge": conge.type_conge,
        "statut": conge.statut,
        "date_debut": conge.date_debut.isoformat(),
        "date_fin": conge.date_fin.isoformat(),
        "nb_jours": conge.nb_jours,
        "motif": conge.motif,
    }


@router.get("/fiches-paie", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def list_fiches_paie(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = FichePaie.objects.select_related('personnel__utilisateur').order_by('-annee', '-mois')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            "id": f.id,
            "personnel": f.personnel.utilisateur.get_full_name() or f.personnel.matricule,
            "mois": f.mois,
            "annee": f.annee,
            "salaire_base": float(f.salaire_base),
            "primes": float(f.primes),
            "deductions": float(f.deductions),
            "net_a_payer": float(f.net_a_payer),
        }
        for f in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/fiches-paie", response={201: FichePaieOut, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def create_fiche_paie(request, payload: FichePaieIn):
    try:
        personnel = Personnel.objects.get(id=payload.personnel_id)
    except Personnel.DoesNotExist:
        return 400, {"error": "Personnel introuvable"}
    user = get_authenticated_user(request)
    fiche = FichePaie.objects.create(
        personnel=personnel,
        mois=payload.mois,
        annee=payload.annee,
        salaire_base=payload.salaire_base,
        primes=payload.primes,
        deductions=payload.deductions,
        nb_heures_sup=payload.nb_heures_sup,
        montant_heures_sup=payload.montant_heures_sup,
        generee_par=user,
    )
    audit_log(request, 'CREATE', fiche)
    return 201, {
        "id": fiche.id,
        "personnel": personnel.utilisateur.get_full_name() or personnel.matricule,
        "mois": fiche.mois,
        "annee": fiche.annee,
        "salaire_base": float(fiche.salaire_base),
        "primes": float(fiche.primes),
        "deductions": float(fiche.deductions),
        "net_a_payer": float(fiche.net_a_payer),
    }
