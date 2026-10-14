from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur
from api.securite import utilisateur_courant
from api.services.indicateurs import (
    activite_par_jour,
    incidents_par_statut,
    stations_actives,
)

router = APIRouter(prefix="/indicateurs", tags=["indicateurs"])


@router.get("/activite-par-jour")
def lire_activite_par_jour(
    date_debut: date | None = None,
    date_fin: date | None = None,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(utilisateur_courant),
) -> dict[str, object]:
    if date_debut and date_fin and date_debut > date_fin:
        raise HTTPException(status_code=422, detail="date_debut doit précéder date_fin")
    return {"donnees": activite_par_jour(db, date_debut, date_fin)}


@router.get("/stations-actives")
def lire_stations_actives(
    limite: int = Query(default=10, ge=1),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(utilisateur_courant),
) -> dict[str, object]:
    return {"donnees": stations_actives(db, limite)}


@router.get("/incidents-par-statut")
def lire_incidents_par_statut(
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(utilisateur_courant),
) -> dict[str, object]:
    return incidents_par_statut(db)
