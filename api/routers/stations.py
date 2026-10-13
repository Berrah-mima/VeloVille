from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Station, Utilisateur
from api.schemas import Pagee, StationLecture
from api.securite import utilisateur_courant

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("", response_model=Pagee[StationLecture])
def lister_stations(
    commune: str | None = None,
    page: int = Query(default=1, ge=1),
    taille_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(utilisateur_courant),
) -> dict[str, object]:
    filtres = [Station.commune == commune] if commune else []
    total = db.scalar(select(func.count()).select_from(Station).where(*filtres)) or 0
    resultats = db.scalars(
        select(Station)
        .where(*filtres)
        .order_by(Station.station_id)
        .offset((page - 1) * taille_page)
        .limit(taille_page)
    ).all()
    return {"total": total, "page": page, "taille_page": taille_page, "resultats": resultats}


@router.get("/{station_id}", response_model=StationLecture)
def lire_station(
    station_id: str,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(utilisateur_courant),
) -> Station:
    station = db.get(Station, station_id)
    if station is None:
        raise HTTPException(status_code=404, detail="Station introuvable")
    return station
