"""Crée les tables VéloVille et initialise les comptes de démonstration."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from api.database import SessionLocal, engine
from api.models import Base, Utilisateur

DEMO_USERS = (
    (
        "exploitant01",
        "$2b$12$ej20gmOU7l.L1SOku8K66uV2PMETEc5ub8A.PM.Y.7QGHEvUlBkEi",
        "exploitant",
    ),
    (
        "direction01",
        "$2b$12$l8m1OACxjxS8rOcvTBH7oOuxkXEfMed1KAcZIZDxGZPLvBmR4w8We",
        "direction",
    ),
)


def initialiser() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for username, password_hash, role in DEMO_USERS:
            utilisateur = db.scalar(
                select(Utilisateur).where(Utilisateur.username == username)
            )
            if utilisateur is None:
                db.add(
                    Utilisateur(
                        username=username,
                        mot_de_passe_hash=password_hash,
                        role=role,
                    )
                )
        db.commit()
    print("Base VéloVille initialisée ; comptes exploitant01 et direction01 disponibles.")


if __name__ == "__main__":
    initialiser()
