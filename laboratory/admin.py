from django.contrib import admin
from .models import ExamenType, DemandeExamen, Prelevement, ResultatExamen, HistoriqueModificationResultat

@admin.register(ExamenType)
class ExamenTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'categorie', 'prix', 'est_actif')
    list_filter = ('categorie', 'est_actif')
    search_fields = ('code', 'nom')

@admin.register(DemandeExamen)
class DemandeExamenAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'examen_type', 'statut', 'urgence', 'date_prescription')
    list_filter = ('statut', 'urgence', 'date_prescription')
    search_fields = ('patient__nom', 'patient__prenom')

@admin.register(Prelevement)
class PrelevementAdmin(admin.ModelAdmin):
    list_display = ('demande', 'type_prelevement', 'date_prelevement', 'preleve_par')
    list_filter = ('type_prelevement', 'date_prelevement')

@admin.register(ResultatExamen)
class ResultatExamenAdmin(admin.ModelAdmin):
    list_display = ('demande', 'est_valide', 'est_publie', 'date_validation', 'valide_par')
    list_filter = ('est_valide', 'est_publie', 'date_validation')
    readonly_fields = ('signature_electronique', 'fichier_pdf')


@admin.register(HistoriqueModificationResultat)
class HistoriqueModificationResultatAdmin(admin.ModelAdmin):
    list_display = ('resultat', 'modifie_par', 'timestamp', 'ip_adresse')
    list_filter = ('timestamp',)
    readonly_fields = ('resultat', 'modifie_par', 'anciens_resultats', 'nouveaux_resultats',
                       'ancienne_interpretation', 'nouvelle_interpretation', 'timestamp', 'ip_adresse')