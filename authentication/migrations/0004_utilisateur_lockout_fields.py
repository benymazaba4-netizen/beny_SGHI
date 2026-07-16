from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_journalconnexion'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilisateur',
            name='failed_login_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='lockout_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
