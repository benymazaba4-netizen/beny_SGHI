"""Services notifications push et in-app."""

import json
import logging
import urllib.request
import urllib.error

from django.conf import settings

from .models import Notification, DeviceToken

logger = logging.getLogger(__name__)


def creer_notification(utilisateur, type_notif, titre, corps, lien='', push=False):
    """Crée une notification in-app et optionnellement envoie un push FCM."""
    notif = Notification.objects.create(
        utilisateur=utilisateur,
        type_notification=type_notif,
        titre=titre,
        corps=corps,
        lien=lien,
    )
    if push:
        envoyer_push(utilisateur, titre, corps, lien)
        notif.push_envoyee = True
        notif.save(update_fields=['push_envoyee'])
    return notif


def envoyer_push(utilisateur, titre, corps, lien=''):
    """Envoie une notification push via FCM (si FCM_SERVER_KEY configuré)."""
    server_key = getattr(settings, 'FCM_SERVER_KEY', '') or ''
    if not server_key:
        logger.info("FCM non configuré — push simulé pour %s", utilisateur.username)
        return False

    tokens = DeviceToken.objects.filter(utilisateur=utilisateur, est_actif=True)
    if not tokens.exists():
        return False

    payload = {
        'notification': {'title': titre, 'body': corps},
        'data': {'lien': lien},
    }
    headers = {
        'Authorization': f'key={server_key}',
        'Content-Type': 'application/json',
    }

    for device in tokens:
        body = json.dumps({**payload, 'to': device.token}).encode('utf-8')
        req = urllib.request.Request(
            'https://fcm.googleapis.com/fcm/send',
            data=body,
            headers=headers,
            method='POST',
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except urllib.error.URLError as exc:
            logger.warning("Push FCM échoué pour %s: %s", device.token[:20], exc)
    return True


def envoyer_rappels_rdv():
    """
    Tâche planifiable : rappels RDV (notification in-app + push + e-mail).
    Cible les RDV confirmés dans la fenêtre [now + RDV_REMINDER_HOURS ± RDV_REMINDER_WINDOW_HOURS].
    """
    from datetime import timedelta

    from django.utils import timezone

    from appointments.models import RendezVous
    from common.email_utils import notify_rdv_reminder

    heures = getattr(settings, 'RDV_REMINDER_HOURS', 24)
    fenetre_h = getattr(settings, 'RDV_REMINDER_WINDOW_HOURS', 1)

    cible = timezone.now() + timedelta(hours=heures)
    fenetre = timedelta(hours=fenetre_h)

    rdvs = RendezVous.objects.filter(
        statut='CONFIRME',
        rappel_envoye=False,
        date_heure__gte=cible - fenetre,
        date_heure__lte=cible + fenetre,
    ).select_related('patient__utilisateur', 'medecin', 'service')

    stats = {'traites': 0, 'notifications': 0, 'emails': 0, 'sans_email': 0}

    for rdv in rdvs:
        stats['traites'] += 1
        local_dt = timezone.localtime(rdv.date_heure)
        medecin = rdv.medecin.get_full_name() or rdv.medecin.username
        corps = (
            f"RDV demain à {local_dt.strftime('%H:%M')} avec Dr {medecin} "
            f"({rdv.service.nom})"
        )

        if rdv.patient.utilisateur:
            creer_notification(
                rdv.patient.utilisateur,
                'RDV',
                'Rappel rendez-vous demain',
                corps,
                push=True,
            )
            stats['notifications'] += 1

        if notify_rdv_reminder(rdv):
            stats['emails'] += 1
        else:
            stats['sans_email'] += 1
            logger.info("Rappel RDV #%s sans adresse e-mail", rdv.id)

        rdv.rappel_envoye = True
        rdv.save(update_fields=['rappel_envoye'])

    return stats


def envoyer_rappels_medicaments():
    """
    Tâche planifiable : rappels médicamenteux pour prescriptions actives verrouillées.
    Une notification par ligne/jour maximum (idempotent).
    """
    from django.utils import timezone

    from prescriptions.models import Prescription

    today = timezone.now().date()
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    prescriptions = Prescription.objects.filter(
        est_verrouillee=True,
        statut__in=['VALIDE', 'PARTIELLE'],
        date_fin__gte=today,
    ).select_related('patient__utilisateur').prefetch_related('lignes__medicament')

    stats = {'traites': 0, 'notifications': 0, 'ignorees': 0}

    for presc in prescriptions:
        user = presc.patient.utilisateur
        if not user:
            continue
        for ligne in presc.lignes.all():
            if ligne.quantite_restante() <= 0:
                continue
            stats['traites'] += 1
            titre = f'Rappel médicament — {ligne.medicament.nom}'
            deja_envoye = Notification.objects.filter(
                utilisateur=user,
                type_notification='MEDICAMENT',
                titre=titre,
                date_creation__gte=today_start,
            ).exists()
            if deja_envoye:
                stats['ignorees'] += 1
                continue
            corps = (
                f"Pensez à prendre {ligne.medicament.nom} "
                f"({ligne.frequence}, {ligne.quantite_restante()} dose(s) restante(s))."
            )
            creer_notification(user, 'MEDICAMENT', titre, corps, push=True)
            stats['notifications'] += 1

    return stats
