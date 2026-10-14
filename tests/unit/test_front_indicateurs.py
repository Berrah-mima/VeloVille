from pathlib import Path
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest

from front import api_client
from front.api_client import ErreurApi

ROOT = Path(__file__).resolve().parents[2]
PAGE_INDICATEURS = ROOT / "front" / "pages" / "3_Indicateurs.py"


def test_page_indicateurs_fait_trois_appels_et_recharge_apres_navigation(
    monkeypatch,
):
    activite = Mock(
        return_value={
            "donnees": [
                {"jour": "2026-08-24", "nb_trajets": 3},
                {"jour": "2026-08-25", "nb_trajets": 2},
            ]
        }
    )
    stations = Mock(
        return_value={
            "donnees": [
                {
                    "station_id": "S001",
                    "nom": "Centre",
                    "nb_departs": 3,
                    "nb_arrivees": 2,
                }
            ]
        }
    )
    incidents = Mock(
        return_value={
            "donnees": [{"statut": "resolu", "nb_incidents": 1}],
            "delai_moyen_resolution_heures": 2.5,
        }
    )
    monkeypatch.setattr(api_client, "lire_activite", activite)
    monkeypatch.setattr(api_client, "lire_stations_actives", stations)
    monkeypatch.setattr(api_client, "lire_incidents_par_statut", incidents)

    app = AppTest.from_file(str(PAGE_INDICATEURS))
    app.session_state["access_token"] = "test-token"
    app.run(timeout=10)

    assert not app.exception
    actualiser = next(button for button in app.button if button.label == "Actualiser")
    assert len(app.metric) == 3
    assert [metric.value for metric in app.metric] == ["5", "1", "2.5"]
    assert (activite.call_count, stations.call_count, incidents.call_count) == (1, 1, 1)

    actualiser.click()
    app.run(timeout=10)

    assert not app.exception
    assert len(app.metric) == 3
    assert (activite.call_count, stations.call_count, incidents.call_count) == (2, 2, 2)


def test_page_indicateurs_affiche_une_erreur_si_un_appel_api_echoue(monkeypatch):
    monkeypatch.setattr(
        api_client,
        "lire_activite",
        Mock(side_effect=ErreurApi("L'API est injoignable.")),
    )
    app = AppTest.from_file(str(PAGE_INDICATEURS))
    app.session_state["access_token"] = "test-token"
    app.run(timeout=10)

    assert not app.exception
    assert any("L'API est injoignable." in erreur.value for erreur in app.error)


def test_page_indicateurs_affiche_les_trois_etats_vides(monkeypatch):
    monkeypatch.setattr(api_client, "lire_activite", Mock(return_value={"donnees": []}))
    monkeypatch.setattr(api_client, "lire_stations_actives", Mock(return_value={"donnees": []}))
    monkeypatch.setattr(
        api_client,
        "lire_incidents_par_statut",
        Mock(return_value={"donnees": [], "delai_moyen_resolution_heures": None}),
    )
    app = AppTest.from_file(str(PAGE_INDICATEURS))
    app.session_state["access_token"] = "test-token"
    app.run(timeout=10)

    assert not app.exception
    assert [element.value for element in app.info] == [
        "Aucun résultat pour ces critères.",
        "Aucune station active pour ces critères.",
        "Aucun incident à afficher.",
    ]
