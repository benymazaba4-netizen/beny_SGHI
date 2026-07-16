"""Envoie les rappels de rendez-vous (24 h avant) — notification + e-mail."""
from django.core.management.base import BaseCommand

from notifications.services import envoyer_rappels_rdv


class Command(BaseCommand):
    help = "Envoie les rappels RDV (in-app, push, e-mail) pour les rendez-vous dans ~24 h"

    def handle(self, *args, **options):
        stats = envoyer_rappels_rdv()

        if stats['traites'] == 0:
            self.stdout.write(self.style.WARNING('Aucun rendez-vous à rappeler.'))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Rappels envoyés : {stats['traites']} RDV — "
                f"{stats['notifications']} notification(s), "
                f"{stats['emails']} e-mail(s), "
                f"{stats['sans_email']} sans e-mail."
            )
        )
