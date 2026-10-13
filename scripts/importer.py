"""Import idempotent des CSV et journalisation des anomalies."""

import argparse
import csv
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models import Incident, Station, Trajet
from api.services.fiabilisation import (
    DonneeInvalide,
    empreinte_ligne,
    normaliser_incident,
    normaliser_station,
    normaliser_trajet,
)

LIGNES_JOURNAL: list[dict[str, str]] = []


def _lire_csv(chemin: Path) -> list[dict[str, str]]:
    with chemin.open("r", encoding="utf-8-sig", newline="") as fichier:
        return list(csv.DictReader(fichier))


def _journaliser(
    source: str,
    identifiant: str,
    colonne: str,
    valeur: Any,
    motif: str,
    decision: str,
) -> None:
    LIGNES_JOURNAL.append(
        {
            "fichier_source": source,
            "identifiant": identifiant,
            "colonne": colonne,
            "valeur": "" if valeur is None else str(valeur),
            "motif": motif,
            "decision": decision,
        }
    )


def _equivalent_existant(objet: Any, donnees: dict[str, Any]) -> bool:
    for colonne, valeur in donnees.items():
        valeur_existante = getattr(objet, colonne)
        if colonne in {"latitude", "longitude"}:
            if round(float(valeur_existante), 5) != round(float(valeur), 5):
                return False
        elif valeur_existante != valeur:
            return False
    return True


def _importer_fichier(
    db: Session,
    dossier: Path,
    nom_fichier: str,
    modele: type,
    normaliser: Callable,
    id_colonne: str,
    stations: set[str] | None = None,
) -> dict[str, int]:
    compteurs = {"lignes": 0, "importees": 0, "rejetees": 0, "doublons": 0}
    deja_vues: set[str] = set()
    for ligne in _lire_csv(dossier / nom_fichier):
        compteurs["lignes"] += 1
        empreinte = empreinte_ligne(ligne)
        identifiant = str(ligne.get(id_colonne, "")).strip()
        if empreinte in deja_vues:
            compteurs["doublons"] += 1
            _journaliser(
                nom_fichier,
                identifiant,
                "",
                "",
                "ligne strictement identique déjà traitée",
                "doublon écarté",
            )
            continue
        deja_vues.add(empreinte)
        try:
            if stations is None:
                donnees, avertissements = normaliser(ligne)
            else:
                donnees, avertissements = normaliser(ligne, stations)
        except DonneeInvalide as erreur:
            compteurs["rejetees"] += 1
            _journaliser(
                nom_fichier,
                identifiant,
                erreur.colonne,
                erreur.valeur,
                erreur.motif,
                "rejet",
            )
            continue
        for avertissement in avertissements:
            _journaliser(
                nom_fichier,
                identifiant,
                avertissement["colonne"],
                avertissement["valeur"],
                avertissement["motif"],
                "normalisation (ligne importée)",
            )
        existant = db.get(modele, donnees[id_colonne])
        if existant is not None:
            if _equivalent_existant(existant, donnees):
                compteurs["doublons"] += 1
                _journaliser(
                    nom_fichier,
                    identifiant,
                    id_colonne,
                    identifiant,
                    "identifiant déjà présent avec les mêmes données",
                    "doublon écarté",
                )
            else:
                compteurs["rejetees"] += 1
                _journaliser(
                    nom_fichier,
                    identifiant,
                    id_colonne,
                    identifiant,
                    "identifiant déjà présent avec des données différentes",
                    "rejet",
                )
            continue
        db.add(modele(**donnees))
        db.flush()
        compteurs["importees"] += 1
    db.commit()
    return compteurs


def _ecrire_journal(lignes: list[dict[str, str]], chemin: Path) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    colonnes = ["fichier_source", "identifiant", "colonne", "valeur", "motif", "decision"]
    with chemin.open("w", encoding="utf-8", newline="") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=colonnes)
        writer.writeheader()
        writer.writerows(lignes)


