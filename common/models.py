"""
Modèle pour tracker les uploads de fichiers et images.
"""

from django.db import models
from authentication.models import Utilisateur


class Upload(models.Model):
    """Fichier uploadé avec métadonnées"""

    TYPE_CHOICES = (
        ('IMAGE', 'Image'),
        ('PDF', 'PDF'),
        ('DOCUMENT', 'Document'),
        ('AUTRE', 'Autre'),
    )

    # Métadonnées
    uuid = models.CharField(max_length=64, unique=True, db_index=True)
    type_fichier = models.CharField(max_length=20, choices=TYPE_CHOICES)
    nom_original = models.CharField(max_length=255)
    nom_stocke = models.CharField(max_length=255, db_index=True)
    chemin_stockage = models.CharField(max_length=500)
    
    # Validation
    mime_type = models.CharField(max_length=100)
    taille_octets = models.BigIntegerField()
    hash_sha256 = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Audit
    uploade_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploads'
    )
    date_upload = models.DateTimeField(auto_now_add=True, db_index=True)
    date_acces_dernier = models.DateTimeField(null=True, blank=True)
    
    # Utilisation
    contenu_type = models.CharField(max_length=50, default='general')  # 'patient_photo', 'exam_result', etc.
    contenu_id = models.PositiveIntegerField(null=True, blank=True)  # ID du patient, exam, etc.
    
    # Marqueurs
    est_actif = models.BooleanField(default=True)
    est_supprime_logiquement = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_upload']
        indexes = [
            models.Index(fields=['hash_sha256']),
            models.Index(fields=['uploade_par', '-date_upload']),
            models.Index(fields=['contenu_type', 'contenu_id']),
        ]
    
    def __str__(self):
        return f"{self.nom_original} ({self.taille_octets} bytes)"
    
    def enregistrer_acces(self):
        """Met à jour la date du dernier accès"""
        from django.utils import timezone
        self.date_acces_dernier = timezone.now()
        self.save(update_fields=['date_acces_dernier'])
    
    def supprimer_logiquement(self):
        """Marque comme supprimé sans vraiment supprimer"""
        self.est_supprime_logiquement = True
        self.est_actif = False
        self.save(update_fields=['est_supprime_logiquement', 'est_actif'])


class EmailLog(models.Model):
    """Traçabilité immutable de tous les emails envoyés — audit trail RGPD."""

    STATUT_CHOICES = (
        ('EN_ATTENTE', 'En attente'),
        ('ENVOYE', 'Envoyé'),
        ('ECHEC', 'Échec'),
        ('REBOND', 'Rebond'),
        ('SPAM', 'Marqué spam'),
    )

    TYPE_EMAIL_CHOICES = (
        ('OTP_LOGIN', 'OTP - Connexion'),
        ('RDV_CONFIRMATION', 'RDV - Confirmation'),
        ('RDV_REMINDER', 'RDV - Rappel 24h'),
        ('EXAM_PUBLISHED', 'Exam - Résultats publiés'),
        ('PATIENT_REGISTRATION', 'Inscription - Bienvenue'),
        ('PRESCRIPTION_VALIDATED', 'Prescription validée'),
        ('DISCHARGE_NOTIFICATION', 'Sortie hospitalière'),
        ('INVOICE_CREATED', 'Facture créée'),
        ('MEDICATION_REMINDER', 'Rappel médicament'),
        ('DOCTOR_ALERT', 'Alerte médecin'),
        ('OTHER', 'Autre'),
    )

    # Destinataire
    destinataire = models.EmailField(db_index=True)
    utilisateur = models.ForeignKey(
        'authentication.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs'
    )

    # Contenu
    sujet = models.CharField(max_length=255)
    type_email = models.CharField(max_length=50, choices=TYPE_EMAIL_CHOICES, default='OTHER')
    contenu_plain = models.TextField()
    contenu_html = models.TextField(blank=True)

    # Statut et erreur
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE', db_index=True)
    erreur_message = models.TextField(blank=True)

    # Métadonnées
    uuid_message = models.CharField(max_length=100, unique=True, null=True, blank=True)
    tentative_num = models.PositiveSmallIntegerField(default=0)
    max_tentatives = models.PositiveSmallIntegerField(default=3)

    # Audit
    date_creation = models.DateTimeField(auto_now_add=True, db_index=True)
    date_envoi = models.DateTimeField(null=True, blank=True)
    date_maj = models.DateTimeField(auto_now=True)
    ip_origine = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['destinataire', '-date_creation']),
            models.Index(fields=['utilisateur', '-date_creation']),
            models.Index(fields=['type_email', 'statut']),
        ]

    def __str__(self):
        return f"{self.type_email} → {self.destinataire} ({self.statut})"

    def marquer_envoye(self):
        """Marque l'email comme envoyé."""
        from django.utils import timezone
        self.statut = 'ENVOYE'
        self.date_envoi = timezone.now()
        self.tentative_num += 1
        self.save(update_fields=['statut', 'date_envoi', 'tentative_num'])

    def marquer_echec(self, erreur: str):
        """Marque l'email comme en échec avec message d'erreur."""
        self.statut = 'ECHEC'
        self.erreur_message = erreur
        self.tentative_num += 1
        self.save(update_fields=['statut', 'erreur_message', 'tentative_num'])
