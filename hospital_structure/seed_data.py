"""Données de démonstration — structure hospitalière (services, chambres, lits)."""

from decimal import Decimal


def seed_hospital_structure(stdout=None):
    from hospital_structure.models import Batiment, Chambre, Lit, ServiceHospitalier

    structure = [
        {
            "batiment": {
                "nom": "Pôle médical principal",
                "code": "BAT-A",
                "adresse": "Avenue de l'Hôpital, Kinshasa",
                "nombre_etages": 4,
            },
            "services": [
                {
                    "nom": "Médecine interne",
                    "code": "MED-INT",
                    "type_service": "MEDICAL",
                    "etage": 2,
                    "chambres": [
                        {"numero": "201", "type_chambre": "DOUBLE", "capacite_max": 2, "prix": 25000, "lits": ["1", "2"]},
                        {"numero": "202", "type_chambre": "DOUBLE", "capacite_max": 2, "prix": 25000, "lits": ["1", "2"]},
                        {"numero": "203", "type_chambre": "INDIVIDUELLE", "capacite_max": 1, "prix": 35000, "lits": ["1"]},
                    ],
                },
                {
                    "nom": "Chirurgie générale",
                    "code": "CHIR",
                    "type_service": "CHIRURGICAL",
                    "etage": 3,
                    "chambres": [
                        {"numero": "301", "type_chambre": "DOUBLE", "capacite_max": 2, "prix": 30000, "lits": ["1", "2"]},
                        {"numero": "302", "type_chambre": "TRIPLE", "capacite_max": 3, "prix": 22000, "lits": ["1", "2", "3"]},
                    ],
                },
                {
                    "nom": "Pédiatrie",
                    "code": "PED",
                    "type_service": "MEDICAL",
                    "etage": 1,
                    "chambres": [
                        {"numero": "101", "type_chambre": "DOUBLE", "capacite_max": 2, "prix": 20000, "lits": ["1", "2"]},
                        {"numero": "102", "type_chambre": "DOUBLE", "capacite_max": 2, "prix": 20000, "lits": ["1", "2"]},
                    ],
                },
            ],
        },
        {
            "batiment": {
                "nom": "Urgences & soins critiques",
                "code": "BAT-URG",
                "adresse": "Entrée des urgences, Kinshasa",
                "nombre_etages": 2,
            },
            "services": [
                {
                    "nom": "Urgences",
                    "code": "URG",
                    "type_service": "MEDICAL",
                    "etage": 0,
                    "chambres": [
                        {"numero": "U01", "type_chambre": "SALLE_COMMUNE", "capacite_max": 4, "prix": 15000, "lits": ["1", "2", "3", "4"]},
                        {"numero": "U02", "type_chambre": "DOUBLE", "capacite_max": 2, "prix": 18000, "lits": ["1", "2"]},
                    ],
                },
                {
                    "nom": "Réanimation",
                    "code": "REA",
                    "type_service": "MEDICAL",
                    "etage": 1,
                    "chambres": [
                        {"numero": "R01", "type_chambre": "REANIMATION", "capacite_max": 2, "prix": 45000, "lits": ["1", "2"]},
                    ],
                },
            ],
        },
    ]

    for bloc in structure:
        bat, _ = Batiment.objects.get_or_create(code=bloc["batiment"]["code"], defaults=bloc["batiment"])
        for svc_data in bloc["services"]:
            chambres_data = svc_data.pop("chambres")
            svc, _ = ServiceHospitalier.objects.get_or_create(
                code=svc_data["code"],
                defaults={**svc_data, "batiment": bat, "est_actif": True},
            )
            if not svc.est_actif:
                svc.est_actif = True
                svc.save(update_fields=["est_actif"])
            for ch_data in chambres_data:
                lits_nums = ch_data.pop("lits")
                prix = ch_data.pop("prix")
                ch, _ = Chambre.objects.get_or_create(
                    service=svc,
                    numero=ch_data["numero"],
                    defaults={**ch_data, "prix_par_jour": Decimal(str(prix)), "est_actif": True},
                )
                for lit_num in lits_nums:
                    Lit.objects.get_or_create(chambre=ch, numero=lit_num, defaults={"statut": "LIBRE"})

    nb_services = ServiceHospitalier.objects.filter(est_actif=True).count()
    nb_lits = Lit.objects.filter(statut="LIBRE").count()
    if stdout:
        stdout.write(f"Structure hospitalière : {nb_services} services, {nb_lits} lits libres.")
    return nb_services, nb_lits
