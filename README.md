# VéloVille — Plateforme de valorisation des données

API REST FastAPI, base PostgreSQL et interface tabulaire Streamlit pour
consulter stations, trajets, incidents et indicateurs d'exploitation.

## Prérequis et installation

Python 3.12+, PostgreSQL 14+ et Git. Depuis la racine :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Configurer `DATABASE_URL`, `JWT_SECRET` (secret aléatoire d'au moins
32 caractères), `JWT_EXPIRATION_MINUTES`, `API_URL` et
`API_TIMEOUT_SECONDES` dans `.env`. Ce fichier est exclu du dépôt.

Créer le rôle et la base PostgreSQL, puis initialiser et importer :

```sql
CREATE ROLE veloville LOGIN PASSWORD '<mot-de-passe-local>';
CREATE DATABASE veloville OWNER veloville;
```

```powershell
psql -U veloville -d veloville -f sql/schema.sql
psql -U veloville -d veloville -f sql/comptes.sql
python scripts/importer.py
```

`scripts/init_db.py` offre aussi une initialisation Python alternative.
Le journal `docs/journal_import.csv` est livré dans le dépôt et peut être
régénéré sans accès à PostgreSQL avec
`python scripts/importer.py --audit-seul`. Un import réel le régénère aussi.
Les fonctions de fiabilisation sont indépendantes de la base ; l'import
applique les stations avant les trajets et les incidents et est rejouable.

## Lancer l'application

```powershell
uvicorn api.main:app --host 127.0.0.1 --port 8000
streamlit run front/app.py
```

Le front cible par défaut `http://127.0.0.1:8000`. Si ce port est occupé sur
ton poste, lance l'API avec `--port 8001` et définis `API_URL` à
`http://127.0.0.1:8001` dans `.env`. L'API répond sur `/sante` avec
`{"statut":"ok"}`. Le front est disponible par défaut à
`http://localhost:8501`. Les identifiants de recette fournis sont
`exploitant01` et `direction01`; le mot de passe partagé est celui indiqué
dans le sujet.

## Tests et couverture

```powershell
python -m pytest --cov=api/services --cov-report=term-missing
```

Résultat mesuré dans cet environnement : **46 tests réussis** et **93 % de
couverture** sur `api/services`. Les tests d'intégration utilisent
`TestClient` et une base SQLite éphémère isolée ; ils ne remplacent pas le
rejeu de recette sur PostgreSQL et les CSV complets.

## Audit des données sources

L'audit détaillé, les règles RG1 à RG8 et les volumes attendus figurent dans
[`docs/schema-donnees.md`](docs/schema-donnees.md). Constats principaux :

- 120 stations : aucune anomalie bloquante repérée.
- 2 030 trajets : 12 doublons excédentaires, 7 références d'arrivée
  inconnues rejetées, durées non positives (9 lignes uniques rejetées; une
  ligne de durée invalide est également le second exemplaire d'un doublon),
  5 horodatages au format hétérogène (4 normalisés et importés, 1 sur une
  ligne rejetée pour référence d'arrivée invalide). Volume attendu : 2 002 trajets.
- 180 incidents : 3 dates de résolution antérieures au signalement rejetées,
  125 statuts de forme hétérogène (124 normalisés sur les lignes importées,
  1 sur une ligne rejetée) et 25 absences de technicien journalisées comme
  avertissements non bloquants. Volume attendu : 177 incidents.

Le total de chaque fichier se répartit entre lignes importées, rejets et
doublons écartés ; les avertissements annotent des lignes importées et ne
s'ajoutent pas comme catégorie exclusive.

## Sécurité, rôles et données personnelles

`POST /auth/login` vérifie les hachages bcrypt et délivre un JWT HS256 expirant.
Toutes les routes, sauf `/sante` et `/auth/login`, exigent un Bearer valide.
La lecture est permise aux rôles `exploitant` et `direction`; seul
`exploitant` peut modifier le statut d'un incident. Voir
[`docs/matrice-roles-droits.md`](docs/matrice-roles-droits.md).
`usager_ref` reste pseudonymisé et n'est pas affiché dans le front.

## Choix écoresponsables

- Les listes sont paginées côté serveur avec une taille bornée, pour éviter
  le chargement de tables entières côté client.
- Aucun rafraîchissement automatique ni flux temps réel : les données sont
  chargées à la demande.
- La liste des communes est mise en cache dans Streamlit pendant une heure.
- Les indicateurs utilisent des agrégations SQL.
- Les dépendances sont limitées à l'API, à l'interface et aux tests.

## Documentation et maintenance

- [`docs/schema-donnees.md`](docs/schema-donnees.md) : MLD, contraintes,
  règles de gestion et audit des exports.
- [`docs/procedure-deploiement.md`](docs/procedure-deploiement.md) :
  déploiement et restauration.
- [`docs/recette/plan-de-recette.md`](docs/recette/plan-de-recette.md) et
  [`docs/recette/resultats-recette.md`](docs/recette/resultats-recette.md) :
  plan et relevé honnête, avec les cas d'intégration PostgreSQL/front encore
  indiqués NT et à exécuter sur l'environnement cible.
- `scripts/sauvegarde.sh` produit une sauvegarde `pg_dump` horodatée au
  format custom ; les sauvegardes ne sont pas versionnées.

## Limites connues

La V1 n'inclut ni données météo, ni prévision de rééquilibrage, ni état
temps réel. La purge de conservation des trajets sur 13 mois et la
planification automatique des sauvegardes sont à industrialiser. La
campagne manuelle de recette sur PostgreSQL authentifié et le parcours
complet du front restent à effectuer avant une mise en service. Si le port
8000 est pris par un autre service local, définir `API_URL` dans `.env` sur
le port alternatif utilisé par Uvicorn (8001 sur le poste de développement).

Version : 1.0.0 — voir [`CHANGELOG.md`](CHANGELOG.md).
