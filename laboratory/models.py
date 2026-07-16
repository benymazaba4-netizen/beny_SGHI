from django.db import models
from django.utils import timezone
from authentication.models import Utilisateur
from clinical.models import Patient, Consultation


class LISError(Exception):
    pass


class ExamenType(models.Model):
    """Type d'examen de laboratoire (ex: NFS, Glycémie, Bilan hépatique)"""

    CATEGORIES = (
        ('HEMATOLOGIE', 'Hématologie'),
        ('BIOCHIMIE', 'Biochimie'),
        ('MICROBIOLOGIE', 'Microbiologie'),
        ('IMMUNOLOGIE', 'Immunologie'),
        ('ANATOMOPATHOLOGIE', 'Anatomopathologie'),
        ('AUTRE', 'Autre'),
    )

    code = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    categorie = models.CharField(max_length=30, choices=CATEGORIES, default='AUTRE')
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duree_traitement_heures = models.IntegerField(default=24, help_text="Délai moyen de rendu")

    jeun_requis = models.BooleanField(default=False)
    instructions_prelevement = models.TextField(blank=True)
    valeurs_normales = models.TextField(blank=True, help_text="Description des valeurs de référence")

    est_actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.nom}"


class DemandeExamen(models.Model):
    """Demande d'examen prescrite par un médecin"""

    STATUT_DEMANDE = (
        ('PRESCRIT', 'Prescrit'),
        ('PRELEVE', 'Prélevé'),
        ('EN_COURS', 'En cours d\'analyse'),
        ('VALIDATION', 'En attente de validation'),
        ('VALIDE', 'Validé'),
        ('REFUSE', 'Refusé'),
        ('ANNULE', 'Annulé'),
    )

    WORKFLOW_ORDER = ('PRESCRIT', 'PRELEVE', 'EN_COURS', 'VALIDATION', 'VALIDE')

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='demandes_examens')
    medecin_prescripteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='examens_prescrits')
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='demandes_examens')
    examen_type = models.ForeignKey(ExamenType, on_delete=models.CASCADE, related_name='demandes')

    statut = models.CharField(max_length=20, choices=STATUT_DEMANDE, default='PRESCRIT')
    date_prescription = models.DateTimeField(auto_now_add=True)
    urgence = models.BooleanField(default=False)

    notes_prescripteur = models.TextField(blank=True)

    date_prelevement = models.DateTimeField(null=True, blank=True)
    date_affectation = models.DateTimeField(null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_publication = models.DateTimeField(null=True, blank=True)

    preleve_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='prelevements',
    )
    affecte_a = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='examens_affectes',
    )
    valide_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='validations_examens',
    )

    def __str__(self):
        return f"Demande {self.id} - {self.patient} - {self.examen_type.nom}"

    def peut_transitionner_vers(self, nouveau_statut):
        if nouveau_statut in ('REFUSE', 'ANNULE'):
            return self.statut not in ('VALIDE', 'ANNULE')
        try:
            idx_actuel = self.WORKFLOW_ORDER.index(self.statut)
            idx_cible = self.WORKFLOW_ORDER.index(nouveau_statut)
            return idx_cible == idx_actuel + 1
        except ValueError:
            return False

    def transitionner(self, nouveau_statut):
        if not self.peut_transitionner_vers(nouveau_statut):
            raise LISError(
                f"Transition impossible : {self.statut} → {nouveau_statut}"
            )
        self.statut = nouveau_statut
        self.save(update_fields=['statut'])


class Prelevement(models.Model):
    """Détail du prélèvement effectué"""

    TYPES_PRELEVEMENT = (
        ('SANG', 'Prise de sang'),
        ('URINE', 'Urines'),
        ('SELLES', 'Selles'),
        ('ECOUVILLON', 'Ecouvillon'),
        ('BIOPSIE', 'Biopsie'),
        ('AUTRE', 'Autre'),
    )

    demande = models.OneToOneField(DemandeExamen, on_delete=models.CASCADE, related_name='prelevement')
    type_prelevement = models.CharField(max_length=20, choices=TYPES_PRELEVEMENT, default='SANG')
    date_prelevement = models.DateTimeField(auto_now_add=True)
    preleve_par = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='prelevements_effectues')
    tube_type = models.CharField(max_length=100, blank=True)
    quantite = models.CharField(max_length=50, blank=True)
    conditions = models.TextField(blank=True, help_text="Conditions de transport/conservation")
    commentaire = models.TextField(blank=True)

    def __str__(self):
        return f"Prélèvement {self.get_type_prelevement_display()} - {self.demande}"


