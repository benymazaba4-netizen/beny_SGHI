"""Notifications email SGHI (SMTP configurable via .env)."""
import logging
import uuid

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.utils import timezone

from .email_templates import render_email_html

logger = logging.getLogger(__name__)


def get_patient_email(patient) -> str:
    """Retourne l'e-mail du patient (fiche ou compte utilisateur)."""
    if patient.email:
        return patient.email
    utilisateur = getattr(patient, 'utilisateur', None)
    if utilisateur and utilisateur.email:
        return utilisateur.email
    return ''


def send_notification(
    to_email: str,
    subject: str,
    message: str,
    *,
    html_message: str | None = None,
    email_type: str = 'OTHER',
    utilisateur = None,
    ip_origin: str | None = None,
) -> bool:
    """
    Envoie une notification par email et enregistre dans EmailLog.
    
    Args:
        to_email: Adresse destinataire
        subject: Sujet de l'email
        message: Contenu texte brut
        html_message: Contenu HTML optionnel
        email_type: Type d'email pour classification (OTP_LOGIN, RDV_CONFIRMATION, etc.)
        utilisateur: Utilisateur Django associé (ForeignKey)
        ip_origin: Adresse IP d'origine pour audit
    """
    if not to_email:
        return False

    # Imports circulaires évités
    from common.models import EmailLog

    full_subject = f"[SGHI] {subject}"
    msg_uuid = str(uuid.uuid4())
    
    # Créer log d'email AVANT envoi
    email_log = EmailLog.objects.create(
        destinataire=to_email,
        sujet=subject,
        type_email=email_type,
        contenu_plain=message,
        contenu_html=html_message or '',
        utilisateur=utilisateur,
        uuid_message=msg_uuid,
        ip_origine=ip_origin,
        statut='EN_ATTENTE',
    )

    try:
        if html_message:
            msg = EmailMultiAlternatives(
                full_subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
                reply_to=[settings.EMAIL_HOST_USER] if settings.EMAIL_HOST_USER else None,
            )
            msg.attach_alternative(html_message, 'text/html')
            msg.send(fail_silently=False)
        else:
            send_mail(
                full_subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
                fail_silently=False,
            )
        
        email_log.marquer_envoye()
        logger.info("Email envoye avec succes — %s → %s (uuid: %s)", email_type, to_email, msg_uuid)
        return True
        
    except Exception as exc:
        email_log.marquer_echec(str(exc))
        logger.error("Echec envoi email — %s → %s : %s (uuid: %s)", email_type, to_email, exc, msg_uuid)
        return False


def notify_patient_registration(user, patient):
    if not user.email:
        return
    plain = (
        f"Bonjour {user.first_name},\n\n"
        f"Votre compte patient a été créé.\n"
        f"Numéro de dossier : {patient.numero_dossier}\n\n"
        f"Connectez-vous sur l'application pour consulter vos résultats.\n\n— SGHI"
    )
    html = render_email_html(
        "Bienvenue sur SGHI Patient",
        [
            f"Bonjour {user.first_name},",
            "Votre compte patient a été créé avec succès.",
            "Connectez-vous à l'application pour consulter vos résultats et prendre rendez-vous.",
        ],
        details=[('Dossier', patient.numero_dossier), ('Identifiant', user.username)],
    )
    send_notification(
        user.email,
        "Bienvenue sur SGHI",
        plain,
        html_message=html,
        email_type='PATIENT_REGISTRATION',
        utilisateur=user,
    )


def notify_rdv_confirmation(rdv) -> bool:
    from django.utils import timezone as tz

    email = get_patient_email(rdv.patient)
    if not email:
        return False

    local_dt = tz.localtime(rdv.date_heure)
    medecin = rdv.medecin.get_full_name() or rdv.medecin.username
    prenom = rdv.patient.prenom or 'Patient'
    date_str = local_dt.strftime('%d/%m/%Y à %H:%M')

    plain = (
        f"Bonjour {prenom},\n\n"
        f"Votre rendez-vous avec Dr {medecin} est confirmé pour le {date_str}.\n"
        f"Motif : {rdv.motif}\n\n— SGHI"
    )
    html = render_email_html(
        "Rendez-vous confirmé",
        [f"Bonjour {prenom},", "Votre rendez-vous est confirmé. Merci de vous présenter 15 minutes avant l'heure prévue."],
        details=[
            ('Date', date_str),
            ('Médecin', f"Dr {medecin}"),
            ('Service', rdv.service.nom),
            ('Motif', rdv.motif),
        ],
    )
    return send_notification(
        email,
        f"Confirmation RDV — {local_dt.strftime('%d/%m/%Y %H:%M')}",
        plain,
        html_message=html,
        email_type='RDV_CONFIRMATION',
        utilisateur=rdv.patient.utilisateur if hasattr(rdv.patient, 'utilisateur') else None,
    )


