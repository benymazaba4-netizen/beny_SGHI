"""Services gouvernance des données."""

import csv
import hashlib
import io
from datetime import date, timedelta

from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from clinical.models import Patient, Consultation
from .models import ArchiveRecord, AnonymizationJob, JournalAccesDossier


DUREE_CONSERVATION_ANNEES = 20


def journaliser_acces(request, patient_id, action='LECTURE'):
    """Enregistre un accès au dossier patient."""
    from common.audit_utils import get_authenticated_user
    user = get_authenticated_user(request)
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
    if not ip:
        ip = request.META.get('REMOTE_ADDR')
    return JournalAccesDossier.objects.create(
        utilisateur=user,
        patient_id=patient_id,
        action=action,
        ip_address=ip or None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
    )


def archiver_dossier_patient(patient_id, archive_par):
    """Archive un dossier patient selon la politique de rétention."""
    patient = Patient.objects.get(id=patient_id)
    ct = ContentType.objects.get_for_model(Patient)
    expiration = date.today() + timedelta(days=365 * DUREE_CONSERVATION_ANNEES)
    record, _ = ArchiveRecord.objects.update_or_create(
        content_type=ct,
        object_id=patient.id,
        defaults={
            'statut': 'ARCHIVE',
            'date_archivage': timezone.now(),
            'date_expiration_legale': expiration,
            'archive_par': archive_par,
            'notes': f"Archivage dossier {patient.numero_dossier}",
        },
    )
    patient.est_actif = False
    patient.save(update_fields=['est_actif'])
    return record


def lancer_anonymisation(job: AnonymizationJob):
    """Anonymise les consultations pour export statistique."""
    job.statut = 'EN_COURS'
    job.save(update_fields=['statut'])

    try:
        consultations = Consultation.objects.filter(
            date_consultation__date__gte=job.periode_debut,
            date_consultation__date__lte=job.periode_fin,
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['hash_patient', 'date', 'diagnostic_cim10', 'service_id'])

        for c in consultations:
            hash_patient = hashlib.sha256(
                f"patient-{c.patient_id}-salt-sghi".encode()
            ).hexdigest()[:16]
            writer.writerow([
                hash_patient,
                c.date_consultation.date().isoformat(),
                c.diagnostic_cim10,
                c.service_id,
            ])

        job.nb_enregistrements = consultations.count()
        job.statut = 'TERMINE'
        job.date_fin = timezone.now()
        job.resultat_fichier = buffer.getvalue()[:5000]
        job.save()
    except Exception as exc:
        job.statut = 'ERREUR'
        job.erreur = str(exc)
        job.date_fin = timezone.now()
        job.save()
    return job
