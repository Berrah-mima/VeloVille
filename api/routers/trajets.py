from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur
from api.schemas import Pagee, TrajetLecture
from api.securite import utilisateur_courant
from api.services.trajets import lister_trajets as service_lister_trajets

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
    total, resultats = service_lister_trajets(
        db, date_debut, date_fin, station, page, taille_page
    )
    return {"total": total, "page": page, "taille_page": taille_page, "resultats": resultats}