class ResultatExamen(models.Model):
    """Résultat d'un examen — immuable après validation biologiste"""

    demande = models.OneToOneField(DemandeExamen, on_delete=models.CASCADE, related_name='resultat')
    date_saisie = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    resultats = models.TextField(help_text="Résultats détaillés de l'examen")
    interpretation = models.TextField(blank=True, help_text="Interprétation clinique")

    fichier_pdf = models.FileField(upload_to='resultats_lab/', null=True, blank=True)

    saisie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='resultats_saisis')

    est_valide = models.BooleanField(default=False)
    est_publie = models.BooleanField(default=False)
    date_validation = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='resultats_valides',
    )

    signature_electronique = models.TextField(blank=True)

    def __str__(self):
        statut = "Validé" if self.est_valide else "Non validé"
        return f"Résultat {self.demande} ({statut})"

    def save(self, *args, **kwargs):
        if self.pk:
            ancien = ResultatExamen.objects.filter(pk=self.pk).values(
                'est_valide', 'resultats', 'interpretation',
            ).first()
            if ancien and ancien['est_valide']:
                update_fields = kwargs.get('update_fields')
                champs_autorises = {'fichier_pdf'}
                if not update_fields or not set(update_fields).issubset(champs_autorises):
                    raise PermissionError(
                        "Résultat validé — immuabilité stricte (modification interdite)"
                    )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.est_valide:
            raise PermissionError("Résultat validé — suppression interdite")
        super().delete(*args, **kwargs)

    def peut_modifier(self, utilisateur):
        if self.est_valide:
            return False
        return utilisateur.role in ('BIOLOGISTE', 'ADMIN') or utilisateur == self.saisie_par

    def generer_signature(self, biologiste):
        import hashlib
        data = (
            f"{self.id}|{biologiste.id}|{self.resultats}|"
            f"{self.interpretation}|{timezone.now().isoformat()}"
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def valider(self, biologiste):
        """Validation exclusive par un biologiste — rend le résultat immuable."""
        if biologiste.role != 'BIOLOGISTE':
            raise PermissionError("Seul un biologiste peut valider un résultat")
        if self.est_valide:
            raise LISError("Ce résultat est déjà validé")
        if self.demande.statut != 'VALIDATION':
            raise LISError("La demande doit être en attente de validation")

        self.est_valide = True
        self.date_validation = timezone.now()
        self.valide_par = biologiste
        self.signature_electronique = self.generer_signature(biologiste)
        self.save()

        demande = self.demande
        demande.transitionner('VALIDE')
        demande.date_validation = self.date_validation
        demande.valide_par = biologiste
        demande.save(update_fields=['date_validation', 'valide_par'])

    def publier(self):
        """Publication du résultat validé (accessible au patient/médecin)."""
        if not self.est_valide:
            raise LISError("Seuls les résultats validés peuvent être publiés")
        self.est_publie = True
        self.save(update_fields=['est_publie'])
        demande = self.demande
        demande.date_publication = timezone.now()
        demande.save(update_fields=['date_publication'])


class HistoriqueModificationResultat(models.Model):
    """Audit trail des modifications avant validation (exigence LIS)"""

    resultat = models.ForeignKey(ResultatExamen, on_delete=models.CASCADE, related_name='historique')
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    anciens_resultats = models.TextField()
    nouveaux_resultats = models.TextField()
    ancienne_interpretation = models.TextField(blank=True)
    nouvelle_interpretation = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_adresse = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Modif résultat #{self.resultat_id} — {self.timestamp}"
