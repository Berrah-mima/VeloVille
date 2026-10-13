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


def normaliser_station(ligne: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    resultat = dict(ligne)
    avertissements: list[dict[str, str]] = []
    ancien_id = _chaine(ligne, "station_id")
    station_id = _identifiant(ancien_id, "format station_id invalide", r"S\d{3}", "station_id")
    if ancien_id != station_id:
        avertissements.append(
            {"colonne": "station_id", "valeur": ancien_id, "motif": "casse ou espaces normalisés"}
        )
    resultat["station_id"] = station_id
    for colonne in ("nom", "commune"):
        valeur_brute = str(ligne.get(colonne, "") or "")
        valeur = _chaine(ligne, colonne)
        if not valeur:
            raise DonneeInvalide(colonne, valeur, "valeur obligatoire absente")
        if valeur_brute != valeur:
            avertissements.append(
                {"colonne": colonne, "valeur": valeur_brute, "motif": "espaces périphériques supprimés"}
            )
        resultat[colonne] = valeur
    try:
        capacite = int(_chaine(ligne, "capacite"))
    except ValueError as erreur:
        raise DonneeInvalide("capacite", ligne.get("capacite"), "capacité non entière") from erreur
    if capacite <= 0:
        raise DonneeInvalide("capacite", capacite, "capacité non positive")
    resultat["capacite"] = capacite
    for colonne, minimum, maximum in (("latitude", -90, 90), ("longitude", -180, 180)):
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
                {"colonne": colonne, "valeur": valeur, "motif": "coordonnée arrondie à cinq décimales"}
            )
    valeur_date = _chaine(ligne, "date_mise_en_service")
    resultat["date_mise_en_service"], normalisee = _date(valeur_date, "date_mise_en_service")
    if normalisee:
        avertissements.append(
            {"colonne": "date_mise_en_service", "valeur": valeur_date, "motif": "format de date normalisé"}
        )
    return resultat, avertissements


