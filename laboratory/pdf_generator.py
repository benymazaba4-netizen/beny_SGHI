"""Génération de comptes-rendus PDF signés électroniquement."""

import io
import os
from django.conf import settings
from django.utils import timezone


def generer_compte_rendu_pdf(resultat):
    """Génère un PDF signé et retourne le chemin relatif pour FileField."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    demande = resultat.demande
    patient = demande.patient
    examen = demande.examen_type

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle(
        'TitreSGHI',
        parent=styles['Heading1'],
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
    )

    elements = [
        Paragraph("SGHI — Compte-Rendu de Laboratoire", titre_style),
        Paragraph(f"<b>N° demande :</b> {demande.id}", styles['Normal']),
        Spacer(1, 0.5 * cm),
    ]

    info_patient = [
        ['Patient', f"{patient.nom} {patient.prenom}"],
        ['N° Dossier', patient.numero_dossier],
        ['Examen', f"{examen.code} — {examen.nom}"],
        ['Catégorie', examen.get_categorie_display()],
        ['Prescrit par', demande.medecin_prescripteur.get_full_name()],
        ['Date prescription', demande.date_prescription.strftime('%d/%m/%Y %H:%M')],
    ]
    if demande.date_prelevement:
        info_patient.append(['Date prélèvement', demande.date_prelevement.strftime('%d/%m/%Y %H:%M')])

    table_info = Table(info_patient, colWidths=[5 * cm, 12 * cm])
    table_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eff6ff')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table_info)
    elements.append(Spacer(1, 0.8 * cm))

    elements.append(Paragraph("<b>RÉSULTATS</b>", styles['Heading2']))
    for ligne in resultat.resultats.split('\n'):
        elements.append(Paragraph(ligne or '&nbsp;', styles['Normal']))

    if resultat.interpretation:
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("<b>INTERPRÉTATION</b>", styles['Heading2']))
        elements.append(Paragraph(resultat.interpretation, styles['Normal']))

    if examen.valeurs_normales:
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("<b>VALEURS DE RÉFÉRENCE</b>", styles['Heading3']))
        elements.append(Paragraph(examen.valeurs_normales, styles['Normal']))

    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph("<b>VALIDATION BIOLOGISTE</b>", styles['Heading2']))

    validation_info = [
        ['Validé par', resultat.valide_par.get_full_name()],
        ['Date validation', resultat.date_validation.strftime('%d/%m/%Y %H:%M')],
        ['Signature électronique', resultat.signature_electronique[:32] + '...'],
    ]
    table_val = Table(validation_info, colWidths=[5 * cm, 12 * cm])
    table_val.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0fdf4')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table_val)

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(
        f"<i>Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')} — SGHI ERP Médical</i>",
        styles['Normal'],
    ))

    doc.build(elements)
    buffer.seek(0)

    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'resultats_lab'), exist_ok=True)
    filename = f"CR_{demande.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    relative_path = f"resultats_lab/{filename}"
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    with open(absolute_path, 'wb') as f:
        f.write(buffer.read())

    return relative_path
