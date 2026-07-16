from django.db import models
from authentication.models import Utilisateur
from hospital_structure.models import ServiceHospitalier

class Personnel(models.Model):
    """Personnel de l'hôpital (médecins, infirmiers, etc.)"""
    
    TYPES_PERSONNEL = (
        ('MEDECIN', 'Médecin'),
        ('INFIRMIER', 'Infirmier'),
        ('BIOLOGISTE', 'Biologiste'),
        ('PHARMACIEN', 'Pharmacien'),
        ('SECRETAIRE', 'Secrétaire'),
        ('ADMINISTRATIF', 'Administratif'),
        ('TECHNICIEN', 'Technicien de laboratoire'),
        ('AUTRE', 'Autre'),
    )
    
    STATUT_EMPLOI = (
        ('CDI', 'CDI'),
        ('CDD', 'CDD'),
        ('STAGIAIRE', 'Stagiaire'),
        ('VACATAIRE', 'Vacataire'),
        ('CONSULTANT', 'Consultant'),
    )
    
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='personnel')
    
    # Informations professionnelles
    type_personnel = models.CharField(max_length=20, choices=TYPES_PERSONNEL)
    statut_emploi = models.CharField(max_length=20, choices=STATUT_EMPLOI, default='CDI')
    service = models.ForeignKey(ServiceHospitalier, on_delete=models.SET_NULL, null=True, related_name='personnels')
    
    matricule = models.CharField(max_length=50, unique=True)
    fonction = models.CharField(max_length=200, blank=True)
    specialite = models.CharField(max_length=200, blank=True, help_text="Pour les médecins: Cardiologue, Pédiatre...")
    
    # Coordonnées professionnelles
    telephone_pro = models.CharField(max_length=20, blank=True)
    email_pro = models.EmailField(blank=True)
    bureau = models.CharField(max_length=100, blank=True)
    
    # Dates
    date_embauche = models.DateField()
    date_fin_contrat = models.DateField(null=True, blank=True)
    
    # Documents
    diplomes = models.TextField(blank=True)
    num_ordre_medecins = models.CharField(max_length=100, blank=True)
    
    # Audit
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.matricule} - {self.utilisateur.get_full_name()} - {self.get_type_personnel_display()}"

class PlanningGarde(models.Model):
    """Planning des gardes pour les médecins et infirmiers"""
    
    TYPES_GARDE = (
        ('JOUR', 'Garde de jour (8h-20h)'),
        ('NUIT', 'Garde de nuit (20h-8h)'),
        ('24H', 'Garde de 24h'),
        ('ASTREINTE', 'Astreinte'),
        ('PERMANENCE', 'Permanence'),
    )
    
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='gardes')
    service = models.ForeignKey(ServiceHospitalier, on_delete=models.CASCADE, related_name='gardes')
    
    type_garde = models.CharField(max_length=20, choices=TYPES_GARDE)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    
    est_effectuee = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True)
    
    # Enregistrement
    planifie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='gardes_planifiees')
    date_planification = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date_debut']
        verbose_name = "Planning de garde"
        verbose_name_plural = "Plannings de gardes"
    
    def __str__(self):
        return f"{self.personnel} - {self.get_type_garde_display()} - {self.date_debut.strftime('%d/%m/%Y')}"
    
    def chevauchement(self):
        """Vérifie s'il y a chevauchement avec une autre garde"""
        return PlanningGarde.objects.filter(
            personnel=self.personnel,
            date_debut__lt=self.date_fin,
            date_fin__gt=self.date_debut
        ).exclude(id=self.id).exists()

class Presence(models.Model):
    """Enregistrement des présences / absences"""
    
    STATUT_PRESENCE = (
        ('PRESENT', 'Présent'),
        ('ABSENT', 'Absent'),
        ('CONGE', 'Congé'),
        ('MALADIE', 'Arrêt maladie'),
        ('FORMATION', 'Formation'),
        ('RETARD', 'Retard'),
    )
    
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='presences')
    date = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_PRESENCE, default='PRESENT')
    heure_arrivee = models.TimeField(null=True, blank=True)
    heure_depart = models.TimeField(null=True, blank=True)
    justificatif = models.FileField(upload_to='presences/', null=True, blank=True)
    commentaire = models.TextField(blank=True)
    
    # Enregistrement
    saisi_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='presences_saisies')
    date_saisie = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['personnel', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.personnel} - {self.date} - {self.get_statut_display()}"

class Conge(models.Model):
    """Demande et gestion des congés"""
    
    TYPES_CONGE = (
        ('ANNUEL', 'Congé annuel'),
        ('MALADIE', 'Arrêt maladie'),
        ('SANS_SOLDE', 'Congé sans solde'),
        ('MATERNITE', 'Congé maternité'),
        ('EVENEMENT', 'Congé événement familial'),
    )
    
    STATUT_CONGE = (
        ('ATTENTE', 'En attente de validation'),
        ('VALIDE', 'Validé'),
        ('REFUSE', 'Refusé'),
        ('ANNULE', 'Annulé'),
        ('TERMINE', 'Terminé'),
    )
    
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='conges')
    type_conge = models.CharField(max_length=20, choices=TYPES_CONGE)
    statut = models.CharField(max_length=20, choices=STATUT_CONGE, default='ATTENTE')
    
    date_debut = models.DateField()
    date_fin = models.DateField()
    nb_jours = models.IntegerField(editable=False)
    
    motif = models.TextField()
    
    # Documents justificatifs
    justificatif = models.FileField(upload_to='conges/', null=True, blank=True)
    
    # Validation
    demande_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='conges_demandes')
    date_demande = models.DateTimeField(auto_now_add=True)
    
    valide_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_valides')
    date_validation = models.DateTimeField(null=True, blank=True)
    commentaire_validation = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        from datetime import timedelta
        if self.date_debut and self.date_fin:
            delta = self.date_fin - self.date_debut
            self.nb_jours = delta.days + 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.personnel} - {self.get_type_conge_display()} ({self.date_debut} au {self.date_fin})"

class FichePaie(models.Model):
    """Fiche de paie du personnel"""
    
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='fiches_paie')
    mois = models.IntegerField()  # 1 à 12
    annee = models.IntegerField()
    
    salaire_base = models.DecimalField(max_digits=12, decimal_places=2)
    primes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_a_payer = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    nb_heures_sup = models.IntegerField(default=0)
    montant_heures_sup = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    details = models.JSONField(default=dict, help_text="Détail des primes et déductions")
    
    fichier_pdf = models.FileField(upload_to='fiches_paie/', null=True, blank=True)
    
    date_generation = models.DateTimeField(auto_now_add=True)
    generee_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ['personnel', 'mois', 'annee']
        ordering = ['-annee', '-mois']
    
    def save(self, *args, **kwargs):
        self.net_a_payer = self.salaire_base + self.primes + self.montant_heures_sup - self.deductions
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Paie {self.personnel} - {self.mois}/{self.annee}"