"""Rappels médicamenteux — notification in-app + push FCM."""

from django.core.management.base import BaseCommand

from notifications.services import envoyer_rappels_medicaments


class Command(BaseCommand):
    help = 'Envoie les rappels médicamenteux du jour (prescriptions actives verrouillées).'

    def handle(self, *args, **options):
        stats = envoyer_rappels_medicaments()
        self.stdout.write(self.style.SUCCESS(
            f"Rappels médicaments : {stats['notifications']} envoyé(s), "
            f"{stats['ignorees']} déjà envoyé(s), {stats['traites']} ligne(s) traitée(s)."
        ))
