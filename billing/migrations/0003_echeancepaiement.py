# Generated manually for SGHI

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_billing_engine'),
    ]

    operations = [
        migrations.CreateModel(
            name='EcheancePaiement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_echeance', models.DateField()),
                ('montant', models.DecimalField(decimal_places=2, max_digits=12)),
                ('est_payee', models.BooleanField(default=False)),
                ('date_paiement', models.DateTimeField(blank=True, null=True)),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('facture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='echeances', to='billing.facture')),
            ],
            options={
                'ordering': ['date_echeance'],
            },
        ),
    ]