def auditer_sources(
    dossier: Path, journal: Path
) -> dict[str, dict[str, int]]:
    """Normalise et compte les CSV sans se connecter à PostgreSQL."""
    LIGNES_JOURNAL.clear()
    compteurs: dict[str, dict[str, int]] = {}

    stations_valides: set[str] = set()
    stations_vues: set[str] = set()
    stations_ids: set[str] = set()
    compteurs["stations.csv"] = {
        "lignes": 0,
        "importees": 0,
        "rejetees": 0,
        "doublons": 0,
    }
    for ligne in _lire_csv(dossier / "stations.csv"):
        compteurs["stations.csv"]["lignes"] += 1
        if empreinte_ligne(ligne) in stations_vues:
            compteurs["stations.csv"]["doublons"] += 1
            _journaliser(
                "stations.csv",
                ligne.get("station_id", ""),
                "",
                "",
                "ligne strictement identique déjà traitée",
                "doublon écarté",
            )
            continue
        stations_vues.add(empreinte_ligne(ligne))
        try:
            donnees, avertissements = normaliser_station(ligne)
        except DonneeInvalide as erreur:
            compteurs["stations.csv"]["rejetees"] += 1
            _journaliser(
                "stations.csv",
                str(ligne.get("station_id", "")),
                erreur.colonne,
                erreur.valeur,
                erreur.motif,
                "rejet",
            )
            continue
        identifiant = donnees["station_id"]
        if identifiant in stations_ids:
            compteurs["stations.csv"]["rejetees"] += 1
            _journaliser(
                "stations.csv",
                identifiant,
                "station_id",
                identifiant,
                "identifiant déjà présent avec des données différentes",
                "rejet",
            )
            continue
        stations_ids.add(identifiant)
        stations_valides.add(identifiant)
        compteurs["stations.csv"]["importees"] += 1
        for avertissement in avertissements:
            _journaliser(
                "stations.csv",
                identifiant,
                avertissement["colonne"],
                avertissement["valeur"],
                avertissement["motif"],
                "normalisation (ligne importée)",
            )

    for nom_fichier, normaliser, id_colonne in (
        ("trajets.csv", normaliser_trajet, "trajet_id"),
        ("incidents.csv", normaliser_incident, "incident_id"),
    ):
        compteurs[nom_fichier] = {
            "lignes": 0,
            "importees": 0,
            "rejetees": 0,
            "doublons": 0,
        }
        empreintes_vues: set[str] = set()
        identifiants_vus: set[str] = set()
        for ligne in _lire_csv(dossier / nom_fichier):
            compteurs[nom_fichier]["lignes"] += 1
            empreinte = empreinte_ligne(ligne)
            identifiant_source = str(ligne.get(id_colonne, "")).strip()
            if empreinte in empreintes_vues:
                compteurs[nom_fichier]["doublons"] += 1
                _journaliser(
                    nom_fichier,
                    identifiant_source,
                    "",
                    "",
                    "ligne strictement identique déjà traitée",
                    "doublon écarté",
                )
                continue
            empreintes_vues.add(empreinte)
            try:
                donnees, avertissements = normaliser(ligne, stations_valides)
            except DonneeInvalide as erreur:
                compteurs[nom_fichier]["rejetees"] += 1
                _journaliser(
                    nom_fichier,
                    identifiant_source,
                    erreur.colonne,
                    erreur.valeur,
                    erreur.motif,
                    "rejet",
                )
                continue
            identifiant = donnees[id_colonne]
            if identifiant in identifiants_vus:
                compteurs[nom_fichier]["rejetees"] += 1
                _journaliser(
                    nom_fichier,
                    identifiant,
                    id_colonne,
                    identifiant,
                    "identifiant déjà présent avec des données différentes",
                    "rejet",
                )
                continue
            identifiants_vus.add(identifiant)
            compteurs[nom_fichier]["importees"] += 1
            for avertissement in avertissements:
                _journaliser(
                    nom_fichier,
                    identifiant,
                    avertissement["colonne"],
                    avertissement["valeur"],
                    avertissement["motif"],
                    "normalisation (ligne importée)",
                )
    _ecrire_journal(LIGNES_JOURNAL, journal)
    return compteurs


def importer(dossier: Path, journal: Path) -> dict[str, dict[str, int]]:
    LIGNES_JOURNAL.clear()
    with SessionLocal() as db:
        compteurs: dict[str, dict[str, int]] = {}
        compteurs["stations.csv"] = _importer_fichier(
            db, dossier, "stations.csv", Station, normaliser_station, "station_id"
        )
        station_ids = {identifiant for (identifiant,) in db.query(Station.station_id).all()}
        compteurs["trajets.csv"] = _importer_fichier(
            db, dossier, "trajets.csv", Trajet, normaliser_trajet, "trajet_id", station_ids
        )
        compteurs["incidents.csv"] = _importer_fichier(
            db, dossier, "incidents.csv", Incident, normaliser_incident, "incident_id", station_ids
        )
    _ecrire_journal(LIGNES_JOURNAL, journal)
    return compteurs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dossier", type=Path, default=ROOT / "data")
    parser.add_argument(
        "--journal",
        type=Path,
        default=ROOT / "docs" / "journal_import.csv",
    )
    parser.add_argument(
        "--audit-seul",
        action="store_true",
        help="valide les CSV et produit le journal sans accès à PostgreSQL",
    )
    args = parser.parse_args()
    compteurs = (
        auditer_sources(args.dossier, args.journal)
        if args.audit_seul
        else importer(args.dossier, args.journal)
    )
    for source, valeurs in compteurs.items():
        print(
            f"{source}: lignes={valeurs['lignes']}, importées={valeurs['importees']}, "
            f"rejetées={valeurs['rejetees']}, doublons écartés={valeurs['doublons']}"
        )
    print(f"Journal des rejets et avertissements : {args.journal}")


if __name__ == "__main__":
    main()
