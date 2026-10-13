"""Write libpq connection settings derived from DATABASE_URL, one per line."""

import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

project_root = Path(__file__).resolve().parents[1]
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    database_url = dotenv_values(project_root / ".env").get("DATABASE_URL")
if not database_url:
    print(
        "DATABASE_URL absent de l'environnement et du fichier .env.",
        file=sys.stderr,
    )
    raise SystemExit(1)

try:
    url = make_url(database_url)
except (TypeError, ValueError) as erreur:
    print(f"DATABASE_URL invalide : {erreur}", file=sys.stderr)
    raise SystemExit(1) from erreur

settings = (
    url.host or "localhost",
    url.port or 5432,
    url.database or "",
    url.username or "",
    url.password or "",
)
if not settings[2] or not settings[3]:
    print(
        "DATABASE_URL doit préciser la base et l'utilisateur PostgreSQL.",
        file=sys.stderr,
    )
    raise SystemExit(1)
for value in settings:
    print(value)
