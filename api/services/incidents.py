from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models import Incident

TRANSITIONS_AUTORISEES = {
    "ouvert": {"en_cours", "resolu"},
    "en_cours": {"resolu"},
    "resolu": set(),
}


def lister_incidents(
    db: Session, statut: str | None, page: int, taille_page: int
) -> tuple[int, list[Incident]]:
    filtres = [Incident.statut == statut] if statut else []
    total = db.scalar(select(func.count()).select_from(Incident).where(*filtres)) or 0
    incidents = db.scalars(
        select(Incident)
        .where(*filtres)
        .order_by(Incident.date_signalement.desc(), Incident.incident_id.desc())
        .offset((page - 1) * taille_page)
        .limit(taille_page)
    ).all()
    return total, incidents


def changer_statut_incident(
    db: Session, incident_id: str, nouveau_statut: str, maintenant: datetime
) -> Incident | None:
    incident = db.get(Incident, incident_id)
    if incident is None:
        return None
    appliquer_transition(incident, nouveau_statut, maintenant)
    db.commit()
    db.refresh(incident)
    return incident


def appliquer_transition(
    incident: Incident, nouveau_statut: str, maintenant: datetime
) -> Incident:
    """Valide et applique une transition métier autorisée sur un incident."""
    if nouveau_statut not in TRANSITIONS_AUTORISEES.get(incident.statut, set()):
        raise ValueError("Transition de statut non autorisee")
    incident.statut = nouveau_statut
    if nouveau_statut == "resolu" and incident.date_resolution is None:
        incident.date_resolution = maintenant
    return incident
