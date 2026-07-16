from django.contrib import admin
from .models import KPICache, StatistiqueJournaliere, AlertSysteme

@admin.register(KPICache)
class KPICacheAdmin(admin.ModelAdmin):
    list_display = ('type_kpi', 'valeur', 'date_calcul', 'date_expiration')
    list_filter = ('type_kpi',)
    readonly_fields = ('date_calcul',)

@admin.register(StatistiqueJournaliere)
class StatistiqueJournaliereAdmin(admin.ModelAdmin):
    list_display = ('date', 'nb_admissions', 'nb_consultations', 'montant_encaisse', 'taux_occupation_lits')
    list_filter = ('date',)
    readonly_fields = ('date_creation', 'date_mise_a_jour')

@admin.register(AlertSysteme)
class AlertSystemeAdmin(admin.ModelAdmin):
    list_display = ('titre', 'categorie', 'niveau', 'date_creation', 'est_lue', 'est_resolue')
    list_filter = ('niveau', 'categorie', 'est_lue', 'est_resolue')
    search_fields = ('titre', 'message')