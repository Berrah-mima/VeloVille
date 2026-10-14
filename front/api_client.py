"""Client HTTP commun pour les appels Streamlit vers l'API VéloVille."""

import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
API_TIMEOUT_SECONDES = float(os.getenv("API_TIMEOUT_SECONDES", "5"))


class ErreurApi(Exception):
    def __init__(self, message: str, statut: int | None = None):
        self.statut = statut
        super().__init__(message)


def _requete(
    methode: str,
    chemin: str,
    jeton: str | None = None,
    **kwargs: Any,
) -> Any:
    entetes = kwargs.pop("headers", {})
    if jeton:
        entetes["Authorization"] = f"Bearer {jeton}"
    try:
        reponse = requests.request(
            methode,
            f"{API_URL}{chemin}",
            headers=entetes,
            timeout=API_TIMEOUT_SECONDES,
            **kwargs,
        )
    except requests.Timeout as erreur:
        raise ErreurApi("L'API met trop de temps à répondre.") from erreur
    except requests.RequestException as erreur:
        raise ErreurApi("L'API est injoignable. Vérifiez qu'elle est démarrée.") from erreur
    try:
        contenu = reponse.json()
    except requests.exceptions.JSONDecodeError as erreur:
        raise ErreurApi("La réponse de l'API est illisible.", reponse.status_code) from erreur
    if not reponse.ok:
        detail = contenu.get("detail") if isinstance(contenu, dict) else None
        if reponse.status_code == 401:
            message = (
                "Identifiant ou mot de passe incorrect."
                if chemin == "/auth/login"
                else "Votre session a expiré. Veuillez vous reconnecter."
            )
        elif reponse.status_code == 403:
            message = "Vous n'avez pas le droit de modifier un incident."
        elif reponse.status_code == 404:
            if chemin.startswith("/stations/"):
                message = "Station introuvable."
            elif chemin.startswith("/incidents/"):
                message = "Incident introuvable."
            else:
                message = "La ressource demandée est introuvable."
        elif reponse.status_code == 422:
            messages_422 = {
                "date_debut doit précéder date_fin": (
                    "La date de début doit précéder la date de fin."
                ),
                "Transition de statut non autorisee": (
                    "Cette transition de statut n'est pas autorisée."
                ),
            }
            message = messages_422.get(
                detail if isinstance(detail, str) else "",
                "Les critères ou la transition demandés ne sont pas valides.",
            )
        else:
            message = str(detail or "Erreur de l'API.")
        raise ErreurApi(message, reponse.status_code)
    return contenu


def se_connecter(username: str, password: str) -> dict[str, Any]:
    return _requete("POST", "/auth/login", json={"username": username, "password": password})


def lire_stations(
    jeton: str, commune: str | None = None, page: int = 1, taille_page: int = 20
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "taille_page": taille_page}
    if commune and commune != "Toutes":
        params["commune"] = commune
    return _requete("GET", "/stations", jeton, params=params)


def lire_incidents(
    jeton: str, statut: str | None = None, page: int = 1, taille_page: int = 20
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "taille_page": taille_page}
    if statut and statut != "Tous":
        params["statut"] = statut
    return _requete("GET", "/incidents", jeton, params=params)


def changer_statut(jeton: str, incident_id: str, statut: str) -> dict[str, Any]:
    return _requete(
        "PUT",
        f"/incidents/{incident_id}/statut",
        jeton,
        json={"statut": statut},
    )


def lire_trajets(jeton: str, date_debut: str, date_fin: str) -> dict[str, Any]:
    return _requete(
        "GET",
        "/trajets",
        jeton,
        params={"date_debut": date_debut, "date_fin": date_fin, "taille_page": 1},
    )


def lire_activite(jeton: str, date_debut: str, date_fin: str) -> dict[str, Any]:
    return _requete(
        "GET",
        "/indicateurs/activite-par-jour",
        jeton,
        params={"date_debut": date_debut, "date_fin": date_fin},
    )


def lire_stations_actives(jeton: str, limite: int) -> dict[str, Any]:
    return _requete(
        "GET", "/indicateurs/stations-actives", jeton, params={"limite": limite}
    )


def lire_incidents_par_statut(jeton: str) -> dict[str, Any]:
    return _requete("GET", "/indicateurs/incidents-par-statut", jeton)
