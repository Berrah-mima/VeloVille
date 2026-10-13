from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur
from api.schemas import Connexion, ReponseConnexion
from api.securite import creer_jeton, verifier_mot_de_passe

router = APIRouter(prefix="/auth", tags=["authentification"])


@router.post("/login", response_model=ReponseConnexion)
def login(payload: Connexion, db: Session = Depends(get_db)) -> ReponseConnexion:
    utilisateur = db.scalar(
        select(Utilisateur).where(Utilisateur.username == payload.username)
    )
    if utilisateur is None or not verifier_mot_de_passe(
        payload.password, utilisateur.mot_de_passe_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ReponseConnexion(
        access_token=creer_jeton(utilisateur),
        role=utilisateur.role,
    )
