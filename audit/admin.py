from django.contrib import admin
from .models import AuditLog, AuditConsultation

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'utilisateur_username', 'action', 'app_name', 'model_name', 'object_id')
    list_filter = ('action', 'app_name', 'timestamp')
    search_fields = ('utilisateur_username', 'object_repr', 'object_id')
    readonly_fields = ('hash_signature', 'previous_hash')
    
    def has_add_permission(self, request):
        """Empêche l'ajout manuel (le système écrit seul dans l'audit)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification des logs (immuabilité)"""
        return False

@admin.register(AuditConsultation)
class AuditConsultationAdmin(admin.ModelAdmin):
    list_display = ('consultation_id', 'patient_nom', 'medecin_nom', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('patient_nom', 'medecin_nom')