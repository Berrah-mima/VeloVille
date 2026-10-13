from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class LectureORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StationLecture(LectureORM):
    station_id: str
    nom: str
    commune: str
    capacite: int
    latitude: float
    longitude: float
    date_mise_en_service: date


class TrajetLecture(LectureORM):
    trajet_id: str
    velo_id: str
    depart_horodatage: datetime
    station_depart: str
    station_arrivee: str | None
    duree_secondes: int
    type_usager: str
    usager_ref: str | None


class IncidentLecture(LectureORM):
    incident_id: str
    date_signalement: datetime
    cible: str
    velo_id: str | None
    station_id: str | None
    type_incident: str
    statut: str
    date_resolution: datetime | None
    technicien: str | None


class Pagee(BaseModel, Generic[T]):
    total: int
    page: int
    taille_page: int
    resultats: list[T]


class Connexion(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class ReponseConnexion(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class ChangementStatut(BaseModel):
    statut: str = Field(pattern="^(en_cours|resolu)$")


class ActiviteJour(BaseModel):
    jour: date
    nb_trajets: int


class StationActive(BaseModel):
    station_id: str
    nom: str
    nb_departs: int
    nb_arrivees: int


class IncidentsParStatut(BaseModel):
    statut: str
    nb_incidents: int
