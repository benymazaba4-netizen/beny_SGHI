from django.db import models, transaction
from django.utils import timezone
from authentication.models import Utilisateur


class Patient(models.Model):
    """Patient du CHU"""

    CIVILITE = (
        ('M', 'Monsieur'),
        ('MME', 'Madame'),
        ('MLLE', 'Mademoiselle'),
    )

    civilite = models.CharField(max_length=4, choices=CIVILITE, default='M')
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100, blank=True)

    numero_identite_national = models.CharField(max_length=255, unique=True, null=True, blank=True)
    numero_securite_sociale = models.CharField(max_length=255, blank=True)
    numero_dossier = models.CharField(max_length=50, unique=True, editable=False)

    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    adresse = models.TextField()
    personne_a_prevenir = models.CharField(max_length=200, blank=True)
    telephone_urgence = models.CharField(max_length=20, blank=True)

    mutuelle = models.CharField(max_length=100, blank=True)
    numero_affiliation = models.CharField(max_length=50, blank=True)

    consentement_donnees = models.BooleanField(default=False)
    consentement_recherche = models.BooleanField(default=False)

    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient'
    )

    # Images
    photo = models.CharField(max_length=500, blank=True, null=True)  # Chemin stockage
    photo_hash = models.CharField(max_length=64, blank=True, null=True)  # SHA256 hash

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    est_actif = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        from common.encryption import encrypt_value, is_encrypted_field
        if self.numero_identite_national and not is_encrypted_field(self.numero_identite_national):
            self.numero_identite_national = encrypt_value(self.numero_identite_national)
        if self.numero_securite_sociale and not is_encrypted_field(self.numero_securite_sociale):
            self.numero_securite_sociale = encrypt_value(self.numero_securite_sociale)
        if not self.numero_dossier:
            import datetime
            annee = datetime.datetime.now().year
            dernier = Patient.objects.filter(numero_dossier__startswith=f"DOS{annee}").count()
            self.numero_dossier = f"DOS{annee}{str(dernier+1).zfill(6)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_dossier} - {self.nom} {self.prenom}"

    def admission_active(self):
        return self.admissions.filter(statut='EN_COURS').first()


class Admission(models.Model):
    """Admission d'un patient dans un service"""

    TYPES_ADMISSION = (
        ('PROGRAMMEE', 'Programmée'),
        ('URGENCE', 'Urgence'),
        ('TRANSFERT', 'Transfert'),
    )

    STATUT_ADMISSION = (
        ('EN_COURS', 'En cours'),
        ('SORTI', 'Sorti'),
        ('TRANSFERE', 'Transféré'),
        ('DECEDE', 'Décédé'),
    )

    STATUTS_ACTIFS = ('EN_COURS',)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='admissions')
    service = models.ForeignKey('hospital_structure.ServiceHospitalier', on_delete=models.CASCADE)
    lit = models.ForeignKey('hospital_structure.Lit', on_delete=models.SET_NULL, null=True)
    medecin_referent = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='admissions_suivies')

    type_admission = models.CharField(max_length=20, choices=TYPES_ADMISSION, default='PROGRAMMEE')
    statut = models.CharField(max_length=20, choices=STATUT_ADMISSION, default='EN_COURS')

    date_entree = models.DateTimeField(auto_now_add=True)
    date_sortie = models.DateTimeField(null=True, blank=True)
    date_previsionnelle_sortie = models.DateField(null=True, blank=True)

    motif_hospitalisation = models.TextField()
    notes = models.TextField(blank=True)

    version = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['patient'],
                condition=models.Q(statut='EN_COURS'),
                name='unique_admission_active_par_patient',
            ),
            models.UniqueConstraint(
                fields=['lit'],
                condition=models.Q(statut='EN_COURS'),
                name='unique_admission_active_par_lit',
            ),
        ]

    def __str__(self):
        return f"{self.patient} - {self.service} ({self.date_entree.date()})"

    @property
    def est_active(self):
        return self.statut == 'EN_COURS'

    def _verifier_version(self, version_attendue):
        if version_attendue is not None and self.version != version_attendue:
            raise ValueError(
                f"Conflit de version (attendu {version_attendue}, actuel {self.version}). "
                "Rechargez le dossier et réessayez."
            )

    def _liberer_lit(self):
        if not self.lit_id:
            return
        from hospital_structure.models import Lit
        lit = Lit.objects.select_for_update().get(pk=self.lit_id)
        lit.liberer_atomique()
        self.lit = None

    def sortir(self, statut='SORTI', notes='', version=None):
        """Clôture l'hospitalisation et libère le lit."""
        if not self.est_active:
            raise ValueError("Cette admission n'est plus active")
        if statut not in ('SORTI', 'DECEDE'):
            raise ValueError("Statut de sortie invalide")

        self._verifier_version(version)
        self._liberer_lit()
        self.statut = statut
        self.date_sortie = timezone.now()
        if notes:
            self.notes = f"{self.notes}\n[Sortie] {notes}".strip()
        self.version += 1
        self.save()
        return self

    def transferer(self, nouveau_service, nouveau_lit, motif='', version=None):
        """Transfert inter-services avec réaffectation de lit."""
        if not self.est_active:
            raise ValueError("Cette admission n'est plus active")
        if not nouveau_lit.est_libre():
            raise ValueError(f"Le lit {nouveau_lit.numero} n'est pas disponible")
        if not nouveau_lit.chambre.est_actif:
            raise ValueError("La chambre de destination est inactive")

        self._verifier_version(version)
        ancien_service = str(self.service)
        self._liberer_lit()

        nouveau_lit.occuper_atomique(self.patient)
        self.service = nouveau_service
        self.lit = nouveau_lit
        self.type_admission = 'TRANSFERT'
        if motif:
            self.notes = f"{self.notes}\n[Transfert {ancien_service} → {nouveau_service}] {motif}".strip()
        self.version += 1
        self.save()
        return self


