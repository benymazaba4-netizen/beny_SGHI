# Generated manually for SGHI

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_utilisateur_mfa_backup_codes_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='JournalConnexion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('reussie', models.BooleanField(default=True)),
                ('date_connexion', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='journal_connexions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_connexion'],
            },
        ),
    ]
