"""Fiabilisation pure des lignes CSV, indépendante de la base de données."""

import json
import re
from datetime import date, datetime
from typing import Any


class DonneeInvalide(ValueError):
    def __init__(self, colonne: str, valeur: Any, motif: str):
        self.colonne = colonne
        self.valeur = valeur
        self.motif = motif
        super().__init__(motif)


def _chaine(ligne: dict[str, Any], colonne: str) -> str:
    return str(ligne.get(colonne, "") or "").strip()


def _identifiant(valeur: str, motif: str, expression: str, colonne: str) -> str:
    normalise = valeur.strip().upper()
    if not re.fullmatch(expression, normalise):
        raise DonneeInvalide(colonne, valeur, motif)
    return normalise


def _date(valeur: str, colonne: str) -> tuple[date, bool]:
    try:
        return date.fromisoformat(valeur), False
    except ValueError:
        try:
            return datetime.strptime(valeur, "%d/%m/%Y").date(), True
        except ValueError as erreur:
            raise DonneeInvalide(colonne, valeur, "date invalide") from erreur


def _horodatage(valeur: str, colonne: str) -> tuple[datetime, bool]:
    try:
        return datetime.fromisoformat(valeur), False
    except ValueError:
        for format_ in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S"):
            try:
                return datetime.strptime(valeur, format_), True
            except ValueError:
                continue
    raise DonneeInvalide(colonne, valeur, "horodatage invalide")


