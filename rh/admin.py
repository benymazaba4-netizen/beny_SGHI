from django.contrib import admin
from .models import Personnel, PlanningGarde, Presence, Conge, FichePaie

@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'utilisateur', 'type_personnel', 'service', 'est_actif')
    list_filter = ('type_personnel', 'statut_emploi', 'service', 'est_actif')
    search_fields = ('matricule', 'utilisateur__username', 'utilisateur__first_name', 'utilisateur__last_name')

@admin.register(PlanningGarde)
class PlanningGardeAdmin(admin.ModelAdmin):
    list_display = ('personnel', 'type_garde', 'date_debut', 'date_fin', 'est_effectuee')
    list_filter = ('type_garde', 'est_effectuee', 'service')
    search_fields = ('personnel__utilisateur__username',)

@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('personnel', 'date', 'statut', 'heure_arrivee', 'heure_depart')
    list_filter = ('statut', 'date')
    search_fields = ('personnel__utilisateur__username',)

@admin.register(Conge)
class CongeAdmin(admin.ModelAdmin):
    list_display = ('personnel', 'type_conge', 'date_debut', 'date_fin', 'nb_jours', 'statut')
    list_filter = ('type_conge', 'statut')
    search_fields = ('personnel__utilisateur__username',)

@admin.register(FichePaie)
class FichePaieAdmin(admin.ModelAdmin):
    list_display = ('personnel', 'mois', 'annee', 'salaire_base', 'net_a_payer')
    list_filter = ('annee', 'mois')
    search_fields = ('personnel__utilisateur__username',)