# Generated migration to add photo fields to Patient

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinical', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='photo',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='photo_hash',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
