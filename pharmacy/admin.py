from django.contrib import admin
from .models import Lot, Stock, MouvementStock, AlerteStock

@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ('medicament', 'numero_lot', 'quantite_restante', 'date_peremption', 'est_perime')
    list_filter = ('date_peremption', 'medicament')
    search_fields = ('numero_lot', 'medicament__nom')
    
    def est_perime(self, obj):
        return obj.est_perime()
    est_perime.boolean = True

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('medicament', 'quantite_totale', 'seuil_alerte', 'est_rupture', 'est_alerte')
    list_filter = ('medicament',)
    
    def est_rupture(self, obj):
        return obj.est_rupture()
    est_rupture.boolean = True
    
    def est_alerte(self, obj):
        return obj.est_alerte()
    est_alerte.boolean = True

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('medicament', 'type_mouvement', 'quantite', 'date_mouvement', 'utilisateur')
    list_filter = ('type_mouvement', 'date_mouvement')
    search_fields = ('medicament__nom', 'reference')

@admin.register(AlerteStock)
class AlerteStockAdmin(admin.ModelAdmin):
    list_display = ('medicament', 'type_alerte', 'date_creation', 'est_lue', 'est_resolue')
    list_filter = ('type_alerte', 'est_lue', 'est_resolue')