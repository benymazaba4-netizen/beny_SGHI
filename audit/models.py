from django.db import models
from authentication.models import Utilisateur

class AuditLog(models.Model):
    """Journal immuable de toutes les actions critiques"""
    
    ACTION_TYPES = (
        ('CREATE', 'Création'),
        ('READ', 'Lecture'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
        ('VALIDATE', 'Validation'),
        ('ARCHIVE', 'Archivage'),
        ('EXPORT', 'Export'),
        ('PRINT', 'Impression'),
        ('SIGN', 'Signature'),
    )
    
    id_log = models.AutoField(primary_key=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    utilisateur_username = models.CharField(max_length=150, blank=True)
    utilisateur_ip = models.GenericIPAddressField(null=True, blank=True)
    
    app_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)
    object_repr = models.CharField(max_length=200, blank=True)
    
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    fields_changed = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    user_agent = models.TextField(blank=True)
    
    hash_signature = models.CharField(max_length=128, unique=True)
    previous_hash = models.CharField(max_length=128, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp} - {self.utilisateur_username} - {self.action}"
    
    def save(self, *args, **kwargs):
        import hashlib
        
        if not self.hash_signature:
            dernier = AuditLog.objects.filter().first()
            if dernier:
                self.previous_hash = dernier.hash_signature
            
            data = f"{self.timestamp}{self.utilisateur_id}{self.action}{self.app_name}{self.model_name}{self.object_id}{self.old_value}{self.new_value}{self.previous_hash}"
            self.hash_signature = hashlib.sha256(data.encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    @classmethod
    def log_action(cls, utilisateur, action, instance, old_value=None, new_value=None, request=None):
        log = cls(
            action=action,
            utilisateur=utilisateur,
            utilisateur_username=utilisateur.username if utilisateur else 'SYSTEM',
            utilisateur_ip=(request.META.get('REMOTE_ADDR') or None) if request else None,
            app_name=instance._meta.app_label,
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk),
            object_repr=str(instance),
            old_value=old_value or '',
            new_value=new_value or '',
            request_method=request.method if request else '',
            request_path=request.path if request else '',
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
        )
        log.save()
        return log

class AuditConsultation(models.Model):
    consultation_id = models.IntegerField()
    patient_nom = models.CharField(max_length=200)
    medecin_nom = models.CharField(max_length=200)
    date_consultation = models.DateTimeField()
    action = models.CharField(max_length=50)
    utilisateur = models.CharField(max_length=150)
    ip = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Consultation {self.consultation_id} - {self.action} par {self.utilisateur}"