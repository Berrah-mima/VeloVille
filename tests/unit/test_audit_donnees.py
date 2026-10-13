import csv
from pathlib import Path

from api.services.fiabilisation import (
    DonneeInvalide,
    empreinte_ligne,
    normaliser_incident,
    normaliser_station,
    normaliser_trajet,
)
from scripts.importer import auditer_sources

ROOT = Path(__file__).resolve().parents[2]


def lire_csv(nom: str) -> list[dict[str, str]]:
    with (ROOT / "data" / nom).open(encoding="utf-8", newline="") as fichier:
        return list(csv.DictReader(fichier))


def test_audit_et_fiabilisation_des_exports_fournis():
    lignes_stations = lire_csv("stations.csv")
    stations = set()
    for ligne in lignes_stations:
        normalisee, _ = normaliser_station(ligne)
        stations.add(normalisee["station_id"])
    assert len(lignes_stations) == 120
    assert len(stations) == 120

    lignes_trajets = lire_csv("trajets.csv")
    fingerprints = set()
    trajets_valides = 0
    trajets_rejetes = 0
    doublons = 0
    avertissements_trajets = []
    for ligne in lignes_trajets:
        fingerprint = empreinte_ligne(ligne)
        if fingerprint in fingerprints:
            doublons += 1
            continue
        fingerprints.add(fingerprint)
        try:
            _, avertissements = normaliser_trajet(ligne, stations)
            trajets_valides += 1
            avertissements_trajets.extend(avertissements)
        except DonneeInvalide:
            trajets_rejetes += 1
    assert (trajets_valides, trajets_rejetes, doublons) == (2002, 16, 12)
    assert trajets_valides + trajets_rejetes + doublons == len(lignes_trajets)
    assert sum(
        avertissement["colonne"] == "depart_horodatage"
        for avertissement in avertissements_trajets
    ) == 4

    lignes_incidents = lire_csv("incidents.csv")
    incidents_valides = 0
    incidents_rejetes = 0
    avertissements_incidents = []
    for ligne in lignes_incidents:
        try:
            _, avertissements = normaliser_incident(ligne, stations)
            incidents_valides += 1
            avertissements_incidents.extend(avertissements)
        except DonneeInvalide:
            incidents_rejetes += 1
    assert (incidents_valides, incidents_rejetes) == (177, 3)
    assert incidents_valides + incidents_rejetes == len(lignes_incidents)
    assert sum(
        avertissement["colonne"] == "statut"
        for avertissement in avertissements_incidents
    ) == 124
    assert sum(
        avertissement["colonne"] == "technicien"
        for avertissement in avertissements_incidents
    ) == 25


def test_journal_audit_sans_base_contient_les_six_colonnes(tmp_path):
    journal = tmp_path / "journal_import.csv"
    compteurs = auditer_sources(ROOT / "data", journal)
    assert compteurs["stations.csv"]["importees"] == 120
    assert compteurs["trajets.csv"] == {
        "lignes": 2030,
        "importees": 2002,
        "rejetees": 16,
        "doublons": 12,
    }
    assert compteurs["incidents.csv"] == {
        "lignes": 180,
        "importees": 177,
        "rejetees": 3,
        "doublons": 0,
    }
    with journal.open(encoding="utf-8", newline="") as fichier:
        lecteur = csv.DictReader(fichier)
        assert lecteur.fieldnames == [
            "fichier_source",
            "identifiant",
            "colonne",
            "valeur",
            "motif",
            "decision",
        ]
        assert any(ligne["decision"] == "rejet" for ligne in lecteur)
