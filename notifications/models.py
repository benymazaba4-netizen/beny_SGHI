from django.db import models
from authentication.models import Utilisateur


class DeviceToken(models.Model):
    """Token FCM/APNs pour notifications push."""

    PLATEFORMES = (
        ('ANDROID', 'Android'),
        ('IOS', 'iOS'),
        ('WEB', 'Web'),
    )

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='device_tokens',
    )
    token = models.CharField(max_length=512, unique=True)
    plateforme = models.CharField(max_length=10, choices=PLATEFORMES, default='ANDROID')
    est_actif = models.BooleanField(default=True)
    date_enregistrement = models.DateTimeField(auto_now_add=True)
    date_dernier_usage = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.utilisateur.username} — {self.plateforme}"


class Notification(models.Model):
    """Notification in-app et push."""

    TYPES = (
        ('RDV', 'Rendez-vous'),
        ('MEDICAMENT', 'Rappel médicament'),
        ('RESULTAT', 'Résultat laboratoire'),
        ('MESSAGE', 'Message'),
        ('GENERAL', 'Général'),
    )

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='notifications',
    )
    type_notification = models.CharField(max_length=20, choices=TYPES, default='GENERAL')
    titre = models.CharField(max_length=200)
    corps = models.TextField()
    lien = models.CharField(max_length=500, blank=True)
    est_lue = models.BooleanField(default=False)
    push_envoyee = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} → {self.utilisateur.username}"
