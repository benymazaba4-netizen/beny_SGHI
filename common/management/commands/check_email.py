"""Diagnostic e-mail — Brevo (HTTPS) ou SMTP."""
import smtplib

from django.conf import settings
from django.core.mail import get_connection
from django.core.management.base import BaseCommand

from common.http_email import brevo_configured


class Command(BaseCommand):
    help = "Diagnostique la configuration e-mail (Brevo / SMTP)"

    def handle(self, *args, **options):
        self.stdout.write("=== Diagnostic e-mail SGHI ===")
        self.stdout.write(
            f"Brevo API     : {'OK (cle presente)' if brevo_configured() else 'non configure'}"
        )
        self.stdout.write(
            f"Brevo sender  : {getattr(settings, 'BREVO_SENDER_EMAIL', '') or '(vide)'}"
        )
        self.stdout.write(f"Backend SMTP  : {settings.EMAIL_BACKEND}")
        self.stdout.write(f"Serveur       : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        self.stdout.write(f"Expediteur    : {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"OTP bypass    : {getattr(settings, 'OTP_ALLOW_BYPASS', False)}")

        if brevo_configured():
            self.stdout.write(self.style.SUCCESS(
                "\nMode BREVO actif (HTTPS) — adapte a Render Free.\n"
                "Testez : python manage.py test_email --to benymazaba4@gmail.com"
            ))
            return

        self.stdout.write(self.style.WARNING(
            "\nBREVO_API_KEY absent — repli sur SMTP "
            "(bloque sur Render Free, ports 25/465/587)."
        ))

        if settings.EMAIL_HOST in ('127.0.0.1', 'localhost', 'mailpit'):
            self.stdout.write(self.style.WARNING(
                "Mode SMTP LOCAL — les e-mails ne partent pas sur Internet."
            ))
            return

        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            self.stdout.write(self.style.ERROR(
                "Identifiants SMTP manquants (EMAIL_HOST_USER / EMAIL_HOST_PASSWORD)."
            ))
            return

        self.stdout.write("\nTest connexion SMTP...")
        try:
            connection = get_connection(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                use_ssl=settings.EMAIL_USE_SSL,
                timeout=settings.EMAIL_TIMEOUT,
            )
            connection.open()
            connection.close()
            self.stdout.write(self.style.SUCCESS("Connexion SMTP OK."))
        except smtplib.SMTPAuthenticationError:
            self.stdout.write(self.style.ERROR("Authentification SMTP refusee."))
        except (TimeoutError, OSError, smtplib.SMTPException) as exc:
            self.stdout.write(self.style.ERROR(f"Erreur SMTP : {exc}"))
