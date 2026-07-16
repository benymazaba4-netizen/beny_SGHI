from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from authentication.models import Utilisateur
from clinical.models import Patient

DEMO_PASSWORD = "Demo2026!"

DEMO_OTP_EMAIL = "benymazaba4@gmail.com"

DEMO_USERS = [
    {"username": "admin", "role": "ADMIN", "first_name": "Admin", "last_name": "SGHI",
     "email": DEMO_OTP_EMAIL, "is_staff": True, "is_superuser": False, "matricule": "ADM001"},
    {"username": "superadmin", "role": "ADMIN", "first_name": "Super", "last_name": "Administrateur",
     "email": DEMO_OTP_EMAIL, "is_staff": True, "is_superuser": True, "matricule": "SUPER001"},
    {"username": "medecin", "role": "MEDECIN", "first_name": "Jean", "last_name": "Kabila",
     "email": DEMO_OTP_EMAIL, "matricule": "MED001"},
    {"username": "medecin2", "role": "MEDECIN", "first_name": "Anne", "last_name": "Mwamba",
     "email": DEMO_OTP_EMAIL, "matricule": "MED002"},
    {"username": "infirmier", "role": "INFIRMIER", "first_name": "Marie", "last_name": "Mukendi",
     "email": DEMO_OTP_EMAIL, "matricule": "INF001"},
    {"username": "biologiste", "role": "BIOLOGISTE", "first_name": "Paul", "last_name": "Tshilombo",
     "email": DEMO_OTP_EMAIL, "matricule": "BIO001"},
    {"username": "pharmacien", "role": "PHARMACIEN", "first_name": "Grace", "last_name": "Ilunga",
     "email": DEMO_OTP_EMAIL, "matricule": "PHA001"},
    {"username": "comptable", "role": "COMPTABLE", "first_name": "Eric", "last_name": "Mbuyi",
     "email": DEMO_OTP_EMAIL, "matricule": "CPT001"},
    {"username": "secretaire", "role": "SECRETAIRE", "first_name": "Sarah", "last_name": "Ngoy",
     "email": DEMO_OTP_EMAIL, "matricule": "SEC001"},
    {"username": "patient", "role": "PATIENT", "first_name": "Joseph", "last_name": "Kabongo",
     "email": DEMO_OTP_EMAIL, "matricule": "PAT001"},
]


