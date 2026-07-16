"""Serveur SMTP local de developpement (sans Docker)."""
import asyncio
import email
from datetime import datetime
from pathlib import Path

from aiosmtpd.controller import Controller

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTBOX = PROJECT_ROOT / 'emails' / 'outbox'


class DevMailHandler:
    async def handle_DATA(self, server, session, envelope):
        msg = email.message_from_bytes(envelope.content)
        subject = msg.get('Subject', '(sans objet)')
        recipients = ', '.join(envelope.rcpt_tos)
        OUTBOX.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        path = OUTBOX / f'{stamp}.eml'
        path.write_bytes(envelope.content)
        print(f'[SMTP] -> {recipients} | {subject}')
        print(f'       sauvegarde : {path}')
        return '250 Message accepted for delivery'


async def _run():
    host = '127.0.0.1'
    port = 1025
    controller = Controller(DevMailHandler(), hostname=host, port=port)
    controller.start()
    print(f'=== SGHI SMTP dev actif sur {host}:{port} ===')
    print(f'E-mails sauvegardes dans : {OUTBOX}')
    print('Ctrl+C pour arreter.')
    try:
        await asyncio.Event().wait()
    finally:
        controller.stop()


def main():
    asyncio.run(_run())


if __name__ == '__main__':
    main()
