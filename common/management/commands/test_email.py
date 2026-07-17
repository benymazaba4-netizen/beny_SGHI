"""Envoie un e-mail de test (Brevo ou SMTP)."""
from django.conf import settings
from django.core.management.base import BaseCommand

from common.email_utils import send_notification
from common.http_email import brevo_configured


class Command(BaseCommand):
    help = "Envoie un e-mail de test via Brevo ou SMTP"

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            default='benymazaba4@gmail.com',
            help='Adresse destinataire',
        )

    def handle(self, *args, **options):
        to = options['to']
        mode = 'Brevo HTTPS' if brevo_configured() else f'SMTP ({settings.EMAIL_BACKEND})'
        self.stdout.write(f"Mode : {mode}")
        self.stdout.write(f"Expediteur Brevo : {getattr(settings, 'BREVO_SENDER_EMAIL', '') or '(defaut)'}")
        self.stdout.write(f"Envoi vers {to}...")

        ok = send_notification(
            to,
            "Test e-mail SGHI",
            "Cet e-mail confirme que la configuration Brevo/SMTP fonctionne.\n\n"
            "— SGHI ERP Medical",
        )

        if ok:
            self.stdout.write(self.style.SUCCESS("E-mail envoye avec succes."))
        else:
            self.stdout.write(self.style.ERROR(
                "Echec d'envoi — lancez : python manage.py check_email"
            ))
