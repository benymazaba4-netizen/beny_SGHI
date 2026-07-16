from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from authentication.models import Utilisateur


class JournalAccesDossier(models.Model):
    """Traçabilité des accès aux dossiers sensibles."""

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name='acces_dossiers',
    )
    patient_id = models.PositiveIntegerField(db_index=True)
    action = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    date_acces = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-date_acces']

    def __str__(self):
        return f"Accès patient #{self.patient_id} par {self.utilisateur}"


class ArchiveRecord(models.Model):
    """Politique d'archivage longue durée."""

    STATUTS = (
        ('ACTIF', 'Actif'),
        ('ARCHIVE', 'Archivé'),
        ('ANONYMISE', 'Anonymisé'),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    contenu = GenericForeignKey('content_type', 'object_id')

    statut = models.CharField(max_length=20, choices=STATUTS, default='ACTIF')
    date_archivage = models.DateTimeField(null=True, blank=True)
    date_expiration_legale = models.DateField(null=True, blank=True)
    archive_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return f"Archive #{self.object_id} — {self.statut}"


class AnonymizationJob(models.Model):
    """Job d'anonymisation pour exploitation statistique."""

    STATUTS = (
        ('EN_ATTENTE', 'En attente'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('ERREUR', 'Erreur'),
    )

    nom = models.CharField(max_length=200)
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    nb_enregistrements = models.PositiveIntegerField(default=0)
    statut = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')
    resultat_fichier = models.CharField(max_length=500, blank=True)
    lance_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    erreur = models.TextField(blank=True)

    def __str__(self):
        return f"Anonymisation {self.nom} — {self.statut}"
