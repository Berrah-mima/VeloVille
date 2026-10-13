# Procédure de déploiement VéloVille

## Prérequis

- Python 3.12 ou supérieur.
- PostgreSQL 14 ou supérieur et `psql`, `pg_dump`, `pg_restore`.
- Bash pour le script de sauvegarde.

Les commandes suivantes sont lancées depuis la racine du projet.

## Installation et configuration

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Modifier `.env` et définir une URL PostgreSQL valide, un secret JWT aléatoire
d'au moins 32 caractères et les paramètres front. Ne jamais partager ni
commiter ce fichier.

Créer le rôle et la base avec un compte PostgreSQL administrateur. Les
identifiants ci-dessous correspondent à l'environnement local d'entraînement ;
remplacez le mot de passe et mettez à jour `DATABASE_URL` hors entraînement :

```sql
CREATE ROLE veloville LOGIN PASSWORD 'veloville';
CREATE DATABASE veloville OWNER veloville;
```

Puis, dans PowerShell :

```powershell
psql -U veloville -d veloville -f sql/schema.sql
psql -U veloville -d veloville -f sql/comptes.sql
python scripts/importer.py
```

`sql/comptes.sql` initialise les deux comptes de démonstration et peut être
relancé sans les dupliquer. `scripts/init_db.py` fournit également une
initialisation idempotente par Python.
Pour produire le journal d'audit hors base, lancer
`python scripts/importer.py --audit-seul`.

## Démarrer et vérifier

Dans deux terminaux activant chacun `.venv` :

```powershell
uvicorn api.main:app --host 127.0.0.1 --port 8000
streamlit run front/app.py
```

Le contrat utilise le port 8000 et `.env.example` configure la même adresse.
Si le port est occupé localement, démarrer l'API avec `--port 8001` et définir
`API_URL=http://127.0.0.1:8001` dans `.env`. Vérifier l'URL correspondant
au port choisi, par exemple `http://127.0.0.1:8000/sante` : réponse
`{"statut":"ok"}`. Le front est servi par Streamlit, habituellement sur
`http://localhost:8501`. Les comptes de recette sont `exploitant01` et
`direction01`, avec le mot de passe de formation fourni dans le sujet.
Ne pas versionner `.env` : il contient les paramètres locaux et secrets.

Exécuter les tests et la couverture :

```powershell
python -m pytest --cov=api/services --cov-report=term-missing
```

Pour une campagne automatisée isolée, les tests utilisent SQLite en mémoire
et créent/suppriment leurs données à chaque test. La base PostgreSQL de
recette reste nécessaire pour rejouer l'import et les vérifications
manuelles de REC-01, REC-02, REC-07 et REC-10.

## Sauvegarder et restaurer

Dans un environnement Bash avec `DATABASE_URL` défini ou un `.env` présent :

```bash
bash scripts/sauvegarde.sh
pg_restore --list sauvegardes/veloville_AAAAMMJJ_HHMMSS.dump
```

Pour restaurer le format custom dans une base déjà créée :

```bash
mapfile -t PG_SETTINGS < <(python scripts/postgres_settings.py)
export PGHOST="${PG_SETTINGS[0]}"
export PGPORT="${PG_SETTINGS[1]}"
export PGDATABASE="${PG_SETTINGS[2]}"
export PGUSER="${PG_SETTINGS[3]}"
export PGPASSWORD="${PG_SETTINGS[4]}"
unset PG_SETTINGS
pg_restore --clean --if-exists --no-owner \
  --dbname="$PGDATABASE" sauvegardes/veloville_AAAAMMJJ_HHMMSS.dump
unset PGHOST PGPORT PGDATABASE PGUSER PGPASSWORD
```

`pg_restore` utilise les variables libpq plutôt que `DATABASE_URL` : le
préfixe SQLAlchemy `postgresql+psycopg://` n'est pas un schéma accepté comme
chaîne de connexion par `pg_restore`. Le script Python charge `.env` et
décompose l'URL sans l'inscrire dans l'historique du shell.

Vérifier ensuite le schéma, les comptages et la réponse de `/sante`. Garder
les sauvegardes hors du dépôt et appliquer la politique de conservation de
l'organisation.
