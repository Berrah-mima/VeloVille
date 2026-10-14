# Schéma des données et audit des exports

## Modèle logique

```text
station(
  station_id PK, nom, commune, capacite, latitude, longitude,
  date_mise_en_service
)
trajet(
  trajet_id PK, velo_id, depart_horodatage,
  station_depart FK -> station.station_id NOT NULL,
  station_arrivee FK -> station.station_id NULL,
  duree_secondes, type_usager, usager_ref NULL
)
incident(
  incident_id PK, date_signalement, cible, velo_id NULL,
  station_id FK -> station.station_id NULL, type_incident, statut,
  date_resolution NULL, technicien NULL
)
utilisateur(
  id_utilisateur PK, username UNIQUE, mot_de_passe_hash, role
)
```

## Tables et contraintes

- **station** : référentiel des stations ; `station_id` est la clé primaire,
  `capacite` est strictement positive et les coordonnées sont dans les bornes
  WGS84.
- **trajet** : chaque trajet référence obligatoirement une station de départ.
  La station d'arrivée est nullable pour les vélos non restitués ; les
  références renseignées sont des clés étrangères. La durée est positive.
  `type_usager` vaut `abonne` ou `occasionnel` ; seul un abonné porte un
  `usager_ref`.
- **incident** : la cible vaut `velo` ou `station` et une seule référence
  correspondante est renseignée. La station cible est une clé étrangère. Les
  statuts sont limités à `ouvert`, `en_cours`, `resolu`. Une date de
  résolution est obligatoire si et seulement si le statut est résolu, et ne
  précède pas le signalement.
- **utilisateur** : identifiant auto-incrémenté, nom d'utilisateur unique,
  hachage bcrypt du mot de passe et rôle limité à `exploitant` ou `direction`.

Les contraintes relationnelles sont déclarées dans `sql/schema.sql` et
reprises au niveau ORM dans `api/models.py`. Les contrôles dépendant des
données source (formats d'identifiants, normalisation des horodatages,
vérification des pseudonymes et références croisées) sont exécutés par les
fonctions pures de `api/services/fiabilisation.py` avant insertion.

## Règles RG1 à RG8

| Règle | Application |
|---|---|
| RG1 — identifiant et capacité station | Clé primaire et `CHECK (capacite > 0)` ; validation du format dans l'import. |
| RG2 — stations de départ et d'arrivée | Clés étrangères ; identifiant de départ obligatoire ; référence d'arrivée renseignée mais inconnue rejetée. |
| RG3 — arrivée inconnue à l'export | Valeur vide conservée à `NULL`; le trajet reste importé et ne compte comme arrivée nulle part. |
| RG4 — durée | `CHECK (duree_secondes > 0)` et validation avant insertion. |
| RG5 — pseudonyme usager | Check de cohérence `type_usager`/`usager_ref`; aucune donnée nominative n'est stockée. |
| RG6 — cible incident | Check d'exclusivité vélo/station et clé étrangère pour la station. |
| RG7 — statuts et transitions | Check des statuts en base ; transitions métier contrôlées sur le PUT par l'API. |
| RG8 — résolution et technicien | Checks d'état/date et d'ordre des dates ; technicien absent après prise en charge journalisé en avertissement. |

## Audit des fichiers fournis

Audit réalisé sur les 120, 2 030 et 180 lignes sources, hors en-tête.
Les compteurs ci-dessous sont des constats sur les CSV fournis ; les nombres
importés sont les résultats attendus après application des règles, à confirmer
par `scripts/importer.py` contre la base de recette.

| Fichier | Défaut constaté | Volume | Traitement |
|---|---|---:|---|
| stations.csv | Identifiants dupliqués, capacité non positive, coordonnées/date invalides, champs obligatoires vides | 0 | 120 lignes importées, aucune normalisation nécessaire. |
| trajets.csv | Lignes strictement identiques (doublons) | 12 lignes excédentaires | Une copie conservée ; 12 doublons écartés. |
| trajets.csv | `velo_id` avec casse ou espaces périphériques hétérogènes | 6 | Identifiants normalisés (majuscules et suppression des espaces) puis importés. |
| trajets.csv | `usager_ref` en minuscules ou avec espaces périphériques | 1 186 | Pseudonymes normalisés en majuscules après validation ; aucune donnée nominative n'est ajoutée. |
| trajets.csv | Horodatage départ au format `JJ/MM/AAAA HH:MM` | 5 | Quatre lignes valides sont normalisées en ISO et importées avec avertissement. La cinquième est rejetée pour sa référence de station d'arrivée invalide. |
| trajets.csv | Station d'arrivée renseignée mais inconnue (`S999`) | 7 | Rejet RG2 ; seule une arrivée réellement vide devient `NULL`. |
| trajets.csv | Durée nulle ou négative | 10 occurrences, dont une ligne déjà comptée comme doublon | 9 lignes uniques rejetées pour durée, plus 7 références invalides. |
| incidents.csv | Statuts en casse/forme hétérogène (`RESOLU`, `En cours`) | 125 | 124 lignes valides sont normalisées vers les valeurs canoniques ; une ligne au statut non canonique est aussi rejetée pour incohérence de date. |
| incidents.csv | `type_incident` avec casse hétérogène | 24 | Texte normalisé en minuscules et ligne importée avec avertissement. |
| incidents.csv | Résolution antérieure au signalement | 3 | Rejet RG8. |
| incidents.csv | Technicien absent alors que l'incident est pris en charge ou résolu | 25 (8 `en_cours`, 17 `resolu`) | Ligne importée, avertissement ; absence non bloquante. |

Les formats et références des autres colonnes contrôlées sont conformes aux
domaines attendus. Totaux attendus au premier import : 120 stations, 2 002
trajets et 177 incidents. Pour les trajets, 2 002 + 16 rejets + 12 doublons =
2 030 lignes source. Pour les incidents, 177 + 3 rejets = 180. Les
avertissements sont des annotations de lignes importées et ne constituent
pas une troisième catégorie de comptage.

Le fichier `docs/journal_import.csv` est régénéré à chaque exécution. Il
contient une ligne par rejet, doublon écarté ou avertissement, avec les six
colonnes attendues : fichier source, identifiant, colonne, valeur, motif et
décision.
