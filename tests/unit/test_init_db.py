import bcrypt
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.models import Base, Utilisateur
from scripts import init_db


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
            assert all(
                bcrypt.checkpw(
                    b"Formation2026!", compte.mot_de_passe_hash.encode("utf-8")
                )
                for compte in comptes
            )
            assert (
                db.scalar(select(func.count()).select_from(Utilisateur)) == 2
            )
    finally:
        Base.metadata.drop_all(engine_test)
        engine_test.dispose()
