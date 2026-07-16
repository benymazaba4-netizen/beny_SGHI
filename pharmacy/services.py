from datetime import date

from django.db import transaction

from .models import Lot, Stock, MouvementStock, AlerteStock


class StockError(Exception):
    pass


def verifier_stock_disponible(medicament_id, quantite):
    """Vérifie que le stock est suffisant avant validation de prescription."""
    stock = Stock.objects.filter(medicament_id=medicament_id).first()
    disponible = stock.quantite_totale if stock else 0
    if disponible < quantite:
        from prescriptions.models import Medicament
        med = Medicament.objects.get(id=medicament_id)
        raise StockError(
            f"Stock insuffisant pour {med.nom} : "
            f"demandé {quantite}, disponible {disponible}"
        )
    return disponible


@transaction.atomic
def decrementer_stock(medicament_id, quantite, utilisateur_id, reference='', commentaire=''):
    """
    Décrémente le stock en FIFO (lots les plus proches de la péremption en premier).
    Crée les mouvements de sortie et met à jour les alertes.
    """
    lots = list(
        Lot.objects.select_for_update().filter(
            medicament_id=medicament_id,
            quantite_restante__gt=0,
            date_peremption__gte=date.today(),
        ).order_by('date_peremption')
    )

    reste = quantite
    mouvements = []

    for lot in lots:
        if reste <= 0:
            break
        prise = min(lot.quantite_restante, reste)
        lot.quantite_restante -= prise
        lot.save(update_fields=['quantite_restante'])

        mouvement = MouvementStock.objects.create(
            medicament_id=medicament_id,
            lot=lot,
            type_mouvement='SORTIE',
            quantite=prise,
            utilisateur_id=utilisateur_id,
            reference=reference,
            commentaire=commentaire or f"Sortie lot {lot.numero_lot}",
        )
        mouvements.append(mouvement)
        reste -= prise

    if reste > 0:
        raise StockError(
            f"Stock insuffisant pour le médicament #{medicament_id} : "
            f"manque {reste} unité(s)"
        )

    stock, _ = Stock.objects.get_or_create(medicament_id=medicament_id)
    stock.mettre_a_jour()
    _generer_alertes_stock(medicament_id, stock)
    return mouvements


def _generer_alertes_stock(medicament_id, stock):
    if stock.est_rupture():
        AlerteStock.objects.get_or_create(
            medicament_id=medicament_id,
            type_alerte='RUPTURE',
            est_resolue=False,
            defaults={'message': f"Rupture de stock : {stock.medicament.nom}"},
        )
    elif stock.est_alerte():
        AlerteStock.objects.get_or_create(
            medicament_id=medicament_id,
            type_alerte='SEUIL',
            est_resolue=False,
            defaults={
                'message': f"Stock faible : {stock.quantite_totale} unités restantes "
                           f"(seuil {stock.seuil_alerte})",
            },
        )


def creer_lot(data):
    """Crée un lot et initialise quantite_restante."""
    lot = Lot.objects.create(
        quantite_restante=data['quantite_initiale'],
        **data,
    )
    stock, _ = Stock.objects.get_or_create(medicament_id=data['medicament_id'])
    stock.mettre_a_jour()

    if lot.est_perime():
        AlerteStock.objects.create(
            medicament_id=data['medicament_id'],
            lot=lot,
            type_alerte='PEREMPTION',
            message=f"Le lot {lot.numero_lot} est périmé",
        )
    return lot
