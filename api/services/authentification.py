from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models import Utilisateur


def trouver_utilisateur(db: Session, username: str) -> Utilisateur | None:
    return db.scalar(select(Utilisateur).where(Utilisateur.username == username))
