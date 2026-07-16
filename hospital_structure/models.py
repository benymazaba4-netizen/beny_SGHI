from django.db import models
from authentication.models import Utilisateur

class Batiment(models.Model):
    """Bâtiment de l'hôpital (ex: Bâtiment A, Mère-Enfant, Urgences)"""
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    adresse = models.TextField(blank=True)
    nombre_etages = models.IntegerField(default=1)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.nom}"

class ServiceHospitalier(models.Model):
    """Service médical (ex: Cardiologie, Pédiatrie, Urgences)"""
    
    TYPE_SERVICE = (
        ('MEDICAL', 'Service Médical'),
        ('CHIRURGICAL', 'Service Chirurgical'),
        ('TECHNIQUE', 'Plateau Technique'),
        ('ADMINISTRATIF', 'Service Administratif'),
    )
    
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    type_service = models.CharField(max_length=20, choices=TYPE_SERVICE, default='MEDICAL')
    
    batiment = models.ForeignKey(Batiment, on_delete=models.CASCADE, related_name='services')
    chef_de_service = models.ForeignKey(
        Utilisateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='services_diriges'
    )
    
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    etage = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    est_actif = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.nom}"

class Chambre(models.Model):
    """Chambre dans un service"""
    
    TYPES_CHAMBRE = (
        ('INDIVIDUELLE', 'Individuelle'),
        ('DOUBLE', 'Double'),
        ('TRIPLE', 'Triple'),
        ('SALLE_COMMUNE', 'Salle Commune'),
        ('REANIMATION', 'Réanimation'),
        ('ISOLEMENT', 'Isolement'),
    )
    
    numero = models.CharField(max_length=10)
    type_chambre = models.CharField(max_length=20, choices=TYPES_CHAMBRE, default='DOUBLE')
    capacite_max = models.IntegerField(default=2)
    
    service = models.ForeignKey(ServiceHospitalier, on_delete=models.CASCADE, related_name='chambres')
    
    prix_par_jour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    a_baignoire = models.BooleanField(default=False)
    a_telephone = models.BooleanField(default=False)
    a_television = models.BooleanField(default=False)
    est_actif = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['service', 'numero']
    
    def __str__(self):
        return f"{self.service.code} - Chambre {self.numero} ({self.get_type_chambre_display()})"

class Lit(models.Model):
    """Lit dans une chambre — verrouillage optimiste sur statut."""
    
    STATUT_LIT = (
        ('LIBRE', 'Libre'),
        ('OCCUPE', 'Occupé'),
        ('RESERVE', 'Réservé'),
        ('HORS_SERVICE', 'Hors Service'),
    )
    
    numero = models.CharField(max_length=10)
    statut = models.CharField(max_length=20, choices=STATUT_LIT, default='LIBRE')
    version = models.PositiveIntegerField(default=0)
    
    chambre = models.ForeignKey(Chambre, on_delete=models.CASCADE, related_name='lits')
    
    patient_actuel = models.ForeignKey(
        'clinical.Patient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lit_occupe'
    )
    
    est_medicalise = models.BooleanField(default=False)
    hauteur_reglable = models.BooleanField(default=False)
    barriere_laterale = models.BooleanField(default=True)
    date_dernier_changement = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['chambre', 'numero']
    
    def __str__(self):
        statut_display = dict(self.STATUT_LIT).get(self.statut, 'Inconnu')
        return f"Lit {self.numero} - {self.chambre} ({statut_display})"
    
    def est_libre(self):
        return self.statut == 'LIBRE' and self.patient_actuel_id is None
    
    def est_disponible_pour_admission(self):
        return (
            self.statut == 'LIBRE'
            and self.patient_actuel_id is None
            and self.chambre.est_actif
            and self.statut != 'HORS_SERVICE'
        )
    
    def _verifier_version(self, version_attendue):
        if version_attendue is not None and self.version != version_attendue:
            raise ValueError(
                f"Conflit de version lit (attendu {version_attendue}, actuel {self.version}). "
                "Rechargez et réessayez."
            )
    
    def occuper_atomique(self, patient, version_attendue=None):
        """Occupation atomique : UPDATE conditionnel statut=LIBRE (anti race condition)."""
        from django.db.models import F
        from django.utils import timezone

        self._verifier_version(version_attendue)
        if not self.chambre.est_actif:
            raise ValueError(f"La chambre {self.chambre.numero} est inactive")

        filtres = {'pk': self.pk, 'statut': 'LIBRE', 'patient_actuel__isnull': True}
        if version_attendue is not None:
            filtres['version'] = version_attendue

        updated = Lit.objects.filter(**filtres).update(
            statut='OCCUPE',
            patient_actuel_id=patient.pk,
            version=F('version') + 1,
            date_dernier_changement=timezone.now().date(),
        )
        if updated == 0:
            raise ValueError(
                f"Le lit {self.numero} n'est plus disponible (concurrence ou version obsolète)"
            )
        self.refresh_from_db()
    
    def occuper(self, patient):
        """Règle métier: 1 lit = 1 patient maximum."""
        self.occuper_atomique(patient)
    
    def liberer_atomique(self):
        """Libération atomique avec incrément de version."""
        from django.db.models import F
        from django.utils import timezone

        updated = Lit.objects.filter(pk=self.pk, statut='OCCUPE').update(
            statut='LIBRE',
            patient_actuel_id=None,
            version=F('version') + 1,
            date_dernier_changement=timezone.now().date(),
        )
        if updated == 0:
            self.refresh_from_db()
            if self.statut == 'LIBRE':
                return
            raise ValueError(f"Impossible de libérer le lit {self.numero}")
        self.refresh_from_db()
    
    def liberer(self):
        self.liberer_atomique()