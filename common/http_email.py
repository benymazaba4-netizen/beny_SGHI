"""Envoi e-mail via API HTTP Brevo — contourne le blocage SMTP du plan Free Render."""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


def brevo_configured() -> bool:
    return bool((getattr(settings, 'BREVO_API_KEY', '') or '').strip())


def _sender() -> tuple[str, str]:
    email = (
        getattr(settings, 'BREVO_SENDER_EMAIL', '')
        or getattr(settings, 'EMAIL_HOST_USER', '')
        or 'noreply@sghi.local'
    ).strip()
    name = (getattr(settings, 'BREVO_SENDER_NAME', '') or 'SGHI ERP').strip()
    return email, name


def send_email_brevo(
    *,
    to: str,
    subject: str,
    text: str,
    html: str | None = None,
) -> None:
    """Envoie un e-mail transactionnel via l'API Brevo (HTTPS :443)."""
    api_key = (getattr(settings, 'BREVO_API_KEY', '') or '').strip()
    if not api_key:
        raise RuntimeError('BREVO_API_KEY non configure')

    sender_email, sender_name = _sender()
    payload: dict = {
        'sender': {'name': sender_name, 'email': sender_email},
        'to': [{'email': to}],
        'subject': subject,
        'textContent': text,
    }
    if html:
        payload['htmlContent'] = html

    request = urllib.request.Request(
        'https://api.brevo.com/v3/smtp/email',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'api-key': api_key,
            'accept': 'application/json',
            'content-type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
        logger.info('Brevo OK → %s (%s)', to, subject)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'Brevo HTTP {exc.code}: {body}') from exc


def send_outbound_email(
    *,
    to: str,
    subject: str,
    text: str,
    html: str | None = None,
    from_email: str | None = None,
) -> None:
    """
    Envoie un e-mail : Brevo si configuré, sinon Django SMTP/console.
    """
    if brevo_configured():
        send_email_brevo(to=to, subject=subject, text=text, html=html)
        return

    from django.core.mail import EmailMultiAlternatives, send_mail

    sender = from_email or settings.DEFAULT_FROM_EMAIL
    if html:
        msg = EmailMultiAlternatives(subject, text, sender, [to])
        msg.attach_alternative(html, 'text/html')
        msg.send(fail_silently=False)
    else:
        send_mail(subject, text, sender, [to], fail_silently=False)
