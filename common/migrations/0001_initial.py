# Generated migration for Upload model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(db_index=True, max_length=64, unique=True)),
                ('type_fichier', models.CharField(choices=[('IMAGE', 'Image'), ('PDF', 'PDF'), ('DOCUMENT', 'Document'), ('AUTRE', 'Autre')], max_length=20)),
                ('nom_original', models.CharField(max_length=255)),
                ('nom_stocke', models.CharField(db_index=True, max_length=255)),
                ('chemin_stockage', models.CharField(max_length=500)),
                ('mime_type', models.CharField(max_length=100)),
                ('taille_octets', models.BigIntegerField()),
                ('hash_sha256', models.CharField(db_index=True, max_length=64, unique=True)),
                ('date_upload', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_acces_dernier', models.DateTimeField(blank=True, null=True)),
                ('contenu_type', models.CharField(default='general', max_length=50)),
                ('contenu_id', models.PositiveIntegerField(blank=True, null=True)),
                ('est_actif', models.BooleanField(default=True)),
                ('est_supprime_logiquement', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('uploade_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploads', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_upload'],
            },
        ),
        migrations.AddIndex(
            model_name='upload',
            index=models.Index(fields=['hash_sha256'], name='common_uplo_hash_s_idx'),
        ),
        migrations.AddIndex(
            model_name='upload',
            index=models.Index(fields=['uploade_par', '-date_upload'], name='common_uplo_uploade__idx'),
        ),
        migrations.AddIndex(
            model_name='upload',
            index=models.Index(fields=['contenu_type', 'contenu_id'], name='common_uplo_contenu__idx'),
        ),
    ]
