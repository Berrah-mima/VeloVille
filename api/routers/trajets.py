from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Trajet, Utilisateur
from api.schemas import Pagee, TrajetLecture
from api.securite import utilisateur_courant

router = APIRouter(prefix="/trajets", tags=["trajets"])


@router.get("", response_model=Pagee[TrajetLecture])
def lister_trajets(
    date_debut: date | None = None,
    date_fin: date | None = None,
    station: str | None = None,
    page: int = Query(default=1, ge=1),
    taille_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(utilisateur_courant),
) -> dict[str, object]:
    if date_debut and date_fin and date_debut > date_fin:
        raise HTTPException(status_code=422, detail="date_debut doit précéder date_fin")
    filtres = []
    if date_debut:
        filtres.append(
            Trajet.depart_horodatage >= datetime.combine(date_debut, time.min)
        )
    if date_fin:
        filtres.append(
            Trajet.depart_horodatage
            <= datetime.combine(date_fin, time.max)
        )
    if station:
        filtres.append(
            or_(Trajet.station_depart == station, Trajet.station_arrivee == station)
        )
    total = db.scalar(select(func.count()).select_from(Trajet).where(*filtres)) or 0
    resultats = db.scalars(
        select(Trajet)
        .where(*filtres)
        .order_by(Trajet.depart_horodatage.asc(), Trajet.trajet_id.asc())
        .offset((page - 1) * taille_page)
        .limit(taille_page)
    ).all()
    return {"total": total, "page": page, "taille_page": taille_page, "resultats": resultats}