def notify_exam_published(patient, examen_nom: str):
    prenom = patient.prenom or 'Patient'
    plain = (
        f"Bonjour {prenom},\n\n"
        f"Votre résultat d'examen « {examen_nom} » est disponible "
        f"dans votre espace patient.\n\n— SGHI"
    )
    html = render_email_html(
        "Résultat de laboratoire disponible",
        [f"Bonjour {prenom},", f"Votre résultat d'examen « {examen_nom} » est maintenant accessible dans votre espace patient."],
        details=[('Examen', examen_nom)],
    )
    send_notification(
        get_patient_email(patient),
        "Résultat de laboratoire disponible",
        plain,
        html_message=html,
        email_type='EXAM_PUBLISHED',
        utilisateur=patient.utilisateur if hasattr(patient, 'utilisateur') else None,
    )


def notify_rdv_reminder(rdv) -> bool:
    """E-mail de rappel 24 h avant un rendez-vous confirmé."""
    from django.utils import timezone as tz

    email = get_patient_email(rdv.patient)
    if not email:
        return False

    local_dt = tz.localtime(rdv.date_heure)
    medecin = rdv.medecin.get_full_name() or rdv.medecin.username
    prenom = rdv.patient.prenom or 'Patient'
    date_str = local_dt.strftime('%d/%m/%Y à %H:%M')

    plain = (
        f"Bonjour {prenom},\n\n"
        f"Rappel : rendez-vous demain à {local_dt.strftime('%H:%M')} avec Dr {medecin}.\n"
        f"Service : {rdv.service.nom}\nMotif : {rdv.motif}\n\n— SGHI"
    )
    html = render_email_html(
        "Rappel — rendez-vous demain",
        [f"Bonjour {prenom},", "Ceci est un rappel pour votre rendez-vous de demain."],
        details=[
            ('Date', date_str),
            ('Médecin', f"Dr {medecin}"),
            ('Service', rdv.service.nom),
            ('Motif', rdv.motif),
        ],
    )
    return send_notification(
        email,
        f"Rappel RDV demain — {local_dt.strftime('%d/%m/%Y %H:%M')}",
        plain,
        html_message=html,
        email_type='RDV_REMINDER',
        utilisateur=rdv.patient.utilisateur if hasattr(rdv.patient, 'utilisateur') else None,
    )


def notify_prescription_validated(prescription) -> bool:
    """E-mail de validation de prescription au patient."""
    from django.utils import timezone as tz
    
    patient = prescription.patient if hasattr(prescription, 'patient') else None
    if not patient or not hasattr(patient, 'utilisateur'):
        return False
    
    email = get_patient_email(patient)
    if not email:
        return False
    
    medecin = prescription.medecin.get_full_name() or prescription.medecin.username
    prenom = patient.prenom or 'Patient'
    date_str = tz.localtime(prescription.date_prescription).strftime('%d/%m/%Y')
    
    plain = (
        f"Bonjour {prenom},\n\n"
        f"Votre prescription a été validée par le Dr {medecin}.\n"
        f"Date : {date_str}\n"
        f"Vous pouvez la consulter et retirer vos médicaments à la pharmacie.\n\n— SGHI"
    )
    html = render_email_html(
        "Prescription validée",
        [
            f"Bonjour {prenom},",
            f"Votre prescription du Dr {medecin} a été validée.",
            "Vous pouvez vous présenter à la pharmacie pour retirer vos médicaments.",
        ],
        details=[('Médecin', f"Dr {medecin}"), ('Date', date_str)],
    )
    return send_notification(
        email,
        "Votre prescription est validée",
        plain,
        html_message=html,
        email_type='PRESCRIPTION_VALIDATED',
        utilisateur=patient.utilisateur,
    )


