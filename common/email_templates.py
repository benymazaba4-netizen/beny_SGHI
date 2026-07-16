"""Templates e-mail HTML SGHI."""

BRAND_NAVY = "#0B1F3A"
BRAND_TEAL = "#0D9488"


def render_email_html(title: str, paragraphs: list[str], details: list[tuple[str, str]] | None = None) -> str:
    """Génère un e-mail HTML responsive aux couleurs SGHI."""
    details_html = ""
    if details:
        rows = "".join(
            f'<tr><td style="padding:8px 12px;color:#64748B;font-size:13px;">{label}</td>'
            f'<td style="padding:8px 12px;font-weight:600;color:#0F172A;font-size:13px;">{value}</td></tr>'
            for label, value in details
        )
        details_html = f"""
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
               style="margin:20px 0;background:#F8FAFC;border-radius:12px;border:1px solid #E2E8F0;">
          {rows}
        </table>"""

    body_paragraphs = "".join(
        f'<p style="margin:0 0 14px;color:#334155;font-size:15px;line-height:1.6;">{p}</p>'
        for p in paragraphs
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:Segoe UI,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
    <tr><td align="center" style="padding:32px 16px;">
      <table role="presentation" width="100%" style="max-width:560px;background:#fff;border-radius:16px;
             overflow:hidden;box-shadow:0 4px 24px rgba(11,31,58,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,{BRAND_NAVY},{BRAND_TEAL});padding:28px 32px;">
            <p style="margin:0;color:rgba(255,255,255,0.85);font-size:12px;letter-spacing:1px;">SGHI ERP MÉDICAL</p>
            <h1 style="margin:8px 0 0;color:#fff;font-size:22px;font-weight:700;">{title}</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            {body_paragraphs}
            {details_html}
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px;background:#F8FAFC;border-top:1px solid #E2E8F0;">
            <p style="margin:0;color:#94A3B8;font-size:12px;text-align:center;">
              CHU — Centre Hospitalier Universitaire · Données chiffrées · Conformité RGPD
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
