"""Envoie une notification push de test à un utilisateur."""
from django.core.management.base import BaseCommand

from authentication.models import Utilisateur
from notifications.services import creer_notification, envoyer_push


class Command(BaseCommand):
    help = "Envoie une notification push de test FCM à un utilisateur"

    def add_arguments(self, parser):
        parser.add_argument('--username', default='patient', help='Nom utilisateur cible')
        parser.add_argument('--titre', default='Test SGHI Push', help='Titre de la notification')
        parser.add_argument('--corps', default='Notification push de test depuis SGHI ERP.', help='Corps du message')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = Utilisateur.objects.get(username=username)
        except Utilisateur.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Utilisateur '{username}' introuvable."))
            return

        creer_notification(user, 'GENERAL', options['titre'], options['corps'])
        sent = envoyer_push(user, options['titre'], options['corps'])

        if sent:
            self.stdout.write(self.style.SUCCESS(f"Push envoyé à {username}."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Notification in-app créée pour {username}. "
                    f"Push FCM non envoyé — vérifiez FCM_SERVER_KEY et token appareil."
                )
            )
