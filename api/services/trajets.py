from datetime import date, datetime, time

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from api.models import Trajet


def lister_trajets(
    db: Session,
    date_debut: date | None,
    date_fin: date | None,
    station: str | None,
    page: int,
    taille_page: int,
) -> tuple[int, list[Trajet]]:
    filtres = []
    if date_debut is not None:
        filtres.append(
            Trajet.depart_horodatage >= datetime.combine(date_debut, time.min)
        )
    if date_fin is not None:
        filtres.append(
            Trajet.depart_horodatage <= datetime.combine(date_fin, time.max)
        )
    if station:
        filtres.append(
            or_(Trajet.station_depart == station, Trajet.station_arrivee == station)
        )
    total = db.scalar(select(func.count()).select_from(Trajet).where(*filtres)) or 0
    trajets = db.scalars(
        select(Trajet)
        .where(*filtres)
        .order_by(Trajet.depart_horodatage.asc(), Trajet.trajet_id.asc())
        .offset((page - 1) * taille_page)
        .limit(taille_page)
    ).all()
    return total, trajets
