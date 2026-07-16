from ninja import Router, Schema
from typing import Optional
from decimal import Decimal

from billing.models import SecretariatInvoice, BillingError
from billing.secretariat_services import (
    serialiser_secretariat_invoice,
    creer_invoice_consultation,
    encaisser_invoice,
)
from common.permissions import (
    auth_bearer, role_required, enforce_patient_scope,
    ROLE_ADMIN, ROLE_SECRETAIRE, ROLE_COMPTABLE, ROLE_PATIENT, ROLE_MEDECIN,
)
from common.audit_utils import audit_log

router = Router(auth=auth_bearer)


class InvoiceCreateIn(Schema):
    patient_id: int
    admission_id: Optional[int] = None
    rendez_vous_id: Optional[int] = None
    amount: Optional[Decimal] = None
    libelle: str = ''


class InvoicePayIn(Schema):
    payment_method: str
    numero_telephone: str = ''


@router.get("/invoices/patient/{patient_id}", response={200: dict, 403: dict, 401: dict})
@role_required([ROLE_PATIENT, ROLE_SECRETAIRE, ROLE_ADMIN, ROLE_MEDECIN])
def list_patient_invoices(request, patient_id: int, status: Optional[str] = None, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response

    denied = enforce_patient_scope(request, patient_id)
    if denied:
        return denied

    qs = SecretariatInvoice.objects.filter(patient_id=patient_id).select_related(
        'patient', 'admission__service', 'rendez_vous__medecin', 'rendez_vous__service',
    ).order_by('-created_at')

    if status:
        qs = qs.filter(status=status.upper())

    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [serialiser_secretariat_invoice(inv) for inv in rows]
    pending_count = SecretariatInvoice.objects.filter(
        patient_id=patient_id, status='PENDING',
    ).count()
    return 200, {
        **paginated_response(items, meta),
        'pending_count': pending_count,
        'payment_required': pending_count > 0,
    }


@router.get("/invoices", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_SECRETAIRE, ROLE_ADMIN, ROLE_COMPTABLE])
def list_invoices(request, status: Optional[str] = None, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response

    qs = SecretariatInvoice.objects.select_related(
        'patient', 'admission__service', 'rendez_vous__medecin', 'rendez_vous__service',
    ).order_by('-created_at')

    if status:
        qs = qs.filter(status=status.upper())

    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [serialiser_secretariat_invoice(inv) for inv in rows]
    pending_count = SecretariatInvoice.objects.filter(status='PENDING').count()
    return 200, {
        **paginated_response(items, meta),
        'pending_count': pending_count,
    }


@router.post("/invoices", response={201: dict, 400: dict, 403: dict})
@role_required([ROLE_SECRETAIRE, ROLE_ADMIN])
def create_invoice(request, payload: InvoiceCreateIn):
    try:
        invoice = creer_invoice_consultation(
            patient_id=payload.patient_id,
            amount=payload.amount,
            admission_id=payload.admission_id,
            rendez_vous_id=payload.rendez_vous_id,
            libelle=payload.libelle or None,
        )
        audit_log(request, 'CREATE', invoice, new_value='Facture caisse secrétariat')
        return 201, {
            'message': 'Facture créée — en attente de règlement',
            'invoice': serialiser_secretariat_invoice(invoice),
        }
    except BillingError as e:
        return 400, {'error': str(e)}
    except Exception as e:
        return 400, {'error': str(e)}


@router.post("/invoices/{invoice_id}/pay", response={200: dict, 400: dict, 404: dict, 403: dict})
@role_required([ROLE_SECRETAIRE, ROLE_ADMIN])
def pay_invoice(request, invoice_id: int, payload: InvoicePayIn):
    try:
        user_id = request.auth_payload['id']
        invoice, transaction = encaisser_invoice(
            invoice_id=invoice_id,
            payment_method=payload.payment_method.upper(),
            utilisateur_id=user_id,
            numero_telephone=payload.numero_telephone,
        )
        audit_log(
            request, 'UPDATE', invoice,
            new_value=f"Encaissement {payload.payment_method} — {invoice.amount} FCFA",
        )
        return 200, {
            'message': 'Paiement enregistré — patient débloqué pour la consultation',
            'invoice': serialiser_secretariat_invoice(invoice),
            'transaction_id': transaction.id,
            'reference': transaction.reference_externe,
        }
    except SecretariatInvoice.DoesNotExist:
        return 404, {'error': 'Facture introuvable'}
    except BillingError as e:
        return 400, {'error': str(e)}
    except Exception as e:
        return 400, {'error': str(e)}
