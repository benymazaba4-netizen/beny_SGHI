"""Diagnostic SMTP — vérifie la configuration e-mail sans afficher le mot de passe."""
import smtplib
import ssl

from django.conf import settings
from django.core.mail import get_connection
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Diagnostique la configuration SMTP (Gmail, Mailpit, etc.)"

    def handle(self, *args, **options):
        self.stdout.write("=== Diagnostic e-mail SGHI ===")
        self.stdout.write(f"Backend      : {settings.EMAIL_BACKEND}")
        self.stdout.write(f"Serveur      : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        self.stdout.write(f"TLS/SSL      : {settings.EMAIL_USE_TLS} / {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"Utilisateur  : {settings.EMAIL_HOST_USER or '(vide)'}")
        self.stdout.write(f"Mot de passe : {'OK (renseigne)' if settings.EMAIL_HOST_PASSWORD else 'MANQUANT'}")
        self.stdout.write(f"Expediteur   : {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"Envoi reel   : {getattr(settings, 'EMAIL_USE_REAL_SMTP', False)}")
        self.stdout.write(f"OTP staff    : {getattr(settings, 'STAFF_OTP_EMAIL', '')}")

        if settings.EMAIL_HOST in ('127.0.0.1', 'localhost', 'mailpit'):
            self.stdout.write(self.style.WARNING(
                "\nMode SMTP LOCAL actif — les e-mails ne partent PAS vers Gmail.\n"
                "Modifiez .env : EMAIL_HOST=smtp.gmail.com puis redemarrez Django."
            ))
            return

        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            self.stdout.write(self.style.ERROR(
                "\nIdentifiants Gmail manquants dans .env "
                "(EMAIL_HOST_USER / EMAIL_HOST_PASSWORD)."
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
            self.stdout.write(self.style.SUCCESS("Connexion SMTP Gmail OK."))
            self.stdout.write(
                "Testez l'envoi : python manage.py test_email --to benymazaba4@gmail.com"
            )
        except smtplib.SMTPAuthenticationError:
            self.stdout.write(self.style.ERROR(
                "\nAuthentification Gmail REFUSEE.\n"
                "Google n'accepte pas le mot de passe du compte - il faut un "
                "mot de passe d'application (16 caracteres) :\n"
                "  https://myaccount.google.com/apppasswords\n"
                "Puis mettez-le dans .env : EMAIL_HOST_PASSWORD=..."
            ))
        except (TimeoutError, OSError, smtplib.SMTPException) as exc:
            self.stdout.write(self.style.ERROR(f"\nErreur SMTP : {exc}"))
