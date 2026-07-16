"""

Utilitaires concurrence SQLite / PostgreSQL.



SQLite : select_for_update() est autorisé mais ne verrouille pas réellement.

La protection repose sur transaction.atomic() + UPDATE conditionnel + contraintes uniques.



PostgreSQL : select_for_update() effectif + mêmes garde-fous applicatifs.

"""

from django.db import connection





def is_postgresql() -> bool:

    return connection.vendor == 'postgresql'





def is_sqlite() -> bool:

    return connection.vendor == 'sqlite'





def lock_for_update(queryset):

    """Applique select_for_update sur PostgreSQL ; queryset inchangé sur SQLite."""

    if is_postgresql():

        return queryset.select_for_update()

    return queryset





def get_locked(model, **lookup):

    """Récupère une ligne avec verrou pessimiste sur PostgreSQL."""

    qs = model.objects.filter(**lookup)

    if is_postgresql():

        return qs.select_for_update().get()

    return qs.get()


