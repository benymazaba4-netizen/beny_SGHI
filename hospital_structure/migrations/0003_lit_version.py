from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospital_structure', '0002_lit_patient_actuel'),
    ]

    operations = [
        migrations.AddField(
            model_name='lit',
            name='version',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
