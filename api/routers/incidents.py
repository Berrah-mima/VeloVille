from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Incident, Utilisateur
from api.schemas import ChangementStatut, IncidentLecture, Pagee
from api.securite import exiger_role, utilisateur_courant
from api.services.incidents import changer_statut_incident, lister_incidents

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=Pagee[IncidentLecture])
def lister_incidents(
    statut: Literal["ouvert", "en_cours", "resolu"] | None = None,
    page: int = Query(default=1, ge=1),
    taille_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(utilisateur_courant),
) -> dict[str, object]:
    total, resultats = lister_incidents(db, statut, page, taille_page)
    return {"total": total, "page": page, "taille_page": taille_page, "resultats": resultats}


@router.put("/{incident_id}/statut", response_model=IncidentLecture)
def changer_statut(
    incident_id: str,
    payload: ChangementStatut,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(exiger_role("exploitant")),
) -> Incident:
    try:
        incident = changer_statut_incident(
            db,
            incident_id,
            payload.statut,
            datetime.now(timezone.utc).replace(tzinfo=None),
        )
    except ValueError as erreur:
        raise HTTPException(status_code=422, detail=str(erreur)) from erreur
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    return incident