def notify_discharge(admission) -> bool:
    """E-mail de notification de sortie hospitalière."""
    from django.utils import timezone as tz
    
    patient = admission.patient
    if not hasattr(patient, 'utilisateur'):
        return False
    
    email = get_patient_email(patient)
    if not email:
        return False
    
    prenom = patient.prenom or 'Patient'
    date_entree = tz.localtime(admission.date_admission).strftime('%d/%m/%Y')
    date_sortie = tz.localtime(admission.date_sortie).strftime('%d/%m/%Y') if admission.date_sortie else 'N/A'
    
    plain = (
        f"Bonjour {prenom},\n\n"
        f"Votre hospitalisation a pris fin.\n"
        f"Date d'entrée : {date_entree}\n"
        f"Date de sortie : {date_sortie}\n"
        f"Consultez votre dossier pour les recommandations post-hospitalisation.\n\n— SGHI"
    )
    html = render_email_html(
        "Fin d'hospitalisation",
        [
            f"Bonjour {prenom},",
            "Votre séjour hospitalier a pris fin.",
            "Consultez votre dossier médical pour les recommandations post-hospitalisation et les médicaments à poursuivre.",
        ],
        details=[
            ('Date d\'entrée', date_entree),
            ('Date de sortie', date_sortie),
            ('Service', admission.lit.chambre.service.nom if admission.lit else 'N/A'),
        ],
    )
    return send_notification(
        email,
        "Fin de votre hospitalisation",
        plain,
        html_message=html,
        email_type='DISCHARGE_NOTIFICATION',
        utilisateur=patient.utilisateur,
    )


def notify_invoice_created(facture) -> bool:
    """E-mail de création de facture au patient."""
    from django.utils import timezone as tz
    
    patient = facture.patient if hasattr(facture, 'patient') else facture.admission.patient if hasattr(facture, 'admission') else None
    if not patient or not hasattr(patient, 'utilisateur'):
        return False
    
    email = get_patient_email(patient)
    if not email:
        return False
    
    prenom = patient.prenom or 'Patient'
    date_emission = tz.localtime(facture.date_emission).strftime('%d/%m/%Y') if hasattr(facture, 'date_emission') else 'N/A'
    montant = f"{facture.montant_total:,.2f}" if hasattr(facture, 'montant_total') else 'N/A'
    
    plain = (
        f"Bonjour {prenom},\n\n"
        f"Votre facture a été créée et est disponible.\n"
        f"Numéro : {facture.numero}\n"
        f"Montant : {montant} FC\n"
        f"Consultez votre espace patient pour plus de détails.\n\n— SGHI"
    )
    html = render_email_html(
        "Facture créée",
        [
            f"Bonjour {prenom},",
            "Votre facture est maintenant disponible dans votre espace patient.",
            f"Vous pouvez la télécharger ou imprimer.",
        ],
        details=[
            ('Numéro', facture.numero),
            ('Date', date_emission),
            ('Montant', f"{montant} FC"),
        ],
    )
    return send_notification(
        email,
        f"Facture créée — {facture.numero}",
        plain,
        html_message=html,
        email_type='INVOICE_CREATED',
        utilisateur=patient.utilisateur,
    )


def notify_medication_reminder(prescription) -> bool:
    """E-mail de rappel de prise de médicament."""
    from django.utils import timezone as tz
    
    patient = prescription.patient if hasattr(prescription, 'patient') else None
    if not patient or not hasattr(patient, 'utilisateur'):
        return False
    
    email = get_patient_email(patient)
    if not email:
        return False
    
    prenom = patient.prenom or 'Patient'
    medecin = prescription.medecin.get_full_name() or prescription.medecin.username
    
    # Construire liste des médicaments (adaptation selon votre structure)
    medications_text = "vos médicaments prescrits"
    if hasattr(prescription, 'medicaments') and prescription.medicaments:
        meds_list = ", ".join([m.nom for m in prescription.medicaments.all()])
        medications_text = meds_list
    
    plain = (
        f"Bonjour {prenom},\n\n"
        f"Rappel : N'oubliez pas de prendre {medications_text}.\n"
        f"Prescription du Dr {medecin}.\n"
        f"Respectez les horaires et dosages prescrits.\n\n— SGHI"
    )
    html = render_email_html(
        "Rappel de médicament",
        [
            f"Bonjour {prenom},",
            f"Ceci est un rappel pour prendre vos médicaments prescrits par le Dr {medecin}.",
            "Veuillez respecter les horaires et dosages indiqués.",
        ],
        details=[('Médecin', f"Dr {medecin}"), ('Médicaments', medications_text)],
    )
    return send_notification(
        email,
        "Rappel — Prise de médicament",
        plain,
        html_message=html,
        email_type='MEDICATION_REMINDER',
        utilisateur=patient.utilisateur,
    )
