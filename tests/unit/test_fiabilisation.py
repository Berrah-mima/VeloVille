from datetime import date, datetime

import pytest

from api.services.fiabilisation import (
    DonneeInvalide,
    empreinte_ligne,
    normaliser_incident,
    normaliser_station,
    normaliser_trajet,
)

STATIONS = {"S001", "S002"}


def ligne_station(**changements):
    ligne = {
        "station_id": "s001",
        "nom": " Lille - Gare ",
        "commune": "Lille",
        "capacite": "15",
        "latitude": "50.599324",
        "longitude": "3.21953",
        "date_mise_en_service": "07/08/2023",
    }
    ligne.update(changements)
    return ligne


def ligne_trajet(**changements):
    ligne = {
        "trajet_id": "T480001",
        "velo_id": "V1167",
        "depart_horodatage": "24/08/2026 08:39",
        "station_depart": "S001",
        "station_arrivee": "",
        "duree_secondes": "215",
        "type_usager": "abonne",
        "usager_ref": "Ued311b7d",
    }
    ligne.update(changements)
    return ligne


def ligne_incident(**changements):
    ligne = {
        "incident_id": "I2026-0001",
        "date_signalement": "2026-08-01 10:00",
        "cible": "velo",
        "velo_id": "V0745",
        "station_id": "",
        "type_incident": "Vandalisme",
        "statut": "En cours",
        "date_resolution": "",
        "technicien": "",
    }
    ligne.update(changements)
    return ligne


def test_station_forme_et_date_normalisees():
    resultat, avertissements = normaliser_station(ligne_station())
    assert resultat["station_id"] == "S001"
    assert resultat["date_mise_en_service"] == date(2023, 8, 7)
    assert resultat["capacite"] == 15
    assert resultat["latitude"] == 50.59932
    assert len(avertissements) == 4


def test_empreinte_ligne_stable_et_distingue_les_valeurs():
    assert empreinte_ligne({"a": "1", "b": "2"}) == empreinte_ligne(
        {"b": "2", "a": "1"}
    )
    assert empreinte_ligne({"a": "1"}) != empreinte_ligne({"a": "2"})


@pytest.mark.parametrize(
    ("colonne", "valeur"),
    [
        ("station_id", "station"),
        ("capacite", "0"),
        ("capacite", "abc"),
        ("latitude", "91"),
        ("longitude", "-181"),
        ("date_mise_en_service", "2026-02-30"),
        ("nom", ""),
    ],
)
def test_station_invalide_rejetee(colonne, valeur):
    with pytest.raises(DonneeInvalide):
        normaliser_station(ligne_station(**{colonne: valeur}))


def test_trajet_normalise_et_arrivee_absente_conservee():
    resultat, avertissements = normaliser_trajet(ligne_trajet(), STATIONS)
    assert resultat["depart_horodatage"] == datetime(2026, 8, 24, 8, 39)
    assert resultat["station_arrivee"] is None
    assert resultat["usager_ref"] == "UED311B7D"
    assert {ligne["colonne"] for ligne in avertissements} == {
        "depart_horodatage",
        "usager_ref",
    }


@pytest.mark.parametrize(
    ("colonne", "valeur"),
    [
        ("trajet_id", "bad"),
        ("velo_id", "V12"),
        ("depart_horodatage", "pas une date"),
        ("station_depart", "S999"),
        ("station_arrivee", "S999"),
        ("duree_secondes", "0"),
        ("duree_secondes", "-1"),
        ("type_usager", "visiteur"),
        ("usager_ref", ""),
    ],
)
def test_trajet_invalide_rejete(colonne, valeur):
    with pytest.raises(DonneeInvalide):
        normaliser_trajet(ligne_trajet(**{colonne: valeur}), STATIONS)


def test_trajet_occasionnel_sans_pseudonyme():
    resultat, avertissements = normaliser_trajet(
        ligne_trajet(type_usager="occasionnel", usager_ref=""), STATIONS
    )
    assert resultat["usager_ref"] is None
    assert "usager_ref" in resultat
    assert avertissements


def test_incident_statut_normalise_et_technicien_signale():
    resultat, avertissements = normaliser_incident(ligne_incident(), STATIONS)
    assert resultat["statut"] == "en_cours"
    assert resultat["technicien"] is None
    assert {ligne["colonne"] for ligne in avertissements} == {
        "statut",
        "technicien",
        "type_incident",
    }


def test_incident_resolu_valide():
    resultat, _ = normaliser_incident(
        ligne_incident(
            statut="RESOLU",
            date_resolution="2026-08-01 12:00",
            technicien="A. Martin",
        ),
        STATIONS,
    )
    assert resultat["statut"] == "resolu"
    assert resultat["date_resolution"] == datetime(2026, 8, 1, 12)


@pytest.mark.parametrize(
    "changements",
    [
        {"cible": "autre"},
        {"cible": "velo", "station_id": "S001"},
        {"cible": "station", "velo_id": "", "station_id": "S999"},
        {"statut": "clos"},
        {"statut": "resolu", "date_resolution": ""},
        {"statut": "ouvert", "date_resolution": "2026-08-01 11:00"},
        {
            "statut": "resolu",
            "date_resolution": "2026-08-01 09:00",
        },
    ],
)
def test_incident_incoherent_rejete(changements):
    with pytest.raises(DonneeInvalide):
        normaliser_incident(ligne_incident(**changements), STATIONS)
