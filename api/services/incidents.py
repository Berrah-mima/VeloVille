from datetime import datetime

from api.models import Incident

TRANSITIONS_AUTORISEES = {
    "ouvert": {"en_cours", "resolu"},
    "en_cours": {"resolu"},
    "resolu": set(),
}


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
