"""Endpoints FHIR R4 simplifiés (interopérabilité HL7/FHIR)."""

from ninja import Router, Schema
from typing import List, Optional

from clinical.models import Patient, Consultation
from common.permissions import auth_bearer, role_required, ROLE_CLINICAL, ROLE_ADMIN

router = Router(auth=auth_bearer, tags=["FHIR"])


class FHIRPatientOut(Schema):
    resourceType: str = 'Patient'
    id: str
    identifier: List[dict]
    name: List[dict]
    birthDate: str
    telecom: List[dict]


class FHIRObservationOut(Schema):
    resourceType: str = 'Observation'
    id: str
    status: str
    code: dict
    subject: dict
    effectiveDateTime: str


@router.get("/Patient/{patient_id}", response={200: FHIRPatientOut, 404: dict})
@role_required(ROLE_CLINICAL + [ROLE_ADMIN])
def fhir_patient(request, patient_id: int):
    try:
        p = Patient.objects.get(id=patient_id, est_actif=True)
    except Patient.DoesNotExist:
        return 404, {"error": "Patient non trouvé"}

    return 200, {
        'resourceType': 'Patient',
        'id': str(p.id),
        'identifier': [{'system': 'urn:sghi:dossier', 'value': p.numero_dossier}],
        'name': [{'family': p.nom, 'given': [p.prenom]}],
        'birthDate': p.date_naissance.isoformat(),
        'telecom': [
            {'system': 'phone', 'value': p.telephone},
            {'system': 'email', 'value': p.email or ''},
        ],
    }


@router.get("/Patient", response={200: dict})
@role_required(ROLE_CLINICAL + [ROLE_ADMIN])
def fhir_search_patients(request, identifier: Optional[str] = None, page: int = 1, page_size: int = 20):
    from common.pagination import paginate_queryset, paginated_response
    qs = Patient.objects.filter(est_actif=True).order_by('nom', 'prenom')
    if identifier:
        qs = qs.filter(numero_dossier=identifier)
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=50)
    entries = []
    for p in rows:
        entries.append({
            'fullUrl': f"/api/v1/fhir/Patient/{p.id}",
            'resource': {
                'resourceType': 'Patient',
                'id': str(p.id),
                'identifier': [{'value': p.numero_dossier}],
                'name': [{'family': p.nom, 'given': [p.prenom]}],
            },
        })
    return 200, {
        'resourceType': 'Bundle',
        'type': 'searchset',
        'total': meta['total'],
        'entry': entries,
        'items': entries,
        'pagination': meta,
    }


@router.get("/Observation", response={200: dict})
@role_required(ROLE_CLINICAL + [ROLE_ADMIN])
def fhir_observations(request, patient: int, page: int = 1, page_size: int = 20):
    from common.pagination import paginate_queryset, paginated_response
    qs = Consultation.objects.filter(
        patient_id=patient,
        diagnostic_cim10__gt='',
    ).order_by('-date_consultation')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=50)
    entries = []
    for c in rows:
        entries.append({
            'resource': {
                'resourceType': 'Observation',
                'id': str(c.id),
                'status': 'final',
                'code': {'coding': [{'system': 'urn:icd10', 'code': c.diagnostic_cim10}]},
                'subject': {'reference': f'Patient/{patient}'},
                'effectiveDateTime': c.date_consultation.isoformat(),
            },
        })
    return 200, {
        'resourceType': 'Bundle',
        'type': 'searchset',
        'total': meta['total'],
        'entry': [{'resource': e['resource']} for e in entries],
        'items': entries,
        'pagination': meta,
    }
