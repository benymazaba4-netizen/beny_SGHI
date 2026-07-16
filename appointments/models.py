from django.db import models
from django.utils import timezone
from authentication.models import Utilisateur
from clinical.models import Patient
from hospital_structure.models import ServiceHospitalier


class DisponibiliteMedecin(models.Model):
    """Créneaux de disponibilité pour prise de rendez-vous."""

    medecin = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='disponibilites',
    )
    service = models.ForeignKey(
        ServiceHospitalier, on_delete=models.CASCADE, related_name='disponibilites_medecins',
    )
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    duree_creneau_minutes = models.PositiveIntegerField(default=30)
    est_actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['date_debut']
        indexes = [models.Index(fields=['medecin', 'date_debut'])]

    def __str__(self):
        return f"{self.medecin.username} — {self.date_debut}"


class RendezVous(models.Model):
    """Rendez-vous patient — médecin."""

    STATUTS = (
        ('PLANIFIE', 'Planifié'),
        ('CONFIRME', 'Confirmé'),
        ('ANNULE', 'Annulé'),
        ('TERMINE', 'Terminé'),
        ('ABSENT', 'Absent'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='rendez_vous')
    medecin = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='rendez_vous_medecin',
    )
    service = models.ForeignKey(ServiceHospitalier, on_delete=models.CASCADE)
    disponibilite = models.ForeignKey(
        DisponibiliteMedecin, on_delete=models.SET_NULL, null=True, blank=True,
    )

    date_heure = models.DateTimeField()
    duree_minutes = models.PositiveIntegerField(default=30)
    motif = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUTS, default='PLANIFIE')
    notes = models.TextField(blank=True)

    confirmation_email_envoyee = models.BooleanField(default=False)
    rappel_envoye = models.BooleanField(default=False)

    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name='rdv_crees',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date_heure']
        indexes = [
            models.Index(fields=['patient', 'date_heure']),
            models.Index(fields=['medecin', 'date_heure']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"RDV {self.patient} — {self.date_heure}"

    def peut_etre_annule(self):
        return self.statut in ('PLANIFIE', 'CONFIRME') and self.date_heure > timezone.now()
