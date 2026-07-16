"""Workflow caisse secrétariat — encaissement avant consultation."""

import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from clinical.models import Patient, Admission
from appointments.models import RendezVous
from .models import (
    Facture, LigneFacture, TransactionPaiement, SecretariatInvoice, BillingError,
)
from .services import TARIF_CONSULTATION

MODE_PAIEMENT_MAP = {
    'CASH': 'ESPECES',
    'MOBILE_MONEY': 'MTN',
    'CARD': 'CARTE',
}


def serialiser_secretariat_invoice(invoice):
    patient = invoice.patient
    rdv = invoice.rendez_vous
    admission = invoice.admission
    return {
        'id': invoice.id,
        'patient_id': patient.id,
        'patient_nom': f"{patient.nom} {patient.prenom}",
        'patient_dossier': patient.numero_dossier,
        'amount': float(invoice.amount),
        'status': invoice.status,
        'payment_method': invoice.payment_method or None,
        'libelle': invoice.libelle,
        'created_at': invoice.created_at.isoformat(),
        'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None,
        'admission_id': admission.id if admission else None,
        'rendez_vous_id': rdv.id if rdv else None,
        'medecin': (
            f"Dr {rdv.medecin.get_full_name() or rdv.medecin.username}"
            if rdv else None
        ),
        'rdv_date_heure': rdv.date_heure.isoformat() if rdv else None,
        'service_nom': (
            admission.service.nom if admission
            else (rdv.service.nom if rdv else None)
        ),
        'facture_id': invoice.facture_id,
    }


@transaction.atomic
def creer_invoice_consultation(
    patient_id,
    amount=None,
    admission_id=None,
    rendez_vous_id=None,
    libelle=None,
):
    """Crée une facture secrétariat en attente de paiement."""
    patient = Patient.objects.get(id=patient_id)
    admission = None
    rdv = None

    if admission_id:
        admission = Admission.objects.select_related('service').get(
            id=admission_id, patient=patient,
        )
        existante = SecretariatInvoice.objects.filter(
            admission=admission, status='PENDING',
        ).first()
        if existante:
            return existante

    if rendez_vous_id:
        rdv = RendezVous.objects.select_related('medecin', 'service').get(
            id=rendez_vous_id, patient=patient,
        )
        if rdv.statut == 'ANNULE':
            raise BillingError("Rendez-vous annulé — facture non créée")
        existante = SecretariatInvoice.objects.filter(
            rendez_vous=rdv, status='PENDING',
        ).first()
        if existante:
            return existante
        if SecretariatInvoice.objects.filter(rendez_vous=rdv, status='PAID').exists():
            raise BillingError("Ce rendez-vous est déjà réglé")

    if not admission and not rdv:
        today = timezone.now().date()
        existante = SecretariatInvoice.objects.filter(
            patient=patient,
            admission__isnull=True,
            rendez_vous__isnull=True,
            status='PENDING',
            created_at__date=today,
        ).first()
        if existante:
            return existante

    montant = amount if amount is not None else TARIF_CONSULTATION
    if libelle is None:
        if rdv:
            libelle = f"Consultation — RDV Dr {rdv.medecin.get_full_name() or rdv.medecin.username}"
        elif admission:
            libelle = f"Frais consultation — Admission {admission.service.nom}"
        else:
            libelle = 'Frais de consultation'

    return SecretariatInvoice.objects.create(
        patient=patient,
        admission=admission,
        rendez_vous=rdv,
        amount=montant,
        status='PENDING',
        libelle=libelle,
    )


def verifier_paiement_consultation(patient_id, admission_id=None):
    """Retourne un message d'erreur si le patient n'a pas réglé au secrétariat."""
    today = timezone.now().date()

    if admission_id:
        if SecretariatInvoice.objects.filter(
            admission_id=admission_id, status='PENDING',
        ).exists():
            return (
                "Paiement requis au secrétariat avant consultation. "
                "Le patient doit régler les frais à la caisse."
            )
        if not SecretariatInvoice.objects.filter(
            admission_id=admission_id, status='PAID',
        ).exists():
            return (
                "Aucun encaissement enregistré pour cette admission. "
                "Dirigez le patient vers la caisse du secrétariat."
            )
        return None

    if SecretariatInvoice.objects.filter(
        patient_id=patient_id,
        admission__isnull=True,
        status='PENDING',
        created_at__date=today,
    ).exists():
        return (
            "Paiement requis au secrétariat avant consultation. "
            "Le patient doit régler les frais à la caisse."
        )

    if not SecretariatInvoice.objects.filter(
        patient_id=patient_id,
        status='PAID',
        created_at__date=today,
    ).exists():
        return (
            "Aucun encaissement enregistré aujourd'hui. "
            "Le patient doit passer par la caisse du secrétariat."
        )
    return None


@transaction.atomic
def encaisser_invoice(invoice_id, payment_method, utilisateur_id, numero_telephone=''):
    """Valide l'encaissement et débloque l'accès au médecin."""
    if payment_method not in MODE_PAIEMENT_MAP:
        raise BillingError("Mode de paiement invalide (CASH, MOBILE_MONEY, CARD)")

    invoice = SecretariatInvoice.objects.select_for_update().select_related(
        'patient', 'admission', 'rendez_vous', 'facture',
    ).get(id=invoice_id)

    if invoice.status == 'PAID':
        raise BillingError("Cette facture est déjà payée")

    mode_interne = MODE_PAIEMENT_MAP[payment_method]
    if payment_method == 'MOBILE_MONEY' and not numero_telephone:
        raise BillingError("Numéro de téléphone requis pour Mobile Money")

    facture = invoice.facture
    if not facture:
        facture = Facture.objects.create(
            patient=invoice.patient,
            admission=invoice.admission,
            emise_par_id=utilisateur_id,
            statut='EMISE',
        )
        LigneFacture.objects.create(
            facture=facture,
            type_ligne='CONSULTATION',
            description=invoice.libelle,
            quantite=1,
            prix_unitaire=invoice.amount,
            admission=invoice.admission,
        )
        facture.recalculer_montants()
        invoice.facture = facture
        invoice.save(update_fields=['facture'])

    if facture.statut == 'BROUILLON':
        facture.statut = 'EMISE'
        facture.save(update_fields=['statut'])
        facture.recalculer_montants()

    ref = f"CAISSE-{uuid.uuid4().hex[:12].upper()}"
    if mode_interne in ('MTN', 'AIRTEL'):
        ref = f"{mode_interne}-{ref}"

    transaction_paiement = TransactionPaiement.objects.create(
        facture=facture,
        mode_paiement=mode_interne,
        montant=invoice.amount,
        numero_telephone=numero_telephone,
        operateur=mode_interne if mode_interne in ('MTN', 'AIRTEL') else '',
        statut='SUCCESS',
        effectue_par_id=utilisateur_id,
        transaction_id=ref,
        reference_externe=ref,
        api_response={
            'source': 'secretariat_caisse',
            'payment_method': payment_method,
            'status': 'SUCCESS',
            'reference': ref,
        },
    )
    transaction_paiement.confirmer_paiement()

    invoice.status = 'PAID'
    invoice.payment_method = payment_method
    invoice.paid_at = timezone.now()
    invoice.paid_by_id = utilisateur_id
    invoice.save(update_fields=['status', 'payment_method', 'paid_at', 'paid_by'])

    return invoice, transaction_paiement