def empreinte_ligne(ligne: dict[str, Any]) -> str:
    """Retourne une empreinte stable utilisée pour repérer les doublons stricts."""
    return json.dumps(ligne, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------------------
# Règles de gestion RG1 à RG8
# ---------------------------------------------------------------------------


def appliquer_rg1_station(
    ligne: dict[str, Any],
) -> tuple[str, int, list[dict[str, str]]]:
    """RG1 : contrôle l'identifiant et la capacité d'une station."""
    avertissements: list[dict[str, str]] = []

    ancien_id = _chaine(ligne, "station_id")
    station_id = _identifiant(
        ancien_id,
        "format station_id invalide",
        r"S\d{3}",
        "station_id",
    )
    if ancien_id != station_id:
        avertissements.append(
            {
                "colonne": "station_id",
                "valeur": ancien_id,
                "motif": "casse ou espaces normalisés",
            }
        )

    try:
        capacite = int(_chaine(ligne, "capacite"))
    except ValueError as erreur:
        raise DonneeInvalide(
            "capacite",
            ligne.get("capacite"),
            "capacité non entière",
        ) from erreur

    if capacite <= 0:
        raise DonneeInvalide("capacite", capacite, "capacité non positive")

    return station_id, capacite, avertissements


def appliquer_rg2_stations_trajet(
    ligne: dict[str, Any],
    stations: set[str],
    station_arrivee_source: str | None,
) -> tuple[str, str | None, list[dict[str, str]]]:
    """RG2 : vérifie les références des stations de départ et d'arrivée."""
    avertissements: list[dict[str, str]] = []

    valeur_depart = _chaine(ligne, "station_depart")
    station_depart = _identifiant(
        valeur_depart,
        "format station invalide",
        r"S\d{3}",
        "station_depart",
    )
    if valeur_depart != station_depart:
        avertissements.append(
            {
                "colonne": "station_depart",
                "valeur": valeur_depart,
                "motif": "casse normalisée",
            }
        )
    if station_depart not in stations:
        raise DonneeInvalide(
            "station_depart",
            valeur_depart,
            "référence de station inconnue",
        )

    station_arrivee: str | None = None
    if station_arrivee_source is not None:
        station_arrivee = _identifiant(
            station_arrivee_source,
            "format station invalide",
            r"S\d{3}",
            "station_arrivee",
        )
        if station_arrivee_source != station_arrivee:
            avertissements.append(
                {
                    "colonne": "station_arrivee",
                    "valeur": station_arrivee_source,
                    "motif": "casse normalisée",
                }
            )
        if station_arrivee not in stations:
            raise DonneeInvalide(
                "station_arrivee",
                station_arrivee_source,
                "référence de station inconnue",
            )

    return station_depart, station_arrivee, avertissements


def appliquer_rg3_arrivee_absente(ligne: dict[str, Any]) -> str | None:
    """RG3 : une station d'arrivée vide est conservée à NULL."""
    valeur = _chaine(ligne, "station_arrivee")
    return valeur or None


def appliquer_rg4_duree(ligne: dict[str, Any]) -> int:
    """RG4 : la durée d'un trajet doit être un entier strictement positif."""
    try:
        duree = int(_chaine(ligne, "duree_secondes"))
    except ValueError as erreur:
        raise DonneeInvalide(
            "duree_secondes",
            ligne.get("duree_secondes"),
            "durée non entière",
        ) from erreur

    if duree <= 0:
        raise DonneeInvalide("duree_secondes", duree, "durée non positive")

    return duree


def appliquer_rg5_usager(
    ligne: dict[str, Any],
) -> tuple[str, str | None, list[dict[str, str]]]:
    """RG5 : contrôle le type d'usager et la cohérence de son pseudonyme."""
    avertissements: list[dict[str, str]] = []

    type_source = _chaine(ligne, "type_usager")
    type_usager = type_source.lower()

    if type_usager not in {"abonne", "occasionnel"}:
        raise DonneeInvalide(
            "type_usager",
            ligne.get("type_usager"),
            "type d'usager invalide",
        )

    if type_source != type_usager:
        avertissements.append(
            {
                "colonne": "type_usager",
                "valeur": type_source,
                "motif": "casse normalisée",
            }
        )

    reference = _chaine(ligne, "usager_ref")

    if type_usager == "abonne":
        reference_normalisee = reference.upper()
        if not re.fullmatch(r"U[0-9A-F]{8}", reference_normalisee):
            raise DonneeInvalide(
                "usager_ref",
                reference,
                "pseudonyme abonné invalide",
            )
        if reference != reference_normalisee:
            avertissements.append(
                {
                    "colonne": "usager_ref",
                    "valeur": reference,
                    "motif": "casse normalisée",
                }
            )
        return type_usager, reference_normalisee, avertissements

    if reference:
        raise DonneeInvalide(
            "usager_ref",
            reference,
            "référence interdite pour un usager occasionnel",
        )

    return type_usager, None, avertissements
def appliquer_rg6_cible_incident(
    ligne: dict[str, Any],
    stations: set[str],
) -> tuple[str, str | None, str | None, list[dict[str, str]]]:
    """RG6 : un incident cible soit un vélo, soit une station, jamais les deux."""
    avertissements: list[dict[str, str]] = []

    cible_source = _chaine(ligne, "cible")
    cible = cible_source.lower()
    if cible not in {"velo", "station"}:
        raise DonneeInvalide("cible", ligne.get("cible"), "cible invalide")

    if cible_source != cible:
        avertissements.append(
            {
                "colonne": "cible",
                "valeur": cible_source,
                "motif": "casse normalisée",
            }
        )

    velo = _chaine(ligne, "velo_id")
    station = _chaine(ligne, "station_id")

    if cible == "velo":
        velo_id = _identifiant(
            velo,
            "format velo_id invalide",
            r"V\d{4}",
            "velo_id",
        )
        if velo != velo_id:
            avertissements.append(
                {
                    "colonne": "velo_id",
                    "valeur": velo,
                    "motif": "casse normalisée",
                }
            )
        if station:
            raise DonneeInvalide(
                "station_id",
                station,
                "une cible vélo ne peut pas référencer une station",
            )
        return cible, velo_id, None, avertissements

    if velo:
        raise DonneeInvalide(
            "velo_id",
            velo,
            "une cible station ne peut pas référencer un vélo",
        )

    station_id = _identifiant(
        station,
        "format station_id invalide",
        r"S\d{3}",
        "station_id",
    )
    if station != station_id:
        avertissements.append(
            {
                "colonne": "station_id",
                "valeur": station,
                "motif": "casse normalisée",
            }
        )
    if station_id not in stations:
        raise DonneeInvalide(
            "station_id",
            station,
            "référence de station inconnue",
        )

    return cible, None, station_id, avertissements


def appliquer_rg7_statut_incident(
    ligne: dict[str, Any],
) -> tuple[str, list[dict[str, str]]]:
    """RG7 : normalise et valide le statut d'un incident."""
    avertissements: list[dict[str, str]] = []

    statut_source = _chaine(ligne, "statut")
    statuts = {
        "ouvert": "ouvert",
        "en cours": "en_cours",
        "en_cours": "en_cours",
        "resolu": "resolu",
    }

    statut = statuts.get(statut_source.lower())
    if statut is None:
        raise DonneeInvalide("statut", statut_source, "statut invalide")

    if statut_source != statut:
        avertissements.append(
            {
                "colonne": "statut",
                "valeur": statut_source,
                "motif": "casse ou format normalisé",
            }
        )

    return statut, avertissements


def appliquer_rg8_resolution_incident(
    ligne: dict[str, Any],
    statut: str,
    date_signalement: datetime,
) -> tuple[datetime | None, str | None, list[dict[str, str]]]:
    """RG8 : contrôle la résolution et le technicien d'un incident."""
    avertissements: list[dict[str, str]] = []

    resolution_source = _chaine(ligne, "date_resolution")
    date_resolution: datetime | None = None

    if statut == "resolu":
        if not resolution_source:
            raise DonneeInvalide(
                "date_resolution",
                resolution_source,
                "date de résolution absente pour un incident résolu",
            )

        date_resolution, normalise = _horodatage(
            resolution_source,
            "date_resolution",
        )
        if date_resolution < date_signalement:
            raise DonneeInvalide(
                "date_resolution",
                resolution_source,
                "résolution antérieure au signalement",
            )
        if normalise:
            avertissements.append(
                {
                    "colonne": "date_resolution",
                    "valeur": resolution_source,
                    "motif": "format d'horodatage normalisé",
                }
            )
    elif resolution_source:
        raise DonneeInvalide(
            "date_resolution",
            resolution_source,
            "date interdite pour un incident non résolu",
        )

    technicien = _chaine(ligne, "technicien") or None
    if statut != "ouvert" and technicien is None:
        avertissements.append(
            {
                "colonne": "technicien",
                "valeur": "",
                "motif": "technicien absent malgré la prise en charge",
            }
        )

    return date_resolution, technicien, avertissements
# ---------------------------------------------------------------------------
# Normalisation complète des trois fichiers CSV
# ---------------------------------------------------------------------------


def normaliser_station(
    ligne: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    resultat = dict(ligne)
    avertissements: list[dict[str, str]] = []

    station_id, capacite, avertissements_rg1 = appliquer_rg1_station(ligne)
    resultat["station_id"] = station_id
    resultat["capacite"] = capacite
    avertissements.extend(avertissements_rg1)

    for colonne in ("nom", "commune"):
        valeur_brute = str(ligne.get(colonne, "") or "")
        valeur = _chaine(ligne, colonne)
        if not valeur:
            raise DonneeInvalide(colonne, valeur, "valeur obligatoire absente")
        if valeur_brute != valeur:
            avertissements.append(
                {
                    "colonne": colonne,
                    "valeur": valeur_brute,
                    "motif": "espaces périphériques supprimés",
                }
            )
        resultat[colonne] = valeur

    for colonne, minimum, maximum in (
        ("latitude", -90, 90),
        ("longitude", -180, 180),
    ):
        valeur = _chaine(ligne, colonne)
        try:
            coordonnee = round(float(valeur), 5)
        except ValueError as erreur:
            raise DonneeInvalide(colonne, valeur, "coordonnée invalide") from erreur
        if not minimum <= coordonnee <= maximum:
            raise DonneeInvalide(colonne, valeur, "coordonnée hors limites")
        resultat[colonne] = coordonnee
        if float(valeur) != coordonnee:
            avertissements.append(
                {
                    "colonne": colonne,
                    "valeur": valeur,
                    "motif": "coordonnée arrondie à cinq décimales",
                }
            )

    valeur_date = _chaine(ligne, "date_mise_en_service")
    resultat["date_mise_en_service"], normalisee = _date(
        valeur_date,
        "date_mise_en_service",
    )
    if normalisee:
        avertissements.append(
            {
                "colonne": "date_mise_en_service",
                "valeur": valeur_date,
                "motif": "format de date normalisé",
            }
        )

    return resultat, avertissements


def normaliser_trajet(
    ligne: dict[str, Any],
    stations: set[str],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    resultat = dict(ligne)
    avertissements: list[dict[str, str]] = []

    identifiant = _chaine(ligne, "trajet_id")
    resultat["trajet_id"] = _identifiant(
        identifiant,
        "format trajet_id invalide",
        r"T\d{6}",
        "trajet_id",
    )
    if str(ligne.get("trajet_id", "")) != resultat["trajet_id"]:
        avertissements.append(
            {
                "colonne": "trajet_id",
                "valeur": str(ligne.get("trajet_id", "")),
                "motif": "casse ou espaces normalisés",
            }
        )

    velo = _chaine(ligne, "velo_id")
    resultat["velo_id"] = _identifiant(
        velo,
        "format velo_id invalide",
        r"V\d{4}",
        "velo_id",
    )
    if str(ligne.get("velo_id", "")) != resultat["velo_id"]:
        avertissements.append(
            {
                "colonne": "velo_id",
                "valeur": str(ligne.get("velo_id", "")),
                "motif": "casse ou espaces normalisés",
            }
        )

    horodatage = _chaine(ligne, "depart_horodatage")
    resultat["depart_horodatage"], normalise = _horodatage(
        horodatage,
        "depart_horodatage",
    )
    if normalise:
        avertissements.append(
            {
                "colonne": "depart_horodatage",
                "valeur": horodatage,
                "motif": "format d'horodatage normalisé",
            }
        )

    station_arrivee_source = appliquer_rg3_arrivee_absente(ligne)
    station_depart, station_arrivee, avertissements_rg2 = (
        appliquer_rg2_stations_trajet(
            ligne,
            stations,
            station_arrivee_source,
        )
    )
    resultat["station_depart"] = station_depart
    resultat["station_arrivee"] = station_arrivee
    avertissements.extend(avertissements_rg2)

    resultat["duree_secondes"] = appliquer_rg4_duree(ligne)

    type_usager, usager_ref, avertissements_rg5 = appliquer_rg5_usager(ligne)
    resultat["type_usager"] = type_usager
    resultat["usager_ref"] = usager_ref
    avertissements.extend(avertissements_rg5)

    return resultat, avertissements


def normaliser_incident(
    ligne: dict[str, Any],
    stations: set[str],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    resultat = dict(ligne)
    avertissements: list[dict[str, str]] = []

    incident_id = _chaine(ligne, "incident_id")
    resultat["incident_id"] = _identifiant(
        incident_id,
        "format incident_id invalide",
        r"I2026-\d{4}",
        "incident_id",
    )
    if incident_id != resultat["incident_id"]:
        avertissements.append(
            {
                "colonne": "incident_id",
                "valeur": incident_id,
                "motif": "casse ou espaces normalisés",
            }
        )

    date_signalement = _chaine(ligne, "date_signalement")
    resultat["date_signalement"], normalise = _horodatage(
        date_signalement,
        "date_signalement",
    )
    if normalise:
        avertissements.append(
            {
                "colonne": "date_signalement",
                "valeur": date_signalement,
                "motif": "format d'horodatage normalisé",
            }
        )

    cible, velo_id, station_id, avertissements_rg6 = appliquer_rg6_cible_incident(
        ligne,
        stations,
    )
    resultat["cible"] = cible
    resultat["velo_id"] = velo_id
    resultat["station_id"] = station_id
    avertissements.extend(avertissements_rg6)

    statut, avertissements_rg7 = appliquer_rg7_statut_incident(ligne)
    resultat["statut"] = statut
    avertissements.extend(avertissements_rg7)

    date_resolution, technicien, avertissements_rg8 = (
        appliquer_rg8_resolution_incident(
            ligne,
            statut,
            resultat["date_signalement"],
        )
    )
    resultat["date_resolution"] = date_resolution
    resultat["technicien"] = technicien
    avertissements.extend(avertissements_rg8)

    type_incident = _chaine(ligne, "type_incident")
    if not type_incident:
        raise DonneeInvalide(
            "type_incident",
            type_incident,
            "type d'incident absent",
        )
    resultat["type_incident"] = type_incident.lower()
    if resultat["type_incident"] != type_incident:
        avertissements.append(
            {
                "colonne": "type_incident",
                "valeur": type_incident,
                "motif": "casse normalisée",
            }
        )

    return resultat, avertissements
