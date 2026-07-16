from django.contrib import admin
from .models import Patient, Admission, Consultation, ConstanteVitale

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('numero_dossier', 'nom', 'prenom', 'telephone', 'date_creation')
    search_fields = ('nom', 'prenom', 'numero_dossier', 'telephone')
    list_filter = ('civilite', 'est_actif')

@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'service', 'lit', 'date_entree', 'statut')
    list_filter = ('statut', 'type_admission', 'service')

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medecin', 'date_consultation', 'est_terminee')
    list_filter = ('est_terminee', 'medecin')

@admin.register(ConstanteVitale)
class ConstanteVitaleAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date_saisie', 'tension_arterielle', 'frequence_cardiaque')
    list_filter = ('date_saisie',)