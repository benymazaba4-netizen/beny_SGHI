"""Envoie un e-mail de test pour valider la configuration SMTP."""
from django.conf import settings
from django.core.management.base import BaseCommand

from common.email_utils import send_notification


class Command(BaseCommand):
    help = "Envoie un e-mail de test via la configuration SMTP active"

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            default='patient@example.com',
            help='Adresse destinataire (defaut: patient@example.com)',
        )

    def handle(self, *args, **options):
        to = options['to']
        self.stdout.write(f"Backend : {settings.EMAIL_BACKEND}")
        self.stdout.write(f"Serveur : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        self.stdout.write(f"TLS={settings.EMAIL_USE_TLS} SSL={settings.EMAIL_USE_SSL}")
        self.stdout.write(f"Expediteur : {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"Envoi reel : {getattr(settings, 'EMAIL_USE_REAL_SMTP', False)}")
        self.stdout.write(f"Envoi vers {to}...")

        ok = send_notification(
            to,
            "Test SMTP SGHI",
            "Cet e-mail confirme que la configuration SMTP fonctionne.\n\n"
            "Declencheurs automatiques :\n"
            "- Inscription patient\n"
            "- Confirmation de rendez-vous\n"
            "- Publication resultat de laboratoire\n\n"
            "— SGHI ERP Medical",
        )

        if ok:
            self.stdout.write(self.style.SUCCESS("E-mail envoye avec succes."))
            if settings.EMAIL_HOST in ('127.0.0.1', 'localhost', 'mailpit'):
                self.stdout.write(self.style.WARNING(
                    "Mode DEV : l'e-mail n'arrive PAS dans une vraie boite Gmail. "
                    "Consultez emails/outbox/ ou http://127.0.0.1:8025 (Mailpit)."
                ))
                self.stdout.write(
                    "Pour une vraie boite mail : .\\scripts\\configure-gmail-smtp.ps1 "
                    "-GmailAddress vous@gmail.com -AppPassword XXXX"
                )
        else:
            self.stdout.write(self.style.ERROR(
                "Echec d'envoi — lancez : python manage.py check_email"
            ))
