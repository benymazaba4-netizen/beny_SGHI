from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinical', '0006_admission_lit_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='numero_identite_national',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='numero_securite_sociale',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
