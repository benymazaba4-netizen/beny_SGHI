from django.contrib import admin
from .models import Medicament, Prescription, LignePrescription, AdministrationMedicament, AlerteDoseOmise

@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'forme', 'dosage', 'prix_unitaire')
    search_fields = ('code', 'nom')
    list_filter = ('forme', 'est_actif')

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'medecin', 'date_prescription', 'statut', 'est_verrouillee')
    list_filter = ('statut', 'est_verrouillee', 'date_prescription')
    search_fields = ('patient__nom', 'patient__prenom')
    readonly_fields = ('signature_electronique', 'date_validation', 'est_verrouillee')

@admin.register(LignePrescription)
class LignePrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'medicament', 'quantite_prescitee', 'quantite_administree')
    list_filter = ('medicament',)

@admin.register(AdministrationMedicament)
class AdministrationMedicamentAdmin(admin.ModelAdmin):
    list_display = ('ligne_prescription', 'infirmier', 'date_administration', 'quantite_administree')
    list_filter = ('date_administration', 'est_refuse')


@admin.register(AlerteDoseOmise)
class AlerteDoseOmiseAdmin(admin.ModelAdmin):
    list_display = ('ligne_prescription', 'date_alerte', 'est_traitee')
    list_filter = ('est_traitee', 'date_alerte')