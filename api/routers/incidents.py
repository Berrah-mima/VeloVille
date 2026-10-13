from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Incident, Utilisateur
from api.schemas import ChangementStatut, IncidentLecture, Pagee
from api.securite import exiger_role, utilisateur_courant
from api.services.incidents import appliquer_transition

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=Pagee[IncidentLecture])
def lister_incidents(
    statut: Literal["ouvert", "en_cours", "resolu"] | None = None,
    page: int = Query(default=1, ge=1),
    taille_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(utilisateur_courant),
) -> dict[str, object]:
    filtres = [Incident.statut == statut] if statut else []
    total = db.scalar(select(func.count()).select_from(Incident).where(*filtres)) or 0
    resultats = db.scalars(
        select(Incident)
        .where(*filtres)
        .order_by(Incident.date_signalement.desc(), Incident.incident_id.desc())
        .offset((page - 1) * taille_page)
        .limit(taille_page)
    ).all()
    return {"total": total, "page": page, "taille_page": taille_page, "resultats": resultats}


@router.put("/{incident_id}/statut", response_model=IncidentLecture)
def changer_statut(
    incident_id: str,
    payload: ChangementStatut,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(exiger_role("exploitant")),
) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    try:
        appliquer_transition(
            incident,
            payload.statut,
            datetime.now(timezone.utc).replace(tzinfo=None),
        )
    except ValueError as erreur:
        raise HTTPException(status_code=422, detail=str(erreur)) from erreur
    db.commit()
    db.refresh(incident)
    return incident
