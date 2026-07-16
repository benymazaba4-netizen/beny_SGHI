from django.contrib import admin
from .models import Batiment, ServiceHospitalier, Chambre, Lit

@admin.register(Batiment)
class BatimentAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'nombre_etages')
    search_fields = ('nom', 'code')

@admin.register(ServiceHospitalier)
class ServiceHospitalierAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'batiment', 'type_service', 'est_actif')
    list_filter = ('type_service', 'est_actif', 'batiment')
    search_fields = ('nom', 'code')

@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ('numero', 'service', 'type_chambre', 'capacite_max')
    list_filter = ('type_chambre', 'service')
    search_fields = ('numero',)

@admin.register(Lit)
class LitAdmin(admin.ModelAdmin):
    list_display = ('numero', 'chambre', 'statut')
    list_filter = ('statut', 'chambre__service')
    search_fields = ('numero',)