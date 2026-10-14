"""Configuration de l'application."""

import os

from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

if len(JWT_SECRET) < 32:
    raise RuntimeError(
        "JWT_SECRET doit contenir au moins 32 caractères."
    )

if JWT_EXPIRE_MINUTES <= 0:
    raise RuntimeError(
        "JWT_EXPIRATION_MINUTES doit être positif."
    )