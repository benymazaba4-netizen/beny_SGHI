from django.contrib import admin
from .models import Upload, EmailLog


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'nom_original', 'type_fichier', 'taille_octets', 'uploade_par', 'date_upload')
    list_filter = ('type_fichier', 'date_upload', 'est_actif', 'est_supprime_logiquement')
    search_fields = ('uuid', 'nom_original', 'nom_stocke', 'hash_sha256')
    readonly_fields = ('uuid', 'hash_sha256', 'date_upload', 'date_acces_dernier')
    fieldsets = (
        ('Identifiants', {
            'fields': ('uuid', 'nom_original', 'nom_stocke', 'chemin_stockage')
        }),
        ('Fichier', {
            'fields': ('type_fichier', 'mime_type', 'taille_octets', 'hash_sha256')
        }),
        ('Audit', {
            'fields': ('uploade_par', 'date_upload', 'date_acces_dernier')
        }),
        ('Utilisation', {
            'fields': ('contenu_type', 'contenu_id')
        }),
        ('État', {
            'fields': ('est_actif', 'est_supprime_logiquement', 'notes')
        }),
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Admin pour traçabilité des emails."""
    list_display = ('type_email', 'destinataire', 'statut', 'tentative_num', 'date_creation')
    list_filter = ('type_email', 'statut', 'date_creation')
    search_fields = ('destinataire', 'utilisateur__username', 'sujet')
    readonly_fields = ('uuid_message', 'date_creation', 'date_maj', 'contenu_plain', 'contenu_html')
    
    fieldsets = (
        ('Destinataire', {
            'fields': ('destinataire', 'utilisateur')
        }),
        ('Contenu', {
            'fields': ('sujet', 'type_email', 'contenu_plain', 'contenu_html')
        }),
        ('Statut', {
            'fields': ('statut', 'erreur_message', 'tentative_num', 'max_tentatives')
        }),
        ('Traçabilité', {
            'fields': ('uuid_message', 'date_creation', 'date_envoi', 'date_maj', 'ip_origine', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-date_creation',)
    
    def has_add_permission(self, request):
        """Empêcher l'ajout manuel (auto-généré seulement)."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression (audit trail immutable)."""
        return False
