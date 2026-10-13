"""Write libpq connection settings derived from DATABASE_URL, one per line."""

import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

def parametres_libpq(database_url: str) -> tuple[str, str, str, str, str]:
    try:
        url = make_url(database_url)
    except (TypeError, ValueError) as erreur:
        raise ValueError(f"DATABASE_URL invalide : {erreur}") from erreur
    settings = (
        url.host or "localhost",
        str(url.port or 5432),
        url.database or "",
        url.username or "",
        url.password or "",
    )
    if not settings[2] or not settings[3]:
        raise ValueError(
            "DATABASE_URL doit préciser la base et l'utilisateur PostgreSQL."
        )
    return settings


def main() -> None:
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
        for value in parametres_libpq(database_url):
            print(value)
    except ValueError as erreur:
        print(str(erreur), file=sys.stderr)
        raise SystemExit(1) from erreur


if __name__ == "__main__":
    main()