class Consultation(models.Model):
    """Consultation médicale"""

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    medecin = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='consultations_realisees')
    service = models.ForeignKey('hospital_structure.ServiceHospitalier', on_delete=models.CASCADE)
    admission = models.ForeignKey(Admission, on_delete=models.SET_NULL, null=True, blank=True)

    date_consultation = models.DateTimeField(auto_now_add=True)
    motif = models.TextField()
    diagnostic = models.TextField(blank=True)
    diagnostic_cim10 = models.CharField(max_length=20, blank=True, help_text="Code CIM-10")

    traitement_prescrit = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)

    est_terminee = models.BooleanField(default=False)
    signature_electronique = models.TextField(blank=True)

    def __str__(self):
        return f"Consultation {self.patient} par {self.medecin.username} - {self.date_consultation.date()}"


class ConstanteVitale(models.Model):
    """Constantes vitales saisies par l'infirmier"""

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='constantes')
    infirmier = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='constantes_saisies')
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='constantes')

    date_saisie = models.DateTimeField(auto_now_add=True)

    tension_arterielle = models.CharField(max_length=20, blank=True)
    frequence_cardiaque = models.IntegerField(null=True, blank=True)
    frequence_respiratoire = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    saturation_o2 = models.IntegerField(null=True, blank=True)
    poids = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    taille = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    autres = models.TextField(blank=True)

    def __str__(self):
        return f"Constantes {self.patient} - {self.date_saisie}"


class PlanSoin(models.Model):
    """Plan de soins infirmier synchronisé aux prescriptions."""

    STATUTS = (
        ('ACTIF', 'Actif'),
        ('TERMINE', 'Terminé'),
        ('SUSPENDU', 'Suspendu'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='plans_soins')
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='plans_soins')
    prescription = models.ForeignKey(
        'prescriptions.Prescription', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='plans_soins',
    )
    infirmier_responsable = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name='plans_soins_assignes',
    )
    medecin_prescripteur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name='plans_soins_prescrits',
    )

    titre = models.CharField(max_length=200)
    description = models.TextField()
    frequence = models.CharField(max_length=100, blank=True, help_text="Ex: 3x/jour, matin et soir")
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='ACTIF')

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Plan {self.titre} — {self.patient}"
