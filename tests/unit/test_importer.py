import csv
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.models import Base, Incident, Station, Trajet
from scripts import importer

ROOT = Path(__file__).resolve().parents[2]


def test_second_import_is_idempotent_and_does_not_log_existing_rows_as_duplicates(
    tmp_path, monkeypatch
):
    engine_test = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_test = sessionmaker(bind=engine_test, expire_on_commit=False)
    monkeypatch.setattr(importer, "SessionLocal", session_test)
    try:
        Base.metadata.create_all(engine_test)
        premier = importer.importer(ROOT / "data", tmp_path / "journal.csv")
        compteurs_premier = {
            source: valeurs.copy() for source, valeurs in premier.items()
        }
        second = importer.importer(ROOT / "data", tmp_path / "journal.csv")

        assert second == compteurs_premier
        assert second["stations.csv"]["rejetees"] == 0
        assert second["stations.csv"]["importees"] == 120
        assert second["trajets.csv"]["importees"] == 2002
        assert second["trajets.csv"]["rejetees"] == 16
        assert second["trajets.csv"]["doublons"] == 12
        assert second["incidents.csv"]["importees"] == 177
        assert second["incidents.csv"]["rejetees"] == 3

        with session_test() as db:
            assert db.scalar(select(func.count()).select_from(Station)) == 120
            assert db.scalar(select(func.count()).select_from(Trajet)) == 2002
            assert db.scalar(select(func.count()).select_from(Incident)) == 177

        with (tmp_path / "journal.csv").open(encoding="utf-8", newline="") as fichier:
            lignes = list(csv.DictReader(fichier))
        assert all(
            "identifiant déjà présent avec les mêmes données" not in ligne["motif"]
            for ligne in lignes
        )
        assert sum(
            ligne["decision"] == "doublon écarté" for ligne in lignes
        ) == 12
    finally:
        Base.metadata.drop_all(engine_test)
        engine_test.dispose()
