from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Station(Base):
    __tablename__ = "station"

    station_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    commune: Mapped[str] = mapped_column(String, nullable=False)
    capacite: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(8, 5), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(8, 5), nullable=False)
    date_mise_en_service: Mapped[date] = mapped_column(Date, nullable=False)
    __table_args__ = (
        CheckConstraint("capacite > 0", name="ck_station_capacite_positive"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_station_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_station_longitude"),
    )


class Trajet(Base):
    __tablename__ = "trajet"

    trajet_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    velo_id: Mapped[str] = mapped_column(String(8), nullable=False)
    depart_horodatage: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    station_depart: Mapped[str] = mapped_column(
        String(10), ForeignKey("station.station_id"), nullable=False
    )
    station_arrivee: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("station.station_id")
    )
    duree_secondes: Mapped[int] = mapped_column(Integer, nullable=False)
    type_usager: Mapped[str] = mapped_column(String(20), nullable=False)
    usager_ref: Mapped[str | None] = mapped_column(String(9))
    __table_args__ = (
        CheckConstraint("duree_secondes > 0", name="ck_trajet_duree_positive"),
        CheckConstraint(
            "(type_usager = 'abonne' AND usager_ref IS NOT NULL) OR "
            "(type_usager = 'occasionnel' AND usager_ref IS NULL)",
            name="ck_trajet_usager_ref",
        ),
        CheckConstraint(
            "type_usager IN ('abonne', 'occasionnel')", name="ck_trajet_type_usager"
        ),
    )


class Incident(Base):
    __tablename__ = "incident"

    incident_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    date_signalement: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cible: Mapped[str] = mapped_column(String(10), nullable=False)
    velo_id: Mapped[str | None] = mapped_column(String(8))
    station_id: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("station.station_id")
    )
    type_incident: Mapped[str] = mapped_column(String(100), nullable=False)
    statut: Mapped[str] = mapped_column(String(20), nullable=False)
    date_resolution: Mapped[datetime | None] = mapped_column(DateTime)
    technicien: Mapped[str | None] = mapped_column(String(100))
    __table_args__ = (
        CheckConstraint("statut IN ('ouvert', 'en_cours', 'resolu')", name="ck_incident_statut"),
        CheckConstraint(
            "(cible = 'velo' AND velo_id IS NOT NULL AND station_id IS NULL) OR "
            "(cible = 'station' AND velo_id IS NULL AND station_id IS NOT NULL)",
            name="ck_incident_cible_reference",
        ),
        CheckConstraint("cible IN ('velo', 'station')", name="ck_incident_cible"),
        CheckConstraint(
            "(statut = 'resolu' AND date_resolution IS NOT NULL) OR "
            "(statut <> 'resolu' AND date_resolution IS NULL)",
            name="ck_incident_date_resolution_statut",
        ),
        CheckConstraint(
            "date_resolution IS NULL OR date_resolution >= date_signalement",
            name="ck_incident_dates_coherentes",
        ),
    )


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id_utilisateur: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    __table_args__ = (
        CheckConstraint("role IN ('exploitant', 'direction')", name="ck_utilisateur_role"),
    )
