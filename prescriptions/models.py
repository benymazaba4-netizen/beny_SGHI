from django.db import models
from django.utils import timezone
from authentication.models import Utilisateur
from clinical.models import Patient, Consultation


class PrescriptionError(Exception):
    pass


class Medicament(models.Model):
    """Médicament disponible à l'hôpital"""

    FORMES = (
        ('COMPRIME', 'Comprimé'),
        ('INJECTION', 'Injection'),
        ('SIROP', 'Sirop'),
        ('POMMADE', 'Pommade'),
        ('PERFUSION', 'Perfusion'),
        ('GOUTTES', 'Gouttes'),
    )

    code = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    forme = models.CharField(max_length=20, choices=FORMES, default='COMPRIME')
    dosage = models.CharField(max_length=100, blank=True)
    unite = models.CharField(max_length=20, default='mg')

    fabricant = models.CharField(max_length=200, blank=True)
    est_generique = models.BooleanField(default=False)
    est_sur_ordonnance = models.BooleanField(default=True)
    est_remboursable = models.BooleanField(default=True)

    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} - {self.dosage}"


class Prescription(models.Model):
    """Prescription médicale — immuable après validation"""

    STATUT_PRESCRIPTION = (
        ('BROUILLON', 'Brouillon'),
        ('VALIDE', 'Validée'),
        ('ADMINISTREE', 'Administrée'),
        ('PARTIELLE', 'Partiellement administrée'),
        ('ANNULEE', 'Annulée'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    medecin = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='prescriptions_emises')
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='prescriptions')

    statut = models.CharField(max_length=20, choices=STATUT_PRESCRIPTION, default='BROUILLON')
    date_prescription = models.DateTimeField(auto_now_add=True)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

    instructions = models.TextField(blank=True)

    est_verrouillee = models.BooleanField(default=False)

    signature_electronique = models.TextField(blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    validee_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='prescriptions_validees',
    )

    def __str__(self):
        return f"Prescription {self.id} - {self.patient} par {self.medecin.username}"

    def save(self, *args, **kwargs):
        if self.pk:
            ancien = Prescription.objects.filter(pk=self.pk).values(
                'est_verrouillee', 'patient_id', 'medecin_id', 'consultation_id',
                'date_debut', 'instructions',
            ).first()
            if ancien and ancien['est_verrouillee']:
                champs_proteges = (
                    self.patient_id != ancien['patient_id']
                    or self.medecin_id != ancien['medecin_id']
                    or self.consultation_id != ancien['consultation_id']
                    or self.date_debut != ancien['date_debut']
                    or self.instructions != ancien['instructions']
                )
                if champs_proteges:
                    raise PrescriptionError("Prescription verrouillée — modification interdite")
        super().save(*args, **kwargs)

    def generer_signature(self, validateur):
        import hashlib
        lignes = '|'.join(
            f"{l.medicament_id}:{l.quantite_prescitee}"
            for l in self.lignes.all()
        )
        data = f"{self.id}|{validateur.id}|{lignes}|{timezone.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verrouiller(self, validateur):
        """Verrouille la prescription (immuable après validation)."""
        if self.est_verrouillee:
            raise PrescriptionError("Prescription déjà verrouillée")
        if validateur.role not in ('MEDECIN', 'ADMIN'):
            raise PermissionError("Seul un médecin peut valider une prescription")

        self.est_verrouillee = True
        self.statut = 'VALIDE'
        self.date_validation = timezone.now()
        self.validee_par = validateur
        self.signature_electronique = self.generer_signature(validateur)
        self.save()


class LignePrescription(models.Model):
    """Ligne d'une prescription (détail des médicaments)"""

    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='lignes')
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)

    quantite_prescitee = models.IntegerField()
    quantite_administree = models.IntegerField(default=0)

    frequence = models.CharField(max_length=100, help_text="ex: 2x par jour")
    duree_jours = models.IntegerField(default=1)

    instructions_specifiques = models.TextField(blank=True)
    doses_omises = models.IntegerField(default=0)

    def quantite_restante(self):
        return self.quantite_prescitee - self.quantite_administree

    def est_entièrement_administree(self):
        return self.quantite_restante() <= 0

    def save(self, *args, **kwargs):
        if self.pk:
            ancien = LignePrescription.objects.filter(pk=self.pk).values(
                'quantite_prescitee', 'medicament_id', 'frequence', 'duree_jours',
                'prescription__est_verrouillee',
            ).first()
            if ancien and ancien['prescription__est_verrouillee']:
                champs_proteges = (
                    self.quantite_prescitee != ancien['quantite_prescitee']
                    or self.medicament_id != ancien['medicament_id']
                    or self.frequence != ancien['frequence']
                    or self.duree_jours != ancien['duree_jours']
                )
                if champs_proteges:
                    raise PrescriptionError("Prescription verrouillée — modification de la ligne interdite")
        elif self.prescription_id:
            if Prescription.objects.filter(pk=self.prescription_id, est_verrouillee=True).exists():
                raise PrescriptionError("Impossible d'ajouter une ligne à une prescription verrouillée")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.prescription.id} - {self.medicament.nom} x{self.quantite_prescitee}"


class AdministrationMedicament(models.Model):
    """Traçabilité de l'administration des médicaments par l'infirmier"""

    ligne_prescription = models.ForeignKey(LignePrescription, on_delete=models.CASCADE, related_name='administrations')
    infirmier = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='administrations')

    date_administration = models.DateTimeField(auto_now_add=True)
    quantite_administree = models.IntegerField()

    commentaire = models.TextField(blank=True)

    est_refuse = models.BooleanField(default=False)
    reaction_indesirable = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.ligne_prescription.prescription.est_verrouillee:
            raise PrescriptionError("Administration impossible — prescription non validée")
        super().save(*args, **kwargs)
        ligne = self.ligne_prescription
        total_admin = AdministrationMedicament.objects.filter(
            ligne_prescription=ligne, est_refuse=False,
        ).aggregate(total=models.Sum('quantite_administree'))['total'] or 0
        ligne.quantite_administree = total_admin
        ligne.save()

        prescription = ligne.prescription
        toutes_terminees = all(l.est_entièrement_administree() for l in prescription.lignes.all())
        prescription.statut = 'ADMINISTREE' if toutes_terminees else 'PARTIELLE'
        prescription.save(update_fields=['statut'])

    def __str__(self):
        return f"Admin {self.ligne_prescription.medicament.nom} - {self.quantite_administree} par {self.infirmier.username}"


class AlerteDoseOmise(models.Model):
    """Alerte automatique pour dose non administrée"""

    ligne_prescription = models.ForeignKey(
        LignePrescription, on_delete=models.CASCADE, related_name='alertes_doses',
    )
    message = models.TextField()
    date_alerte = models.DateTimeField(auto_now_add=True)
    est_traitee = models.BooleanField(default=False)
    traitee_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alertes_doses_traitees',
    )

    class Meta:
        ordering = ['-date_alerte']

    def __str__(self):
        return f"Dose omise — {self.ligne_prescription}"
