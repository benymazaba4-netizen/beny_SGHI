from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.Model):
    """Rôle pour le RBAC"""
    nom = models.CharField(max_length=50, unique=True)  # Medecin, Infirmier, Patient, etc.
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.nom

class Utilisateur(AbstractUser):
    """Utilisateur personnalisé pour le SGHI"""
    
    # Choix des rôles principaux
    ROLE_CHOICES = (
        ('PATIENT', 'Patient'),
        ('MEDECIN', 'Médecin'),
        ('INFIRMIER', 'Infirmier'),
        ('BIOLOGISTE', 'Biologiste'),
        ('PHARMACIEN', 'Pharmacien'),
        ('SECRETAIRE', 'Secrétaire'),
        ('ADMIN', 'Administrateur'),
        ('COMPTABLE', 'Comptable'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    roles_secondaires = models.ManyToManyField(Role, blank=True)
    
    # Informations personnelles
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    matricule = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    # Sécurité
    is_mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=100, blank=True)
    mfa_backup_codes = models.TextField(blank=True, help_text="Codes de secours JSON")
    mfa_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Verrouillage après échecs de connexion
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)

    # Audit
    date_derniere_connexion = models.DateTimeField(null=True, blank=True)
    ip_derniere_connexion = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


class RefreshToken(models.Model):
    """Refresh token stocké sous forme hashée pour rotation et révocation."""

    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='refresh_tokens')
    token_hash = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    replaced_by = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"RefreshToken for {self.user.username} (revoked={self.revoked})"

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def revoke(self):
        self.revoked = True
        self.save()


class JournalConnexion(models.Model):
    """Historique des connexions utilisateur."""

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='journal_connexions',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    reussie = models.BooleanField(default=True)
    date_connexion = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-date_connexion']

    def __str__(self):
        return f"{self.utilisateur.username} — {self.date_connexion}"