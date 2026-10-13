# Résultats de recette — VéloVille V1

## Relevé d'exécution

Campagne d'entraînement automatisée du 13/10/2026. Environnement : Python
3.14.7, tests d'API via FastAPI `TestClient`, base SQLite en mémoire créée
pour chaque test. Le service PostgreSQL local était joignable mais la
connexion n'a pas pu être authentifiée avec la configuration disponible ;
le parcours Streamlit a été lancé mais pas validé contre une base importée.
Les cas notés NT doivent être rejoués sur une base PostgreSQL configurée.

| Cas | Résultat obtenu / preuve | Statut |
|---|---|---|
| REC-01 | Non exécuté contre PostgreSQL : création de la base et second import requis. | NT |
| REC-02 | `python scripts/importer.py --audit-seul` génère `docs/journal_import.csv`; test `tests/unit/test_audit_donnees.py::test_journal_audit_sans_base_contient_les_six_colonnes` vérifie les six colonnes et l'équation lignes = importées + rejets + doublons. Les comptages PostgreSQL et la requête de références restent à exécuter. | NT |
| REC-03 | Login exploitant/direction et rôles testés avec `TestClient` : `tests/integration/test_api.py::test_connexion_reussie_et_refusee`. | OK |
| REC-04 | Mauvais mot de passe et identifiant inconnu renvoient 401 avec le même message : `tests/integration/test_api.py::test_connexion_reussie_et_refusee`. | OK |
| REC-05 | `/stations` sans jeton refusé en 401 ; `/sante` accessible : `test_ressource_protegee_sans_jeton_refusee`, `test_sante`. | OK |
| REC-06 | Direction refusée en 403 ; exploitant effectue la transition et la répétition renvoie 422 : `test_direction_ne_peut_pas_modifier_un_incident`, `test_exploitant_peut_modifier_et_transition_invalide_renvoie_422`. | OK |
| REC-07 | Pagination et bornes testées sur 3 stations de la fixture, mais pas les attendus de production (120 stations, 46 à Lille). | NT |
| REC-08 | Station présente/inconnue testées : `test_station_introuvable`. | OK |
| REC-09 | Cohérence indicateur/liste testée sur les dates de fixture : `test_indicateur_activite_coherent_avec_liste`. Le jeu complet 24–30 août reste à comparer à PostgreSQL. | NT |
| REC-10 | Page de connexion Streamlit chargée dans le navigateur. Absence de preuve du parcours vide, de l'arrêt/redémarrage de l'API et du retour aux données après connexion. | NT |

Résultats automatisés associés : `python -m pytest --cov=api/services
--cov-report=term-missing` — 46 tests réussis, 93 % de couverture. Ce chiffre
ne vaut pas preuve des tests manuels NT. Aucune anomalie KO n'a été constatée
dans les tests exécutés ; aucune fiche d'anomalie ni correction de recette
n'est donc déclarée.

## Synthèse chiffrée

10 cas prévus ; 10 examinés, dont 5 OK, 5 NT et 0 KO.
Anomalies ouvertes : 0 ; anomalies corrigées et rejouées : 0. La recette
demeure incomplète car les cas de données complètes et le front n'ont pas
été exécutés sur l'environnement cible.

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

## Procès-verbal de recette — VéloVille V1 1.0.0

### 1. Identification

Application VéloVille V1 ; version 1.0.0 ; campagne d'entraînement du
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

Campagne PostgreSQL complète, import idempotent, journal/volumes, données
réelles des indicateurs et parcours front à exécuter avant validation
opérationnelle.

### 5. Réserves non bloquantes

Rejouer les scénarios manuels sur PostgreSQL et conserver les preuves HTTP
ou captures d'écran associées.

### 6. Décision

**PRONONCÉE AVEC RÉSERVES** — les contrôles automatisés disponibles sont
verts, mais les cas dépendants de PostgreSQL, des exports complets et du
navigateur ne sont pas encore exécutés. Cette décision est un état
d'entraînement, pas une acceptation de mise en production.

### 7. Signatures

Commanditaire : non applicable (entraînement) — Développeur : à compléter.
