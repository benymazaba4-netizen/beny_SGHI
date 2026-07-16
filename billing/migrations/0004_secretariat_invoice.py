# Generated manually for SecretariatInvoice workflow

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0001_initial'),
        ('clinical', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('billing', '0003_echeancepaiement'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecretariatInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('status', models.CharField(choices=[('PENDING', 'En attente'), ('PAID', 'Payé')], default='PENDING', max_length=20)),
                ('payment_method', models.CharField(blank=True, choices=[('CASH', 'Espèces'), ('MOBILE_MONEY', 'Mobile Money'), ('CARD', 'Carte')], max_length=20)),
                ('libelle', models.CharField(default='Frais de consultation', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('admission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='secretariat_invoices', to='clinical.admission')),
                ('consultation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='secretariat_invoices', to='clinical.consultation')),
                ('facture', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='secretariat_invoices', to='billing.facture')),
                ('paid_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='encaissements_secretariat', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='secretariat_invoices', to='clinical.patient')),
                ('rendez_vous', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='secretariat_invoices', to='appointments.rendezvous')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='secretariatinvoice',
            index=models.Index(fields=['status', 'created_at'], name='billing_sec_status_8f0c0d_idx'),
        ),
        migrations.AddIndex(
            model_name='secretariatinvoice',
            index=models.Index(fields=['patient', 'status'], name='billing_sec_patient_2a8f1e_idx'),
        ),
    ]
