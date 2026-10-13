from datetime import date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models import Incident, Station, Trajet


def activite_par_jour(
    db: Session, date_debut: date | None = None, date_fin: date | None = None
) -> list[dict[str, object]]:
    jour_sql = func.date(Trajet.depart_horodatage)
    requete = select(jour_sql.label("jour"), func.count(Trajet.trajet_id).label("nb_trajets"))
    if date_debut is not None:
        requete = requete.where(Trajet.depart_horodatage >= datetime.combine(date_debut, time.min))
    if date_fin is not None:
        requete = requete.where(
            Trajet.depart_horodatage <= datetime.combine(date_fin, time.max)
        )
    requete = requete.group_by(jour_sql).order_by(jour_sql)
    return [{"jour": jour, "nb_trajets": nombre} for jour, nombre in db.execute(requete)]


def stations_actives(db: Session, limite: int = 10) -> list[dict[str, object]]:
    departs = (
        select(Trajet.station_depart.label("station_id"), func.count().label("nb_departs"))
        .group_by(Trajet.station_depart)
        .subquery()
    )
    arrivees = (
        select(Trajet.station_arrivee.label("station_id"), func.count().label("nb_arrivees"))
        .where(Trajet.station_arrivee.is_not(None))
        .group_by(Trajet.station_arrivee)
        .subquery()
    )
    nb_departs = func.coalesce(departs.c.nb_departs, 0)
    nb_arrivees = func.coalesce(arrivees.c.nb_arrivees, 0)
    requete = (
        select(
            Station.station_id,
            Station.nom,
            nb_departs.label("nb_departs"),
            nb_arrivees.label("nb_arrivees"),
        )
        .outerjoin(departs, Station.station_id == departs.c.station_id)
        .outerjoin(arrivees, Station.station_id == arrivees.c.station_id)
        .where(nb_departs + nb_arrivees > 0)
        .order_by((nb_departs + nb_arrivees).desc(), Station.station_id.asc())
        .limit(limite)
    )
    return [
        {
            "station_id": ligne.station_id,
            "nom": ligne.nom,
            "nb_departs": ligne.nb_departs,
            "nb_arrivees": ligne.nb_arrivees,
        }
        for ligne in db.execute(requete)
    ]


def incidents_par_statut(db: Session) -> dict[str, object]:
    requete = (
        select(Incident.statut, func.count(Incident.incident_id).label("nb_incidents"))
        .group_by(Incident.statut)
        .order_by(Incident.statut)
    )
    if db.bind is not None and db.bind.dialect.name == "sqlite":
        delai_heures = (
            func.julianday(Incident.date_resolution)
            - func.julianday(Incident.date_signalement)
        ) * 24
    else:
        delai_heures = func.extract(
            "epoch", Incident.date_resolution - Incident.date_signalement
        ) / 3600
    moyenne = db.scalar(
        select(func.avg(delai_heures)).where(
            Incident.statut == "resolu", Incident.date_resolution.is_not(None)
        )
    )
    return {
        "donnees": [
            {"statut": statut, "nb_incidents": nombre}
            for statut, nombre in db.execute(requete)
        ],
        "delai_moyen_resolution_heures": round(float(moyenne), 1) if moyenne is not None else None,
    }
