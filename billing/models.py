from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from authentication.models import Utilisateur
from clinical.models import Patient, Admission
from prescriptions.models import Prescription
from laboratory.models import DemandeExamen

class Facture(models.Model):
    """Facture générée pour un patient"""
    
    STATUT_FACTURE = (
        ('BROUILLON', 'Brouillon'),
        ('EMISE', 'Émise'),
        ('PARTIELLE', 'Payée partiellement'),
        ('PAYEE', 'Payée totalement'),
        ('IMPAYEE', 'Impayée'),
        ('ANNULEE', 'Annulée'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='factures')
    admission = models.ForeignKey(Admission, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures')
    numero_facture = models.CharField(max_length=50, unique=True, editable=False)
    
    statut = models.CharField(max_length=20, choices=STATUT_FACTURE, default='BROUILLON')
    
    # Montants
    sous_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remise = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_assurance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_patient = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_paye = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_restant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Dates
    date_emission = models.DateTimeField(auto_now_add=True)
    date_echeance = models.DateField(null=True, blank=True)
    
    # Gestion
    emise_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='factures_emises')
    notes = models.TextField(blank=True)
    
    # Fichier PDF
    fichier_pdf = models.FileField(upload_to='factures/', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.numero_facture:
            import datetime
            annee = datetime.datetime.now().year
            mois = datetime.datetime.now().month
            dernier = Facture.objects.filter(numero_facture__startswith=f"FACT{annee}{mois:02d}").count()
            self.numero_facture = f"FACT{annee}{mois:02d}{str(dernier+1).zfill(4)}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_facture} - {self.patient} - {self.get_statut_display()}"
    
    def recalculer_montants(self):
        """Recalcule les montants à partir des lignes de facture."""
        total = self.lignes.aggregate(total=models.Sum('montant'))['total'] or 0
        self.sous_total = total
        montant_apres_remise = total - self.remise
        if self.montant_assurance > montant_apres_remise:
            self.montant_assurance = montant_apres_remise
        self.montant_patient = montant_apres_remise - self.montant_assurance
        self.montant_restant = self.montant_patient - self.montant_paye

        if self.statut not in ('ANNULEE', 'BROUILLON'):
            if self.montant_restant <= 0 and self.montant_patient > 0:
                self.statut = 'PAYEE'
            elif self.montant_paye > 0:
                self.statut = 'PARTIELLE'
            elif self.montant_paye == 0:
                self.statut = 'IMPAYEE' if self.statut == 'EMISE' else self.statut

        self.save()
        return self.montant_restant

class LigneFacture(models.Model):
    """Ligne détaillée d'une facture"""
    
    TYPES_LIGNE = (
        ('NUITEE', 'Nuitée'),
        ('CONSULTATION', 'Consultation'),
        ('EXAMEN', 'Examen'),
        ('MEDICAMENT', 'Médicament'),
        ('CONSOMMABLE', 'Consommable'),
        ('ACTE', 'Acte médical'),
    )
    
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    type_ligne = models.CharField(max_length=20, choices=TYPES_LIGNE)
    description = models.CharField(max_length=255)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    montant = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    # Références optionnelles
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True)
    demande_examen = models.ForeignKey(DemandeExamen, on_delete=models.SET_NULL, null=True, blank=True)
    admission = models.ForeignKey(Admission, on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        self.montant = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)
        self.facture.recalculer_montants()
    
    def __str__(self):
        return f"{self.facture.numero_facture} - {self.description} : {self.montant} FCFA"

class TransactionPaiement(models.Model):
    """Transaction de paiement (espèces, carte, Mobile Money)"""
    
    MODES_PAIEMENT = (
        ('ESPECES', 'Espèces'),
        ('CARTE', 'Carte bancaire'),
        ('MTN', 'MTN Mobile Money'),
        ('AIRTEL', 'Airtel Money'),
        ('VIRAMENT', 'Virement'),
    )
    
    STATUT_TRANSACTION = (
        ('PENDING', 'En attente'),
        ('SUCCESS', 'Réussi'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
        ('REFUNDED', 'Remboursé'),
    )
    
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
    mode_paiement = models.CharField(max_length=20, choices=MODES_PAIEMENT)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_TRANSACTION, default='PENDING')
    
    # Pour Mobile Money
    operateur = models.CharField(max_length=10, blank=True)  # MTN, AIRTEL
    numero_telephone = models.CharField(max_length=20, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True, help_text="ID transaction opérateur")
    
    # Pour traçabilité
    date_transaction = models.DateTimeField(auto_now_add=True)
    effectue_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    reference_externe = models.CharField(max_length=100, blank=True)
    
    # Webhook / API Mobile Money
    api_response = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.mode_paiement} - {self.montant} FCFA - {self.get_statut_display()}"
    
    def confirmer_paiement(self):
        """Confirme le paiement et met à jour la facture."""
        self.statut = 'SUCCESS'
        self.save()

        facture = self.facture
        facture.montant_paye += self.montant
        facture.montant_restant = facture.montant_patient - facture.montant_paye

        if facture.montant_restant <= 0:
            facture.statut = 'PAYEE'
        elif facture.montant_paye > 0:
            facture.statut = 'PARTIELLE'

        facture.save()

        from billing.models import JournalComptable
        JournalComptable.enregistrer(
            facture=facture,
            type_operation='PAIEMENT',
            montant=self.montant,
            description=f"Paiement {self.get_mode_paiement_display()} — {facture.numero_facture}",
            utilisateur=self.effectue_par,
        )

