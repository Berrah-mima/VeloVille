# Journal des versions

Format recommandé : une section par version, les changements regroupés en
« Ajouté », « Modifié », « Corrigé ».

## [0.1.0] - 2026-10-07

### Ajouté
- Initialisation du projet à partir du squelette fourni.

## [1.0.0] - 2026-10-13

### Ajouté
- Schéma PostgreSQL, import idempotent et fiabilisation avec journal CSV.
- API FastAPI protégée par JWT, pagination, transitions d'incidents et indicateurs.
- Interface Streamlit tabulaire pour la connexion, les stations, les incidents et les indicateurs.
- Tests unitaires et d'intégration, 46 tests réussis et couverture de 93 % des services.
- Documentation du schéma, des accès, du déploiement et des résultats d'entraînement.
- Script de sauvegarde PostgreSQL horodaté.
- Script Python idempotent `scripts/init_db.py` pour créer les tables ORM et les comptes.
- Script `sql/comptes.sql` idempotent conforme au contrat de l'épreuve.
- Journal d'audit CSV régénérable sans base PostgreSQL.

### Modifié
- Dépendances Python épinglées dans `requirements.txt`.
- Port API par défaut aligné sur le contrat (8000) ; port local 8001 configurable en cas de conflit.

### Corrigé
- Les incohérences des exports sont normalisées ou rejetées selon les règles RG1 à RG8.

## [1.0.1] - 2026-10-13

### Ajouté
- Mode `--audit-seul` pour générer le journal et vérifier les volumes CSV sans connexion PostgreSQL.
- Couverture des branches métier incident, de l'audit CSV, du script d'initialisation et du parsing de connexion sauvegarde.

### Modifié
- Transitions de statut déplacées dans `api/services/incidents.py`.
- Ports par défaut alignés sur le contrat (API 8000), avec surcharge documentée en cas de conflit local.
- Résultats de recette clarifiés pour distinguer les cas automatisés des contrôles PostgreSQL/front non exécutés.

### Corrigé
- Script de sauvegarde Bash validé par `bash -n` et lecture des identifiants libpq à partir de `DATABASE_URL`.
- Restauration du livrable contractuel `sql/comptes.sql` ; `.env` et `.venv` vérifiés comme exclus de Git.
