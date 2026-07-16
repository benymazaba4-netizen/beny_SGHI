from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'
    verbose_name = 'Utilitaires Communs'

    def ready(self):
        import logging
        import os
        import sys
        from pathlib import Path

        from django.conf import settings

        # Recharger Django quand .env change (mot de passe Gmail, SMTP, etc.)
        if os.environ.get('RUN_MAIN') == 'true' and 'runserver' in sys.argv:
            try:
                from django.utils import autoreload
                env_file = Path(settings.BASE_DIR) / '.env'
                if env_file.exists():
                    autoreload.watch_for_reload(env_file)
            except Exception:
                pass

        if settings.EMAIL_USE_REAL_SMTP:
            logging.getLogger(__name__).info(
                "SMTP reel actif : %s:%s -> %s",
                settings.EMAIL_HOST,
                settings.EMAIL_PORT,
                settings.EMAIL_HOST_USER,
            )
        elif settings.EMAIL_HOST in ('127.0.0.1', 'localhost', 'mailpit'):
            logging.getLogger(__name__).warning(
                "SMTP local (%s) — les e-mails ne partent pas vers une vraie boite mail.",
                settings.EMAIL_HOST,
            )