class Command(BaseCommand):
    help = "Crée l'environnement de démonstration complet SGHI (utilisateurs + workflow métier)."

    def handle(self, *args, **options):
        created = updated = 0
        for data in DEMO_USERS:
            username = data["username"]
            defaults = {k: v for k, v in data.items() if k != "username"}
            user, was_created = Utilisateur.objects.get_or_create(username=username, defaults=defaults)
            if was_created:
                user.set_password(DEMO_PASSWORD)
                user.save()
                created += 1
            else:
                for key, value in defaults.items():
                    setattr(user, key, value)
                user.set_password(DEMO_PASSWORD)
                user.save()
                updated += 1

            if user.role == "PATIENT":
                patient, _ = Patient.objects.get_or_create(
                    utilisateur=user,
                    defaults={
                        "nom": user.last_name,
                        "prenom": user.first_name,
                        "date_naissance": date(1990, 1, 15),
                        "telephone": "+243900000001",
                        "adresse": "Kinshasa, RDC",
                        "consentement_donnees": True,
                        "numero_identite_national": "CD-DEMO-1990-001",
                        "numero_securite_sociale": "SS-DEMO-001",
                    },
                )
                patient.numero_identite_national = "CD-DEMO-1990-001"
                patient.numero_securite_sociale = "SS-DEMO-001"
                patient.email = user.email or ""
                patient.save()

        self._ensure_hospital_structure()
        self._ensure_personnel()
        self._ensure_pharmacie()
        self._ensure_laboratoire()
        self._ensure_workflow_clinique()
        self._ensure_labo_workflow()
        self._ensure_demo_rdv()
        self._ensure_demo_facture()

        self.stdout.write(self.style.SUCCESS(
            f"Demo SGHI prete ({created} crees, {updated} mis a jour). Mot de passe : {DEMO_PASSWORD}"
        ))
        for data in DEMO_USERS:
            self.stdout.write(f"  {data['username']:12} -> {data['role']}")
        self.stdout.write(self.style.WARNING(
            "\nComptes administrateurs :\n"
            "  admin      -> Administrateur (gestion courante, ne peut pas modifier le super-admin)\n"
            "  superadmin -> Super-administrateur (droits complets sur tous les comptes)"
        ))

    def _ensure_hospital_structure(self):
        from hospital_structure.seed_data import seed_hospital_structure
        seed_hospital_structure(stdout=self.stdout)

    def _ensure_personnel(self):
        from hospital_structure.models import ServiceHospitalier
        from rh.models import Personnel, PlanningGarde

        mapping = {
            "medecin": ("MEDECIN", "MED001"),
            "medecin2": ("MEDECIN", "MED002"),
            "infirmier": ("INFIRMIER", "INF001"),
            "biologiste": ("BIOLOGISTE", "BIO001"),
            "pharmacien": ("PHARMACIEN", "PHA001"),
            "secretaire": ("SECRETAIRE", "SEC001"),
            "comptable": ("COMPTABLE", "CPT001"),
        }
        service = ServiceHospitalier.objects.filter(code="MED-INT").first()
        admin = Utilisateur.objects.filter(username="admin").first()
        now = timezone.now()

        for username, (ptype, matricule) in mapping.items():
            user = Utilisateur.objects.filter(username=username).first()
            if not user:
                continue
            Personnel.objects.get_or_create(
                utilisateur=user,
                defaults={
                    "type_personnel": ptype,
                    "matricule": matricule,
                    "service": service,
                    "date_embauche": date(2020, 1, 1),
                    "est_actif": True,
                },
            )

        medecin_pers = Personnel.objects.filter(matricule="MED001").first()
        if medecin_pers and service and not PlanningGarde.objects.exists():
            PlanningGarde.objects.create(
                personnel=medecin_pers,
                service=service,
                type_garde="JOUR",
                date_debut=now,
                date_fin=now + timedelta(hours=12),
                planifie_par=admin,
            )
            self.stdout.write("  Planning de garde démo créé.")

    def _ensure_pharmacie(self):
        from datetime import date as dt_date
        from prescriptions.models import Medicament
        from pharmacy.models import Lot, Stock

        meds = [
            ("PARA500", "Paracétamol 500mg", "COMPRIME", "500", 150),
            ("AMOX500", "Amoxicilline 500mg", "COMPRIME", "500", 200),
            ("SF09", "Sérum physiologique 0,9%", "PERFUSION", "500ml", 80),
        ]
        for code, nom, forme, dosage, prix in meds:
            med, _ = Medicament.objects.get_or_create(
                code=code,
                defaults={
                    "nom": nom, "forme": forme, "dosage": dosage,
                    "prix_unitaire": Decimal(str(prix)), "est_actif": True,
                },
            )
            stock, _ = Stock.objects.get_or_create(medicament=med, defaults={"quantite_totale": 0, "seuil_alerte": 20})
            if not Lot.objects.filter(medicament=med).exists():
                lot = Lot.objects.create(
                    medicament=med,
                    numero_lot=f"LOT-{code}-2026",
                    quantite_initiale=500,
                    quantite_restante=500,
                    date_fabrication=dt_date(2025, 6, 1),
                    date_peremption=dt_date(2027, 6, 1),
                    prix_achat=Decimal(str(prix * 0.6)),
                    fournisseur="Pharma RDC",
                )
                stock.mettre_a_jour()
        self.stdout.write("  Pharmacie : 3 médicaments + stocks.")

    def _ensure_laboratoire(self):
        from laboratory.models import ExamenType

        examens = [
            ("NFS", "Numération formule sanguine", "HEMATOLOGIE", 15000),
            ("GLY", "Glycémie à jeun", "BIOCHIMIE", 8000),
            ("CRP", "Protéine C réactive", "BIOCHIMIE", 12000),
            ("UREE", "Urée sanguine", "BIOCHIMIE", 7000),
            ("HIV", "Test VIH", "IMMUNOLOGIE", 25000),
        ]
        for code, nom, cat, prix in examens:
            ExamenType.objects.get_or_create(
                code=code,
                defaults={"nom": nom, "categorie": cat, "prix": Decimal(str(prix)), "est_actif": True},
            )
        self.stdout.write("  Laboratoire : 5 types d'examens.")

    def _ensure_workflow_clinique(self):
        from clinical.models import Admission, Consultation, ConstanteVitale
        from clinical.services import creer_admission
        from hospital_structure.models import Lit, ServiceHospitalier
        from laboratory.models import DemandeExamen, ExamenType
        from prescriptions.models import LignePrescription, Medicament, Prescription

        patient = Patient.objects.filter(utilisateur__username="patient").first()
        medecin = Utilisateur.objects.filter(username="medecin").first()
        infirmier = Utilisateur.objects.filter(username="infirmier").first()
        service = ServiceHospitalier.objects.filter(code="MED-INT").first()
        lit = Lit.objects.filter(chambre__service=service, statut="LIBRE").first()

        if not all([patient, medecin, service, lit]):
            self.stdout.write(self.style.WARNING("  Workflow clinique : données structure manquantes."))
            return

        admission = patient.admission_active()
        if not admission:
            admission = creer_admission(
                patient_id=patient.id,
                service_id=service.id,
                lit_id=lit.id,
                medecin_referent_id=medecin.id,
                motif_hospitalisation="Fièvre persistante et asthénie — démonstration",
                date_previsionnelle_sortie=date.today() + timedelta(days=5),
            )
            self.stdout.write(f"  Admission active créée (lit {lit.numero}).")

        if not Consultation.objects.filter(patient=patient).exists():
            consult = Consultation.objects.create(
                patient=patient,
                medecin=medecin,
                service=service,
                admission=admission,
                motif="Consultation de suivi hospitalier",
                diagnostic="Syndrome infectieux à explorer",
                diagnostic_cim10="A09",
                est_terminee=True,
            )
            para = Medicament.objects.filter(code="PARA500").first()
            presc = Prescription.objects.create(
                patient=patient,
                medecin=medecin,
                consultation=consult,
                date_debut=date.today(),
                date_fin=date.today() + timedelta(days=7),
                statut="VALIDE",
                est_verrouillee=False,
                instructions="Prendre après les repas",
            )
            if para:
                LignePrescription.objects.create(
                    prescription=presc,
                    medicament=para,
                    quantite_prescitee=21,
                    frequence="3x par jour",
                    duree_jours=7,
                    instructions_specifiques="500mg après les repas",
                )
                presc.est_verrouillee = True
                presc.save(update_fields=["est_verrouillee"])
            nfs = ExamenType.objects.filter(code="NFS").first()
            if nfs:
                DemandeExamen.objects.get_or_create(
                    patient=patient,
                    consultation=consult,
                    examen_type=nfs,
                    medecin_prescripteur=medecin,
                    defaults={"statut": "PRESCRIT", "urgence": False},
                )
            self.stdout.write("  Workflow : consultation + prescription + demande NFS créés.")

        consult = Consultation.objects.filter(patient=patient).first()
        if consult and infirmier and admission:
            ConstanteVitale.objects.get_or_create(
                patient=patient,
                admission=admission,
                infirmier=infirmier,
                frequence_cardiaque=78,
                defaults={
                    "tension_arterielle": "120/80",
                    "temperature": Decimal("37.2"),
                    "saturation_o2": 98,
                },
            )
            for hours_ago, ta, fc, temp, spo2 in [
                (6, "118/78", 76, Decimal("37.0"), 97),
                (12, "122/82", 80, Decimal("37.4"), 98),
            ]:
                ts = timezone.now() - timedelta(hours=hours_ago)
                if not ConstanteVitale.objects.filter(
                    patient=patient, admission=admission, frequence_cardiaque=fc,
                ).exists():
                    ConstanteVitale.objects.create(
                        patient=patient,
                        admission=admission,
                        infirmier=infirmier,
                        tension_arterielle=ta,
                        frequence_cardiaque=fc,
                        temperature=temp,
                        saturation_o2=spo2,
                        date_saisie=ts,
                    )

            from clinical.models import PlanSoin
            presc_obj = Prescription.objects.filter(patient=patient, consultation=consult).first()
            if presc_obj and not PlanSoin.objects.filter(patient=patient, admission=admission).exists():
                PlanSoin.objects.create(
                    patient=patient,
                    admission=admission,
                    prescription=presc_obj,
                    infirmier_responsable=infirmier,
                    medecin_prescripteur=medecin,
                    titre="Surveillance post-fébrile",
                    description="Contrôle température 3x/jour, hydratation, repos.",
                    frequence="3x par jour",
                    date_debut=date.today(),
                    date_fin=date.today() + timedelta(days=5),
                    statut="ACTIF",
                )
            self.stdout.write("  Workflow : constantes + plan de soins prêts.")

    def _ensure_labo_workflow(self):
        """Prepare LIS demo: NFS en attente validation + CRP valide/publie pour le patient."""
        from clinical.models import Consultation
        from laboratory.models import DemandeExamen, ExamenType
        from laboratory.services import (
            enregistrer_prelevement, affecter_demande,
            saisir_resultat, valider_et_publier,
        )

        patient = Patient.objects.filter(utilisateur__username="patient").first()
        medecin = Utilisateur.objects.filter(username="medecin").first()
        infirmier = Utilisateur.objects.filter(username="infirmier").first()
        biologiste = Utilisateur.objects.filter(username="biologiste").first()
        consult = Consultation.objects.filter(patient=patient).first()

        if not all([patient, medecin, infirmier, biologiste, consult]):
            self.stdout.write(self.style.WARNING("  Labo workflow : donnees manquantes."))
            return

        nfs = ExamenType.objects.filter(code="NFS").first()
        if nfs:
            demande_nfs = DemandeExamen.objects.filter(
                patient=patient, examen_type=nfs, statut="VALIDATION",
            ).first()
            if not demande_nfs:
                demande_nfs = DemandeExamen.objects.create(
                    patient=patient,
                    consultation=consult,
                    examen_type=nfs,
                    medecin_prescripteur=medecin,
                    statut="PRESCRIT",
                    notes_prescripteur="NFS démo — à valider en live",
                )
                enregistrer_prelevement(demande_nfs.id, infirmier.id, {"type_prelevement": "SANG"})
                affecter_demande(demande_nfs.id, biologiste.id)
                saisir_resultat(
                    demande_nfs.id, biologiste.id,
                    '{"gb": 7.2, "hb": 13.5, "plt": 250}',
                    "NFS dans les normes de reference",
                )
            self.stdout.write("  Labo : NFS en attente de validation (biologiste).")

        crp = ExamenType.objects.filter(code="CRP").first()
        if crp and not DemandeExamen.objects.filter(patient=patient, examen_type=crp, statut="VALIDE").exists():
            demande_crp = DemandeExamen.objects.create(
                patient=patient,
                consultation=consult,
                examen_type=crp,
                medecin_prescripteur=medecin,
                statut="PRESCRIT",
            )
            enregistrer_prelevement(demande_crp.id, infirmier.id, {"type_prelevement": "SANG"})
            affecter_demande(demande_crp.id, biologiste.id)
            saisir_resultat(
                demande_crp.id, biologiste.id,
                '{"crp": 4.2, "unite": "mg/L"}',
                "CRP legerement elevee",
            )
            demande_crp.refresh_from_db()
            try:
                valider_et_publier(demande_crp.resultat.id, biologiste.id)
                self.stdout.write("  Labo : CRP valide et publie (visible patient).")
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  Labo CRP : validation partielle ({exc})"))

    def _ensure_demo_rdv(self):
        from appointments.models import DisponibiliteMedecin, RendezVous
        from hospital_structure.models import ServiceHospitalier

        patient = Patient.objects.filter(utilisateur__username="patient").first()
        medecin = Utilisateur.objects.filter(username="medecin").first()
        secretaire = Utilisateur.objects.filter(username="secretaire").first()
        service = ServiceHospitalier.objects.filter(code="MED-INT").first()
        if not all([patient, medecin, service]):
            return

        now = timezone.now()
        if not DisponibiliteMedecin.objects.filter(medecin=medecin, service=service).exists():
            debut = now + timedelta(days=2)
            DisponibiliteMedecin.objects.create(
                medecin=medecin,
                service=service,
                date_debut=debut.replace(hour=8, minute=0, second=0, microsecond=0),
                date_fin=debut.replace(hour=12, minute=0, second=0, microsecond=0),
                duree_creneau_minutes=30,
            )
            self.stdout.write("  RDV : disponibilités médecin créées.")

        if not RendezVous.objects.filter(patient=patient, statut__in=["PLANIFIE", "CONFIRME"]).exists():
            rdv_date = now + timedelta(days=3)
            rdv_date = rdv_date.replace(hour=10, minute=0, second=0, microsecond=0)
            dispo = DisponibiliteMedecin.objects.filter(medecin=medecin, service=service).first()
            RendezVous.objects.create(
                patient=patient,
                medecin=medecin,
                service=service,
                disponibilite=dispo,
                date_heure=rdv_date,
                duree_minutes=30,
                motif="Contrôle post-hospitalisation — démonstration",
                statut="CONFIRME",
                cree_par=secretaire or medecin,
            )
            self.stdout.write(f"  RDV : rendez-vous patient le {rdv_date.strftime('%d/%m/%Y %H:%M')}.")

    def _ensure_demo_facture(self):
        from billing.models import Facture, LigneFacture
        from billing.services import emettre_facture

        patient = Patient.objects.filter(utilisateur__username="patient").first()
        if not patient:
            return
        comptable = Utilisateur.objects.filter(username="comptable").first()
        if not comptable:
            return

        facture = Facture.objects.filter(
            patient=patient,
            statut__in=["EMISE", "PARTIELLE", "IMPAYEE", "BROUILLON"],
        ).order_by("-date_emission").first()

        if facture and facture.fichier_pdf and facture.montant_paye == 0:
            self.stdout.write(f"  Facture démo : {facture.numero_facture} ({facture.montant_restant} FCFA restants, PDF OK)")
            return

        if facture:
            facture.delete()

        facture = Facture.objects.create(
            patient=patient,
            statut="BROUILLON",
            emise_par=comptable,
            notes="Facture démonstration SGHI",
        )
        LigneFacture.objects.create(
            facture=facture,
            type_ligne="CONSULTATION",
            description="Consultation générale — démonstration",
            quantite=1,
            prix_unitaire=Decimal("50000"),
        )
        facture.recalculer_montants()
        try:
            facture = emettre_facture(facture.id, comptable.id)
            self.stdout.write(
                f"  Facture démo : {facture.numero_facture} "
                f"({facture.montant_restant} FCFA impayés, PDF généré)"
            )
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  Facture démo : émission partielle ({exc})"))
