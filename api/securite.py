import os
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
JWT_ALGORITHM = "HS256"


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET doit contenir au moins 32 caractères.")
    return secret


def verifier_mot_de_passe(mot_de_passe: str, hachage: str) -> bool:
    try:
        return bcrypt.checkpw(mot_de_passe.encode("utf-8"), hachage.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def creer_jeton(utilisateur: Utilisateur) -> str:
    expiration = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    if expiration <= 0:
        raise RuntimeError("JWT_EXPIRATION_MINUTES doit être positif.")
    maintenant = datetime.now(timezone.utc)
    charge_utile = {
        "sub": str(utilisateur.id_utilisateur),
        "role": utilisateur.role,
        "iat": maintenant,
        "exp": maintenant + timedelta(minutes=expiration),
    }
    return jwt.encode(charge_utile, _jwt_secret(), algorithm=JWT_ALGORITHM)


def utilisateur_courant(
    jeton: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Utilisateur:
    identifiants_invalides = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Jeton invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        contenu: dict[str, Any] = jwt.decode(
            jeton, _jwt_secret(), algorithms=[JWT_ALGORITHM]
        )
        identifiant = contenu.get("sub")
        role = contenu.get("role")
        if not identifiant or role not in {"exploitant", "direction"}:
            raise identifiants_invalides
        utilisateur = db.get(Utilisateur, int(identifiant))
        if utilisateur is None or utilisateur.role != role:
            raise identifiants_invalides
        return utilisateur
    except (jwt.PyJWTError, ValueError, TypeError):
        raise identifiants_invalides


def exiger_role(role_requis: str):
    def verifier_role(
        utilisateur: Utilisateur = Depends(utilisateur_courant),
    ) -> Utilisateur:
        if utilisateur.role != role_requis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acces reserve au role exploitant",
            )
        return utilisateur

    return verifier_role
