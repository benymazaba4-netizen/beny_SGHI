"""Services rendez-vous SGHI."""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from .models import RendezVous, DisponibiliteMedecin
from common.email_utils import notify_rdv_confirmation


def creneaux_disponibles(medecin_id, service_id, date_debut, date_fin):
    """Retourne les créneaux libres pour un médecin sur une période."""
    dispos = DisponibiliteMedecin.objects.filter(
        medecin_id=medecin_id,
        service_id=service_id,
        est_actif=True,
        date_debut__gte=date_debut,
        date_fin__lte=date_fin,
    )
    rdv_pris = RendezVous.objects.filter(
        medecin_id=medecin_id,
        statut__in=['PLANIFIE', 'CONFIRME'],
        date_heure__gte=date_debut,
        date_heure__lte=date_fin,
    ).values_list('date_heure', 'duree_minutes')

    pris_set = set()
    for dt, duree in rdv_pris:
        pris_set.add(dt)
        for i in range(1, (duree // 30) + 1):
            pris_set.add(dt + timedelta(minutes=30 * i))

    creneaux = []
    for dispo in dispos:
        current = dispo.date_debut
        delta = timedelta(minutes=dispo.duree_creneau_minutes)
        while current + delta <= dispo.date_fin:
            if current not in pris_set and current > timezone.now():
                creneaux.append({
                    'debut': current.isoformat(),
                    'fin': (current + delta).isoformat(),
                    'disponibilite_id': dispo.id,
                })
            current += delta
    return creneaux


def confirmer_rendez_vous(rdv: RendezVous):
    """Confirme un RDV et envoie l'email de confirmation."""
    rdv.statut = 'CONFIRME'
    rdv.save(update_fields=['statut', 'date_modification'])

    if not rdv.confirmation_email_envoyee:
        if notify_rdv_confirmation(rdv):
            rdv.confirmation_email_envoyee = True
            rdv.save(update_fields=['confirmation_email_envoyee'])

    from notifications.services import creer_notification
    if rdv.patient.utilisateur:
        creer_notification(
            rdv.patient.utilisateur,
            'RDV',
            'Rendez-vous confirmé',
            f"RDV confirmé le {rdv.date_heure.strftime('%d/%m/%Y %H:%M')}",
            push=True,
        )
    return rdv


def serialiser_rdv(rdv):
    return {
        'id': rdv.id,
        'patient_id': rdv.patient_id,
        'patient': f"{rdv.patient.nom} {rdv.patient.prenom}",
        'medecin_id': rdv.medecin_id,
        'medecin': rdv.medecin.get_full_name() or rdv.medecin.username,
        'service_id': rdv.service_id,
        'service': rdv.service.nom,
        'date_heure': rdv.date_heure.isoformat(),
        'duree_minutes': rdv.duree_minutes,
        'motif': rdv.motif,
        'statut': rdv.statut,
        'notes': rdv.notes,
    }
