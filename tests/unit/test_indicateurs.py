from datetime import date

from api.models import Incident
from api.services.indicateurs import (
    activite_par_jour,
    incidents_par_statut,
    stations_actives,
)
from api.services.incidents import appliquer_transition


def test_activite_par_jour_est_agregee_et_bornee(db_session):
    resultat = activite_par_jour(db_session, date(2026, 8, 24), date(2026, 8, 24))
    assert resultat == [{"jour": "2026-08-24", "nb_trajets": 2}]
    assert len(activite_par_jour(db_session)) == 2


def test_stations_actives_triees_et_arrivees_absentes_ignorees(db_session):
    resultat = stations_actives(db_session, 2)
    assert [ligne["station_id"] for ligne in resultat] == ["S001", "S002"]
    assert resultat[0]["nb_departs"] == 2
    assert resultat[0]["nb_arrivees"] == 0
    assert stations_actives(db_session, 0) == []


def test_incidents_par_statut_et_delai_moyen(db_session):
    resultat = incidents_par_statut(db_session)
    assert resultat["donnees"] == [
        {"statut": "ouvert", "nb_incidents": 1},
        {"statut": "resolu", "nb_incidents": 1},
    ]
    assert resultat["delai_moyen_resolution_heures"] == 2.5


def test_delai_moyen_est_null_sans_incident_resolu(db_session):
    incident = db_session.get(Incident, "I2026-0002")
    db_session.delete(incident)
    db_session.commit()
    assert incidents_par_statut(db_session)["delai_moyen_resolution_heures"] is None


def test_transition_incident_resolu_renseigne_date_et_interdit_retransition(db_session):
    from datetime import datetime

    incident = db_session.get(Incident, "I2026-0001")
    applique = appliquer_transition(
        incident, "en_cours", datetime(2026, 8, 1, 10)
    )
    assert applique.statut == "en_cours"
    applique = appliquer_transition(
        applique, "resolu", datetime(2026, 8, 1, 11)
    )
    assert applique.statut == "resolu"
    assert applique.date_resolution == datetime(2026, 8, 1, 11)
    try:
        appliquer_transition(applique, "en_cours", datetime(2026, 8, 1, 12))
    except ValueError as erreur:
        assert str(erreur) == "Transition de statut non autorisee"
    else:
        raise AssertionError("Une transition depuis resolu aurait dû être refusée.")
