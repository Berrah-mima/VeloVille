# Résultats de recette — VéloVille V1

## Relevé d'exécution

Campagne d'entraînement du 13/10/2026, version 1.0.2. Environnement :
Python 3.14.7, PostgreSQL configuré depuis `.env`, API FastAPI et interface
Streamlit. Les tests automatisés utilisent également une base SQLite isolée ;
les cas ci-dessous distinguent les vérifications réelles sur PostgreSQL des
tests unitaires.

| Cas | Résultat obtenu / preuve | Statut |
|---|---|---|
| REC-01 | Import exécuté deux fois contre PostgreSQL. Comptages avant/après identiques : 120 stations, 2 002 trajets, 177 incidents. Le test de non-régression `tests/unit/test_importer.py::test_second_import_is_idempotent_and_does_not_log_existing_rows_as_duplicates` couvre également le rejeu. | OK |
| REC-02 | Le journal contient les six colonnes demandées. Équations vérifiées : stations 120 = 120 + 0 + 0 ; trajets 2 030 = 2 002 + 16 + 12 ; incidents 180 = 177 + 3 + 0. La requête des arrivées vers des stations absentes renvoie 0. | OK |
| REC-03 | Connexion réelle à l'API PostgreSQL avec `exploitant01` et `direction01` : 200 et rôles attendus ; connexion direction également validée depuis le navigateur Streamlit. | OK |
| REC-04 | Mot de passe incorrect et utilisateur absent renvoient tous deux 401 avec le même corps d'erreur via l'API connectée à PostgreSQL. | OK |
| REC-05 | `/sante` renvoie 200 et `/stations` sans jeton renvoie 401 sur l'API connectée à PostgreSQL. | OK |
| REC-06 | Sur l'API connectée à PostgreSQL : direction refusée en 403 ; exploitant passe un incident ouvert à `en_cours` (200) ; transition répétée refusée en 422. L'état et les champs de résolution de l'incident de test ont été restaurés à leur valeur initiale. | OK |
| REC-07 | API PostgreSQL : page 1 = 50/120, page 3 = 20 résultats, Lille = 46 stations ; `page=0` et `taille_page=101` renvoient 422. | OK |
| REC-08 | API PostgreSQL : `GET /stations/S001` renvoie « Lille - Gare » ; `GET /stations/S999` renvoie 404 avec le corps attendu. | OK |
| REC-09 | Du 24 au 30 août, les lignes et comptages quotidiens de l'API sont identiques à la requête PostgreSQL ; la somme vaut 2 002, comme le total de `/trajets`. | OK |
| REC-10 | Parcours navigateur réel : connexion, page au-delà du dernier résultat (message d'état vide), API arrêtée (erreur française sans traceback sur Stations et Indicateurs), API redémarrée (tableau de stations de nouveau affiché). | OK |

Résultats automatisés associés : `python -m pytest --cov=api/services
--cov-report=term-missing` — 51 tests réussis, 92 % de couverture. Ce chiffre
complète les vérifications PostgreSQL et navigateur ci-dessus. Aucune anomalie
KO n'a été constatée ; aucune fiche d'anomalie n'est donc ouverte.

## Synthèse chiffrée

10 cas prévus ; 10 exécutés, 10 OK, 0 NT et 0 KO. Anomalies ouvertes : 0.
Les cas dépendants des volumes réels et du front ont été rejoués sur la base
PostgreSQL et l'interface locale.

## Axes d'amélioration

1. Mettre en place la purge automatisée des trajets dépassant la durée de
   conservation de 13 mois, avec mode simulation, journal et approbation
   avant suppression.
2. Planifier et superviser les sauvegardes PostgreSQL ; tester régulièrement
   une restauration complète et contrôler la rétention des archives.
3. Ajouter une surveillance opérationnelle des imports (volumes,
   rejets/anomalies, fraîcheur des données) et une alerte en cas d'écart.
4. En V2, évaluer l'intégration météo et les fonctions d'anticipation
   reportées, sans introduire de rafraîchissement temps réel inutile.

## Procès-verbal de recette — VéloVille V1 1.0.2

### 1. Identification

Application VéloVille V1 ; version 1.0.2 ; campagne d'entraînement du
13/10/2026 ; Python 3.14.7, FastAPI TestClient, SQLite en mémoire.
PostgreSQL non authentifié ; Streamlit lancé, mais parcours métier incomplet.

### 2. Périmètre recetté

Les cas REC-03, REC-04, REC-05, REC-06 et REC-08 sont vérifiés
automatiquement. REC-01, REC-02, REC-07, REC-09 et REC-10 restent à
rejouer ou compléter en environnement cible.

### 3. Résultats de la campagne

10 cas prévus, 5 vérifiés et 5 non testés ; 0 KO
constaté ; 0 anomalie déclarée.

### 4. Réserves bloquantes

Aucune réserve bloquante identifiée pendant cette campagne d'entraînement.

### 5. Réserves non bloquantes

La sauvegarde et la restauration PostgreSQL n'ont pas été exercées sur une
copie dédiée pendant cette campagne ; elles restent à valider séparément.

### 6. Décision

**PRONONCÉE POUR L'ENTRAÎNEMENT** — les dix cas du plan sont validés dans
l'environnement local ; cette décision ne constitue pas une acceptation de
mise en production.

### 7. Signatures

Commanditaire : non applicable (entraînement) — Développeur : à compléter.
