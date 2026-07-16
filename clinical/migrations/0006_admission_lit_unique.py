from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinical', '0005_plansoin'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='admission',
            constraint=models.UniqueConstraint(
                condition=models.Q(('statut', 'EN_COURS')),
                fields=('lit',),
                name='unique_admission_active_par_lit',
            ),
        ),
    ]
