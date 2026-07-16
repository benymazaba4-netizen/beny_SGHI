"""Audit trail automatique sur tables critiques (INSERT/UPDATE/DELETE)."""
import json

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from common.request_context import get_current_request
from .models import AuditLog

AUDITED_LABELS = {
    'clinical.Patient',
    'clinical.Admission',
    'clinical.Consultation',
    'billing.Facture',
    'billing.LigneFacture',
    'prescriptions.Prescription',
    'prescriptions.LignePrescription',
    'laboratory.DemandeExamen',
    'laboratory.ResultatExamen',
    'pharmacy.MouvementStock',
    'rh.Personnel',
    'governance.JournalAccesDossier',
    'authentication.Utilisateur',
}

_pre_save_cache: dict[str, dict] = {}


def _model_label(instance) -> str:
    return f"{instance._meta.app_label}.{instance.__class__.__name__}"


def _serialize(instance) -> dict:
    data = {}
    for field in instance._meta.fields:
        try:
            value = getattr(instance, field.attname)
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            elif hasattr(value, 'pk'):
                value = value.pk
            data[field.name] = value
        except Exception:
            data[field.name] = None
    return data


def _write_audit(instance, action: str, old_value: dict | None, new_value: dict | None):
    if _model_label(instance) not in AUDITED_LABELS:
        return
    request = get_current_request()
    user = None
    if request and getattr(request, 'auth_payload', None):
        from authentication.models import Utilisateur
        try:
            user = Utilisateur.objects.get(id=request.auth_payload['id'])
        except Utilisateur.DoesNotExist:
            pass
    AuditLog.log_action(
        utilisateur=user,
        action=action,
        instance=instance,
        old_value=json.dumps(old_value, default=str, ensure_ascii=False) if old_value else '',
        new_value=json.dumps(new_value, default=str, ensure_ascii=False) if new_value else '',
        request=request,
    )


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    label = f"{sender._meta.app_label}.{sender.__name__}"
    if label not in AUDITED_LABELS or not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
        _pre_save_cache[f"{label}:{instance.pk}"] = _serialize(old)
    except sender.DoesNotExist:
        pass


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    label = f"{sender._meta.app_label}.{sender.__name__}"
    if label not in AUDITED_LABELS:
        return
    key = f"{label}:{instance.pk}"
    if created:
        _write_audit(instance, 'CREATE', None, _serialize(instance))
    else:
        old = _pre_save_cache.pop(key, None)
        new = _serialize(instance)
        if old != new:
            _write_audit(instance, 'UPDATE', old, new)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    label = f"{sender._meta.app_label}.{sender.__name__}"
    if label not in AUDITED_LABELS:
        return
    _write_audit(instance, 'DELETE', _serialize(instance), None)
