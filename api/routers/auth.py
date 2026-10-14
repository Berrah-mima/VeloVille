from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import Connexion, ReponseConnexion
from api.securite import create_access_token, verify_password
from api.services.authentification import trouver_utilisateur

router = APIRouter(
    prefix="/auth",
    tags=["authentification"],
)


@router.post(
    "/login",
    response_model=ReponseConnexion,
)
def login(
    payload: Connexion,
    db: Session = Depends(get_db),
) -> ReponseConnexion:

    utilisateur = trouver_utilisateur(
        db,
        payload.username,
    )

    if utilisateur is None or not verify_password(
        payload.password,
        utilisateur.mot_de_passe_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    token = create_access_token(
        utilisateur.username,
        utilisateur.role,
    )

    return ReponseConnexion(
        access_token=token,
        role=utilisateur.role,
    )