from django.core.management.base import BaseCommand
from referentials.models import CodeCIM10

CIM10_COMMON = [
    ('A09', 'Diarrhée et gastro-entérite', 'Maladies infectieuses'),
    ('A15', 'Tuberculose respiratoire', 'Maladies infectieuses'),
    ('B20', 'Infection par le VIH', 'Maladies infectieuses'),
    ('E11', 'Diabète sucré de type 2', 'Maladies endocriniennes'),
    ('E14', 'Diabète sucré, sans précision', 'Maladies endocriniennes'),
    ('I10', 'Hypertension essentielle (primitive)', 'Maladies circulatoires'),
    ('I21', 'Infarctus aigu du myocarde', 'Maladies circulatoires'),
    ('I50', 'Insuffisance cardiaque', 'Maladies circulatoires'),
    ('J06', 'Infections aiguës des voies respiratoires supérieures', 'Maladies respiratoires'),
    ('J18', 'Pneumopathie, sans précision', 'Maladies respiratoires'),
    ('J45', 'Asthme', 'Maladies respiratoires'),
    ('K29', 'Gastrite et duodénite', 'Maladies digestives'),
    ('K80', 'Lithiase biliaire', 'Maladies digestives'),
    ('M54', 'Dorsalgie', 'Maladies musculo-squelettiques'),
    ('N18', 'Insuffisance rénale chronique', 'Maladies urogénitales'),
    ('N39', 'Autres affections de l\'appareil urinaire', 'Maladies urogénitales'),
    ('O80', 'Accouchement unique spontané', 'Grossesse et accouchement'),
    ('R50', 'Fièvre d\'origine inconnue', 'Symptômes généraux'),
    ('R51', 'Céphalée', 'Symptômes généraux'),
    ('S72', 'Fracture du fémur', 'Traumatismes'),
    ('Z00', 'Examen médical général', 'Facteurs influant sur l\'état de santé'),
    ('Z23', 'Nécessité de vaccination', 'Facteurs influant sur l\'état de santé'),
    ('Z51', 'Soins médicaux et traitements', 'Facteurs influant sur l\'état de santé'),
]


class Command(BaseCommand):
    help = 'Charge le référentiel CIM-10 de base'

    def handle(self, *args, **options):
        created = 0
        for code, libelle, chapitre in CIM10_COMMON:
            _, is_new = CodeCIM10.objects.update_or_create(
                code=code,
                defaults={'libelle': libelle, 'chapitre': chapitre, 'est_actif': True},
            )
            if is_new:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'CIM-10 : {created} nouveaux codes, {len(CIM10_COMMON)} au total'
        ))
