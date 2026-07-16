from django.db import models


class CodeCIM10(models.Model):
    """Référentiel CIM-10 (ICD-10)."""

    code = models.CharField(max_length=10, unique=True, db_index=True)
    libelle = models.CharField(max_length=500)
    chapitre = models.CharField(max_length=200, blank=True)
    est_actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Code CIM-10'
        verbose_name_plural = 'Codes CIM-10'

    def __str__(self):
        return f"{self.code} — {self.libelle[:60]}"
