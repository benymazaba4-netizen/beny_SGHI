from django.db import models
from django.utils import timezone
from datetime import timedelta
from clinical.models import Patient, Admission, Consultation
from billing.models import Facture, TransactionPaiement
from laboratory.models import DemandeExamen

class KPICache(models.Model):
    """Cache pour les KPIs (mis à jour périodiquement)"""
    
    TYPES_KPI = (
        ('OCCUPATION', "Taux d'occupation des lits"),
        ('RECETTES_JOUR', "Recettes du jour"),
        ('RECETTES_MOIS', "Recettes du mois"),
        ('PATIENTS_JOUR', "Patients admis aujourd'hui"),
        ('EXAMENS_ATTENTE', "Examens en attente de validation"),
        ('URGENCES', "Patients aux urgences"),
        ('PRESCRIPTIONS_JOUR', "Prescriptions du jour"),
    )
    
    type_kpi = models.CharField(max_length=50, choices=TYPES_KPI, unique=True)
    valeur = models.TextField()
    date_calcul = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
    
    class Meta:
        verbose_name = "KPI en cache"
        verbose_name_plural = "KPIs en cache"
    
    def __str__(self):
        return f"{self.get_type_kpi_display()} : {self.valeur[:50]}"
    
    def est_valide(self):
        return timezone.now() < self.date_expiration

class StatistiqueJournaliere(models.Model):
    """Statistiques agrégées par jour"""
    
    date = models.DateField(unique=True)
    
    nb_admissions = models.IntegerField(default=0)
    nb_sorties = models.IntegerField(default=0)
    nb_consultations = models.IntegerField(default=0)
    nb_examens_prescrits = models.IntegerField(default=0)
    nb_examens_realises = models.IntegerField(default=0)
    nb_examens_valides = models.IntegerField(default=0)
    nb_prescriptions = models.IntegerField(default=0)
    
    montant_total_factures = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    montant_encaisse = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    montant_assurance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    taux_occupation_lits = models.FloatField(default=0)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Statistique journalière"
        verbose_name_plural = "Statistiques journalières"
    
    def __str__(self):
        return f"Statistiques du {self.date}"

class AlertSysteme(models.Model):
    """Alertes système générées automatiquement"""
    
    NIVEAUX = (
        ('INFO', 'Information'),
        ('WARNING', 'Avertissement'),
        ('CRITICAL', 'Critique'),
    )
    
    CATEGORIES = (
        ('STOCK', 'Stock pharmacie'),
        ('PEREMPTION', 'Péremption'),
        ('FINANCE', 'Finance'),
        ('LABORATOIRE', 'Laboratoire'),
        ('RH', 'Ressources humaines'),
        ('SYSTEME', 'Système'),
    )
    
    niveau = models.CharField(max_length=20, choices=NIVEAUX, default='INFO')
    categorie = models.CharField(max_length=20, choices=CATEGORIES)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    
    est_lue = models.BooleanField(default=False)
    est_resolue = models.BooleanField(default=False)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    
    responsable = models.ForeignKey('authentication.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True)
    resolution_commentaire = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_creation', 'niveau']
    
    def __str__(self):
        return f"[{self.get_niveau_display()}] {self.titre}"