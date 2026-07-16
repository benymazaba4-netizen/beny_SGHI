"""Crée le super-administrateur SGHI (compte hors interface Django /admin/)."""
import getpass

from django.core.management.base import BaseCommand, CommandError

from authentication.models import Utilisateur

VALID_ROLES = {c[0] for c in Utilisateur.ROLE_CHOICES}


class Command(BaseCommand):
    help = "Crée ou met à jour le super-administrateur SGHI (role ADMIN, is_superuser=True)"

    def add_arguments(self, parser):
        parser.add_argument('--username', default='superadmin', help='Identifiant (défaut: superadmin)')
        parser.add_argument('--email', default='', help='E-mail pour OTP et notifications')
        parser.add_argument('--password', default='', help='Mot de passe (sinon demandé interactivement)')
        parser.add_argument('--first-name', default='Super', dest='first_name')
        parser.add_argument('--last-name', default='Administrateur', dest='last_name')
        parser.add_argument('--matricule', default='SUPER001', help='Matricule unique')

    def handle(self, *args, **options):
        username = (options['username'] or '').strip()
        email = (options['email'] or '').strip()
        password = options['password'] or ''
        first_name = options['first_name']
        last_name = options['last_name']
        matricule = (options['matricule'] or '').strip() or None

        if not username:
            raise CommandError('Le nom d\'utilisateur est requis.')

        if not password:
            password = getpass.getpass('Mot de passe superadmin : ')
            confirm = getpass.getpass('Confirmer le mot de passe : ')
            if password != confirm:
                raise CommandError('Les mots de passe ne correspondent pas.')
        if len(password) < 10:
            raise CommandError('Le mot de passe doit contenir au moins 10 caractères.')

        user, created = Utilisateur.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'role': 'ADMIN',
                'matricule': matricule,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )

        if not created:
            user.first_name = first_name
            user.last_name = last_name
            if email:
                user.email = email
            user.role = 'ADMIN'
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            if matricule:
                user.matricule = matricule

        user.set_password(password)
        user.save()

        action = 'créé' if created else 'mis à jour'
        self.stdout.write(self.style.SUCCESS(
            f"Super-admin {action} : {username} (role ADMIN, is_superuser=True)"
        ))
        if email:
            self.stdout.write(f"  E-mail OTP : {email}")
        self.stdout.write(
            "  Connexion : portail web /login → tableau de bord admin\n"
            "  Django /admin/ : désactivé par défaut (DJANGO_ADMIN_ENABLED=False)"
        )
