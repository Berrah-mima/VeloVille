"""Fonctions de sécurité : bcrypt, JWT et protection des routes."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import (
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
)
from api.database import get_db
from api.models import Utilisateur


# Swagger demandera simplement un Bearer token.
bearer_scheme = HTTPBearer()


def hash_password(plain_password: str) -> str:
    """Hache le mot de passe avant stockage en base."""

    return bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Compare le mot de passe saisi avec le hash stocké."""

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    username: str,
    role: str,
) -> str:
    """Crée un JWT signé contenant l'identité et le rôle."""

    now = datetime.now(timezone.utc)

    expiration = now + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Vérifie la signature et l'expiration du JWT."""

    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )


def utilisateur_courant(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> Utilisateur:
    """Retourne l'utilisateur correspondant au JWT."""

    erreur_authentification = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Jeton invalide ou expiré",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    token = credentials.credentials

    try:
        payload = decode_access_token(token)

        username = payload.get("sub")
        role = payload.get("role")

        if not username:
            raise erreur_authentification

        if role not in {
            "exploitant",
            "direction",
        }:
            raise erreur_authentification

    except jwt.PyJWTError:
        raise erreur_authentification

    utilisateur = db.scalar(
        select(Utilisateur).where(
            Utilisateur.username == username
        )
    )

    if utilisateur is None:
        raise erreur_authentification

    if utilisateur.role != role:
        raise erreur_authentification

    return utilisateur


def exiger_role(role_requis: str):
    """Vérifie que l'utilisateur possède le rôle demandé."""

    def verifier_role(
        utilisateur: Utilisateur = Depends(
            utilisateur_courant
        ),
    ) -> Utilisateur:

        if utilisateur.role != role_requis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acces reserve au role exploitant",
            )

        return utilisateur

    return verifier_role