def normaliser_trajet(
    ligne: dict[str, Any], stations: set[str]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    resultat = dict(ligne)
    avertissements: list[dict[str, str]] = []
    identifiant = _chaine(ligne, "trajet_id")
    resultat["trajet_id"] = _identifiant(
        identifiant, "format trajet_id invalide", r"T\d{6}", "trajet_id"
    )
    if str(ligne.get("trajet_id", "")) != resultat["trajet_id"]:
        avertissements.append(
            {"colonne": "trajet_id", "valeur": str(ligne.get("trajet_id", "")), "motif": "casse ou espaces normalisés"}
        )
    velo = _chaine(ligne, "velo_id")
    resultat["velo_id"] = _identifiant(velo, "format velo_id invalide", r"V\d{4}", "velo_id")
    if str(ligne.get("velo_id", "")) != resultat["velo_id"]:
        avertissements.append(
            {"colonne": "velo_id", "valeur": str(ligne.get("velo_id", "")), "motif": "casse ou espaces normalisés"}
        )
    horodatage = _chaine(ligne, "depart_horodatage")
    resultat["depart_horodatage"], normalise = _horodatage(
        horodatage, "depart_horodatage"
    )
    if normalise:
        avertissements.append(
            {
                "colonne": "depart_horodatage",
                "valeur": horodatage,
                "motif": "format d'horodatage normalisé",
            }
        )
    for colonne, facultatif in (("station_depart", False), ("station_arrivee", True)):
        valeur = _chaine(ligne, colonne)
        if not valeur and facultatif:
            resultat[colonne] = None
            continue
        station_id = _identifiant(valeur, "format station invalide", r"S\d{3}", colonne)
        if valeur != station_id:
            avertissements.append(
                {"colonne": colonne, "valeur": valeur, "motif": "casse normalisée"}
            )
        if station_id not in stations:
            raise DonneeInvalide(colonne, valeur, "référence de station inconnue")
        resultat[colonne] = station_id
    try:
        duree = int(_chaine(ligne, "duree_secondes"))
    except ValueError as erreur:
        raise DonneeInvalide(
            "duree_secondes", ligne.get("duree_secondes"), "durée non entière"
        ) from erreur
    if duree <= 0:
        raise DonneeInvalide("duree_secondes", duree, "durée non positive")
    resultat["duree_secondes"] = duree
    type_usager = _chaine(ligne, "type_usager").lower()
    if type_usager not in {"abonne", "occasionnel"}:
        raise DonneeInvalide("type_usager", ligne.get("type_usager"), "type d'usager invalide")
    resultat["type_usager"] = type_usager
    if _chaine(ligne, "type_usager") != type_usager:
        avertissements.append(
            {
                "colonne": "type_usager",
                "valeur": _chaine(ligne, "type_usager"),
                "motif": "casse normalisée",
            }
        )
    reference = _chaine(ligne, "usager_ref")
    if type_usager == "abonne":
        reference_normalisee = reference.upper()
        if not re.fullmatch(r"U[0-9A-F]{8}", reference_normalisee):
            raise DonneeInvalide("usager_ref", reference, "pseudonyme abonné invalide")
        if reference != reference_normalisee:
            avertissements.append(
                {"colonne": "usager_ref", "valeur": reference, "motif": "casse normalisée"}
            )
        resultat["usager_ref"] = reference_normalisee
    elif reference:
        raise DonneeInvalide(
            "usager_ref", reference, "référence interdite pour un usager occasionnel"
        )
    else:
        resultat["usager_ref"] = None
    return resultat, avertissements


def normaliser_incident(
    ligne: dict[str, Any], stations: set[str]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    resultat = dict(ligne)
    avertissements: list[dict[str, str]] = []
    incident_id = _chaine(ligne, "incident_id")
    resultat["incident_id"] = _identifiant(
        incident_id, "format incident_id invalide", r"I2026-\d{4}", "incident_id"
    )
    if incident_id != resultat["incident_id"]:
        avertissements.append(
            {"colonne": "incident_id", "valeur": incident_id, "motif": "casse ou espaces normalisés"}
        )
    date_signalement = _chaine(ligne, "date_signalement")
    resultat["date_signalement"], normalise = _horodatage(
        date_signalement, "date_signalement"
    )
    if normalise:
        avertissements.append(
            {
                "colonne": "date_signalement",
                "valeur": date_signalement,
                "motif": "format d'horodatage normalisé",
            }
        )
    cible = _chaine(ligne, "cible").lower()
    if cible not in {"velo", "station"}:
        raise DonneeInvalide("cible", ligne.get("cible"), "cible invalide")
    resultat["cible"] = cible
    if _chaine(ligne, "cible") != cible:
        avertissements.append(
            {"colonne": "cible", "valeur": _chaine(ligne, "cible"), "motif": "casse normalisée"}
        )
    velo = _chaine(ligne, "velo_id")
    station = _chaine(ligne, "station_id")
    if cible == "velo":
        resultat["velo_id"] = _identifiant(
            velo, "format velo_id invalide", r"V\d{4}", "velo_id"
        )
        if velo != resultat["velo_id"]:
            avertissements.append(
                {"colonne": "velo_id", "valeur": velo, "motif": "casse normalisée"}
            )
        if station:
            raise DonneeInvalide(
                "station_id", station, "une cible vélo ne peut pas référencer une station"
            )
        resultat["station_id"] = None
    else:
        if velo:
            raise DonneeInvalide(
                "velo_id", velo, "une cible station ne peut pas référencer un vélo"
            )
        station_id = _identifiant(
            station, "format station_id invalide", r"S\d{3}", "station_id"
        )
        if station != station_id:
            avertissements.append(
                {"colonne": "station_id", "valeur": station, "motif": "casse normalisée"}
            )
        if station_id not in stations:
            raise DonneeInvalide("station_id", station, "référence de station inconnue")
        resultat["station_id"] = station_id
        resultat["velo_id"] = None
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
    resultat["statut"] = statut
    if statut_source != statut:
        avertissements.append(
            {"colonne": "statut", "valeur": statut_source, "motif": "casse ou format normalisé"}
        )
    resolution_source = _chaine(ligne, "date_resolution")
    if statut == "resolu":
        if not resolution_source:
            raise DonneeInvalide(
                "date_resolution", resolution_source, "date de résolution absente pour un incident résolu"
            )
        resolution, normalise = _horodatage(resolution_source, "date_resolution")
        if resolution < resultat["date_signalement"]:
            raise DonneeInvalide(
                "date_resolution", resolution_source, "résolution antérieure au signalement"
            )
        resultat["date_resolution"] = resolution
        if normalise:
            avertissements.append(
                {
                    "colonne": "date_resolution",
                    "valeur": resolution_source,
                    "motif": "format d'horodatage normalisé",
                }
            )
    else:
        if resolution_source:
            raise DonneeInvalide(
                "date_resolution", resolution_source, "date interdite pour un incident non résolu"
            )
        resultat["date_resolution"] = None
    technicien = _chaine(ligne, "technicien")
    resultat["technicien"] = technicien or None
    if statut != "ouvert" and not technicien:
        avertissements.append(
            {
                "colonne": "technicien",
                "valeur": "",
                "motif": "technicien absent malgré la prise en charge",
            }
        )
    type_incident = _chaine(ligne, "type_incident")
    if not type_incident:
        raise DonneeInvalide("type_incident", type_incident, "type d'incident absent")
    resultat["type_incident"] = type_incident.lower()
    if resultat["type_incident"] != type_incident:
        avertissements.append(
            {"colonne": "type_incident", "valeur": type_incident, "motif": "casse normalisée"}
        )
    return resultat, avertissements
