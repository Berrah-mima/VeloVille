from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.models import Base, Utilisateur
from scripts import init_db
from scripts.postgres_settings import parametres_libpq


def test_initialisation_est_rejouable_et_cree_les_deux_comptes(monkeypatch):
    engine_test = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_test = sessionmaker(bind=engine_test, expire_on_commit=False)
    monkeypatch.setattr(init_db, "engine", engine_test)
    monkeypatch.setattr(init_db, "SessionLocal", session_test)
    try:
        init_db.initialiser()
        init_db.initialiser()
        with session_test() as db:
            comptes = db.scalars(
                select(Utilisateur).order_by(Utilisateur.username)
            ).all()
            assert len(comptes) == 2
            assert [(compte.username, compte.role) for compte in comptes] == [
                ("direction01", "direction"),
                ("exploitant01", "exploitant"),
            ]
            comptes_attendus = {
                username: (password_hash, role)
                for username, password_hash, role in init_db.DEMO_USERS
            }
            assert {
                compte.username: (compte.mot_de_passe_hash, compte.role)
                for compte in comptes
            } == comptes_attendus
            assert (
                db.scalar(select(func.count()).select_from(Utilisateur)) == 2
            )
    finally:
        Base.metadata.drop_all(engine_test)
        engine_test.dispose()


def test_parametres_sauvegarde_decodent_url_postgres_et_conservent_port():
    assert parametres_libpq(
        "postgresql+psycopg://alice:p%40ss@db.example:5544/veloville"
    ) == ("db.example", "5544", "veloville", "alice", "p@ss")


def test_parametres_sauvegarde_refusent_url_sans_base():
    try:
        parametres_libpq("postgresql+psycopg://alice:secret@localhost")
    except ValueError as erreur:
        assert "base et l'utilisateur" in str(erreur)
    else:
        raise AssertionError("Une URL sans base aurait dû être refusée.")
