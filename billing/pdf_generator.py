"""Génération de factures PDF."""

import io
import os
from django.conf import settings
from django.utils import timezone


def generer_facture_pdf(facture):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    patient = facture.patient
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    titre = ParagraphStyle('Titre', parent=styles['Heading1'], textColor=colors.HexColor('#1e40af'))

    elements = [
        Paragraph("SGHI — FACTURE", titre),
        Paragraph(f"<b>N° {facture.numero_facture}</b>", styles['Normal']),
        Paragraph(f"Date : {facture.date_emission.strftime('%d/%m/%Y')}", styles['Normal']),
        Spacer(1, 0.5 * cm),
    ]

    info = [
        ['Patient', f"{patient.nom} {patient.prenom}"],
        ['N° Dossier', patient.numero_dossier],
        ['Statut', facture.get_statut_display()],
    ]
    if facture.admission_id:
        info.append(['Admission', f"#{facture.admission_id}"])

    t_info = Table(info, colWidths=[4 * cm, 13 * cm])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eff6ff')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 0.8 * cm))

    data = [['Description', 'Qté', 'P.U. (FCFA)', 'Montant (FCFA)']]
    for l in facture.lignes.all():
        data.append([
            l.description[:50],
            str(l.quantite),
            f"{l.prix_unitaire:,.0f}",
            f"{l.montant:,.0f}",
        ])

    t_lignes = Table(data, colWidths=[9 * cm, 1.5 * cm, 3 * cm, 3.5 * cm])
    t_lignes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(t_lignes)
    elements.append(Spacer(1, 0.5 * cm))

    totaux = [
        ['Sous-total', f"{facture.sous_total:,.0f} FCFA"],
        ['Remise', f"-{facture.remise:,.0f} FCFA"],
        ['Tiers-payant (assurance)', f"-{facture.montant_assurance:,.0f} FCFA"],
        ['À payer par le patient', f"{facture.montant_patient:,.0f} FCFA"],
        ['Déjà payé', f"{facture.montant_paye:,.0f} FCFA"],
        ['Reste à payer', f"{facture.montant_restant:,.0f} FCFA"],
    ]
    t_totaux = Table(totaux, colWidths=[10 * cm, 7 * cm])
    t_totaux.setStyle(TableStyle([
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fef3c7')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elements.append(t_totaux)

    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph(
        f"<i>Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')} — SGHI ERP Médical</i>",
        styles['Normal'],
    ))

    doc.build(elements)
    buffer.seek(0)

    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'factures'), exist_ok=True)
    filename = f"{facture.numero_facture}.pdf"
    relative = f"factures/{filename}"
    with open(os.path.join(settings.MEDIA_ROOT, relative), 'wb') as f:
        f.write(buffer.read())
    return relative
