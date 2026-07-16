"""Crée la base PostgreSQL si elle n'existe pas (dev local Windows)."""
from __future__ import annotations

import os
import sys

import psycopg


def main() -> int:
    db_name = os.environ.get('DB_NAME', 'sghi_db')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'postgres')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')

    admin_dsn = (
        f'dbname=postgres user={db_user} password={db_password} '
        f'host={db_host} port={db_port} connect_timeout=10'
    )
    try:
        with psycopg.connect(admin_dsn) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (db_name,))
                if cur.fetchone():
                    print(f'Base {db_name} deja presente.')
                    return 0
                cur.execute(f'CREATE DATABASE "{db_name}"')
                print(f'Base {db_name} creee.')
                return 0
    except psycopg.Error as exc:
        print(f'Echec creation base {db_name}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
