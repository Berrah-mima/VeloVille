import os
from datetime import date, datetime

os.environ.setdefault("JWT_SECRET", "unit-test-secret-with-more-than-32-characters")

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import get_db
from api.main import app
from api.models import Base, Incident, Station, Trajet, Utilisateur
from tests.constantes import MOT_DE_PASSE_TEST

engine_test = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionTest = sessionmaker(bind=engine_test, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(engine_test)
    db = SessionTest()
    stations = [
        Station(
            station_id=f"S00{index}",
            nom=f"Lille - Lieu {index}",
            commune="Lille",
            capacite=10 + index,
            latitude=50.6,
            longitude=3.1,
            date_mise_en_service=date(2024, 1, 1),
        )
        for index in range(1, 4)
    ]
    db.add_all(stations)
    db.flush()
    db.add_all(
        [
            Trajet(
                trajet_id="T000001",
                velo_id="V0001",
                depart_horodatage=datetime(2026, 8, 24, 9, 0),
                station_depart="S001",
                station_arrivee="S002",
                duree_secondes=300,
                type_usager="abonne",
                usager_ref="U12345678",
            ),
            Trajet(
                trajet_id="T000002",
                velo_id="V0002",
                depart_horodatage=datetime(2026, 8, 24, 10, 0),
                station_depart="S001",
                station_arrivee=None,
                duree_secondes=600,
                type_usager="occasionnel",
                usager_ref=None,
            ),
            Trajet(
                trajet_id="T000003",
                velo_id="V0003",
                depart_horodatage=datetime(2026, 8, 25, 9, 0),
                station_depart="S002",
                station_arrivee="S003",
                duree_secondes=900,
                type_usager="occasionnel",
                usager_ref=None,
            ),
        ]
    )
    db.add_all(
        [
            Incident(
                incident_id="I2026-0001",
                date_signalement=datetime(2026, 8, 1, 9),
                cible="velo",
                velo_id="V0001",
                station_id=None,
                type_incident="frein defectueux",
                statut="ouvert",
                date_resolution=None,
                technicien=None,
            ),
            Incident(
                incident_id="I2026-0002",
                date_signalement=datetime(2026, 8, 1, 9),
                cible="station",
                velo_id=None,
                station_id="S001",
                type_incident="borne hors service",
                statut="resolu",
                date_resolution=datetime(2026, 8, 1, 11, 30),
                technicien="A. Martin",
            ),
        ]
    )
    hash_mdp = bcrypt.hashpw(MOT_DE_PASSE_TEST.encode(), bcrypt.gensalt()).decode()
    db.add_all(
        [
            Utilisateur(username="exploitant01", mot_de_passe_hash=hash_mdp, role="exploitant"),
            Utilisateur(username="direction01", mot_de_passe_hash=hash_mdp, role="direction"),
        ]
    )
    db.commit()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine_test)


@pytest.fixture()
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def jetons(client: TestClient) -> dict[str, str]:
    resultats = {}
    for username in ("exploitant01", "direction01"):
        reponse = client.post(
            "/auth/login",
            json={"username": username, "password": MOT_DE_PASSE_TEST},
        )
        assert reponse.status_code == 200
        resultats[username] = reponse.json()["access_token"]
    return resultats
