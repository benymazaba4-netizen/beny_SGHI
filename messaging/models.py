from django.db import models
from authentication.models import Utilisateur
from clinical.models import Patient


class Conversation(models.Model):
    """Fil de conversation médecin ↔ patient."""

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='conversations')
    medecin = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='conversations_medecin',
    )
    sujet = models.CharField(max_length=200, blank=True)
    est_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_dernier_message = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('patient', 'medecin')
        ordering = ['-date_dernier_message']

    def __str__(self):
        return f"Conv. {self.patient} ↔ Dr {self.medecin.username}"


class Message(models.Model):
    """Message dans une conversation."""

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages',
    )
    expediteur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='messages_envoyes',
    )
    contenu = models.TextField()
    est_lu = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_envoi']

    def __str__(self):
        return f"Msg #{self.id} — {self.expediteur.username}"
