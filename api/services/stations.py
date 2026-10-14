from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models import Station


def lister_stations(
    db: Session, commune: str | None, page: int, taille_page: int
) -> tuple[int, list[Station]]:
    filtres = [Station.commune == commune] if commune else []
    total = db.scalar(select(func.count()).select_from(Station).where(*filtres)) or 0
    stations = db.scalars(
        select(Station)
        .where(*filtres)
        .order_by(Station.station_id)
        .offset((page - 1) * taille_page)
        .limit(taille_page)
    ).all()
    return total, stations


def trouver_station(db: Session, station_id: str) -> Station | None:
    return db.get(Station, station_id)
