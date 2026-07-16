from django.db import migrations


def seed_structure(apps, schema_editor):
    """Seed compatible SQLite — modèles historiques pour le contrôle d'idempotence."""
    ServiceHospitalier = apps.get_model('hospital_structure', 'ServiceHospitalier')
    if ServiceHospitalier.objects.filter(est_actif=True).count() >= 5:
        return
    from hospital_structure.seed_data import seed_hospital_structure
    seed_hospital_structure()


class Migration(migrations.Migration):

    dependencies = [
        ('hospital_structure', '0003_lit_version'),
        ('clinical', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_structure, migrations.RunPython.noop),
    ]