class Assurance(models.Model):
    """Compagnie d'assurance / mutuelle"""
    
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    taux_prise_en_charge = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Pourcentage pris en charge (ex: 70%)"
    )
    contact = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    est_actif = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.nom} ({self.taux_prise_en_charge}%)"

class PriseEnChargeAssurance(models.Model):
    """Prise en charge d'un patient par une assurance"""
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prises_en_charge')
    assurance = models.ForeignKey(Assurance, on_delete=models.CASCADE)
    numero_contrat = models.CharField(max_length=100)
    date_debut = models.DateField()
    date_fin = models.DateField()
    est_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.patient} - {self.assurance.nom}"


class BillingError(Exception):
    pass


class JournalComptable(models.Model):
    """Journal comptable immuable — conformité financière SGHL"""

    TYPES_OPERATION = (
        ('EMISSION', 'Émission facture'),
        ('TIERS_PAYANT', 'Tiers-payant assurance'),
        ('PAIEMENT', 'Paiement reçu'),
        ('AJUSTEMENT', 'Ajustement'),
        ('ANNULATION', 'Annulation'),
    )

    facture = models.ForeignKey(Facture, on_delete=models.PROTECT, related_name='journal')
    type_operation = models.CharField(max_length=20, choices=TYPES_OPERATION)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    hash_signature = models.CharField(max_length=128, unique=True)
    previous_hash = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Écriture comptable'

    def __str__(self):
        return f"{self.timestamp} — {self.type_operation} — {self.montant} FCFA"

    def save(self, *args, **kwargs):
        if self.pk:
            raise BillingError("Le journal comptable est immuable")
        import hashlib
        dernier = JournalComptable.objects.order_by('-timestamp').first()
        if dernier:
            self.previous_hash = dernier.hash_signature
        data = (
            f"{self.facture_id}|{self.type_operation}|{self.montant}|"
            f"{self.description}|{self.previous_hash}"
        )
        self.hash_signature = hashlib.sha256(data.encode()).hexdigest()
        super().save(*args, **kwargs)

    @classmethod
    def enregistrer(cls, facture, type_operation, montant, description, utilisateur=None):
        return cls.objects.create(
            facture=facture,
            type_operation=type_operation,
            montant=montant,
            description=description,
            utilisateur=utilisateur,
        )


class SecretariatInvoice(models.Model):
    """Facture caisse secrétariat — paiement obligatoire avant consultation."""

    INVOICE_STATUS = (
        ('PENDING', 'En attente'),
        ('PAID', 'Payé'),
    )
    PAYMENT_METHODS = (
        ('CASH', 'Espèces'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CARD', 'Carte'),
    )

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='secretariat_invoices',
    )
    admission = models.ForeignKey(
        Admission, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='secretariat_invoices',
    )
    consultation = models.ForeignKey(
        'clinical.Consultation', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='secretariat_invoices',
    )
    rendez_vous = models.ForeignKey(
        'appointments.RendezVous', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='secretariat_invoices',
    )
    facture = models.ForeignKey(
        Facture, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='secretariat_invoices',
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True)
    libelle = models.CharField(max_length=255, default='Frais de consultation')

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='encaissements_secretariat',
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['patient', 'status']),
        ]

    def __str__(self):
        return f"{self.patient} — {self.amount} FCFA — {self.get_status_display()}"


class EcheancePaiement(models.Model):
    """Échéance d'un plan de paiement échelonné."""

    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='echeances')
    date_echeance = models.DateField()
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    est_payee = models.BooleanField(default=False)
    date_paiement = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['date_echeance']

    def __str__(self):
        return f"{self.facture.numero_facture} — {self.date_echeance} — {self.montant} FCFA"