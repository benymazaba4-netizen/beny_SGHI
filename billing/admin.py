from django.contrib import admin
from .models import Facture, LigneFacture, TransactionPaiement, Assurance, PriseEnChargeAssurance, JournalComptable

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero_facture', 'patient', 'montant_patient', 'montant_paye', 'montant_restant', 'statut')
    list_filter = ('statut', 'date_emission')
    search_fields = ('numero_facture', 'patient__nom', 'patient__prenom')

@admin.register(LigneFacture)
class LigneFactureAdmin(admin.ModelAdmin):
    list_display = ('facture', 'description', 'quantite', 'montant')
    list_filter = ('type_ligne',)

@admin.register(TransactionPaiement)
class TransactionPaiementAdmin(admin.ModelAdmin):
    list_display = ('facture', 'mode_paiement', 'montant', 'statut', 'date_transaction')
    list_filter = ('mode_paiement', 'statut', 'date_transaction')

@admin.register(Assurance)
class AssuranceAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'taux_prise_en_charge', 'est_actif')
    list_filter = ('est_actif',)

@admin.register(PriseEnChargeAssurance)
class PriseEnChargeAssuranceAdmin(admin.ModelAdmin):
    list_display = ('patient', 'assurance', 'numero_contrat', 'est_active')
    list_filter = ('est_active', 'assurance')


@admin.register(JournalComptable)
class JournalComptableAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'facture', 'type_operation', 'montant', 'utilisateur')
    list_filter = ('type_operation', 'timestamp')
    readonly_fields = (
        'facture', 'type_operation', 'montant', 'description',
        'utilisateur', 'timestamp', 'hash_signature', 'previous_hash',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False