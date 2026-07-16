from django.db import models
from django.core.exceptions import ValidationError
from datetime import date
from prescriptions.models import Medicament

class Lot(models.Model):
    """Lot de médicaments reçu"""
    
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name='lots')
    numero_lot = models.CharField(max_length=100, unique=True)
    quantite_initiale = models.IntegerField()
    quantite_restante = models.IntegerField()
    date_fabrication = models.DateField()
    date_peremption = models.DateField()
    date_reception = models.DateField(auto_now_add=True)
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fournisseur = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.medicament.nom} - Lot {self.numero_lot} ({self.quantite_restante} restants)"
    
    def est_perime(self):
        return self.date_peremption < date.today()
    
    def est_alerte_rupture(self, seuil=10):
        return self.quantite_restante <= seuil
    
    def clean(self):
        if self.date_peremption <= self.date_fabrication:
            raise ValidationError("La date de péremption doit être postérieure à la date de fabrication")
        if self.quantite_restante > self.quantite_initiale:
            raise ValidationError("La quantité restante ne peut pas dépasser la quantité initiale")
        if self.est_perime() and self.quantite_restante > 0:
            raise ValidationError("Ce lot est périmé, mettez la quantité restante à 0")

class Stock(models.Model):
    """Stock global d'un médicament (agrégation des lots)"""
    
    medicament = models.OneToOneField(Medicament, on_delete=models.CASCADE, related_name='stock')
    quantite_totale = models.IntegerField(default=0)
    seuil_alerte = models.IntegerField(default=10)
    
    def __str__(self):
        return f"{self.medicament.nom} : {self.quantite_totale} unités"
    
    def mettre_a_jour(self):
        """Met à jour la quantité totale à partir des lots non périmés"""
        total = Lot.objects.filter(
            medicament=self.medicament,
            date_peremption__gte=date.today()
        ).aggregate(total=models.Sum('quantite_restante'))['total'] or 0
        self.quantite_totale = total
        self.save()
        return total
    
    def est_rupture(self):
        return self.quantite_totale <= 0
    
    def est_alerte(self):
        return self.quantite_totale <= self.seuil_alerte and self.quantite_totale > 0

class MouvementStock(models.Model):
    """Historique des mouvements de stock"""
    
    TYPES_MOUVEMENT = (
        ('ENTREE', 'Entrée (réception)'),
        ('SORTIE', 'Sortie (consommation)'),
        ('PERTE', 'Perte (péremption/casse)'),
        ('RETOUR', 'Retour fournisseur'),
        ('AJUSTEMENT', 'Ajustement inventaire'),
    )
    
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name='mouvements')
    lot = models.ForeignKey(Lot, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements')
    type_mouvement = models.CharField(max_length=20, choices=TYPES_MOUVEMENT)
    quantite = models.IntegerField()
    date_mouvement = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey('authentication.Utilisateur', on_delete=models.SET_NULL, null=True)
    reference = models.CharField(max_length=100, blank=True, help_text="Prescription ID, Bon de commande, etc.")
    commentaire = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_type_mouvement_display()} - {self.medicament.nom} : {self.quantite}"

class AlerteStock(models.Model):
    """Alerte générée automatiquement pour rupture ou seuil critique"""
    
    TYPES_ALERTE = (
        ('RUPTURE', 'Rupture de stock'),
        ('SEUIL', 'Seuil d\'alerte atteint'),
        ('PEREMPTION', 'Lot proche de péremption'),
    )
    
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name='alertes')
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, null=True, blank=True, related_name='alertes')
    type_alerte = models.CharField(max_length=20, choices=TYPES_ALERTE)
    message = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    est_lue = models.BooleanField(default=False)
    est_resolue = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Alerte {self.get_type_alerte_display()} - {self.medicament.nom}"