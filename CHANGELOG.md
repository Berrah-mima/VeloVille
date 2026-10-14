# Journal des versions

Format recommandé : une section par version, les changements regroupés en
« Ajouté », « Modifié », « Corrigé ».

## [1.0.3] - 2026-10-13

### Modifié
- Les indicateurs disposent d'un bouton Actualiser et affichent un état vide
  explicite pour chaque tableau.
- Les messages API 404 et 422 sont adaptés en français pour les erreurs
  usuelles de stations, incidents, dates et transitions.
- La procédure de restauration utilise les variables libpq extraites de
  `DATABASE_URL`, et `.gitattributes` normalise les fins de ligne.
- README, résultats de recette et support de soutenance sont harmonisés sur
  les 57 tests et les dix cas de recette validés.

### Corrigé
- La route `GET /incidents` délègue au service sous un alias explicite, évitant
  l'appel récursif au routeur.
- Ajout d'un test d'intégration dédié à la liste paginée des incidents.

## [1.0.2] - 2026-10-13

### Modifié
- Les routeurs délèguent les requêtes de données et les traitements métier à
  `api/services/`.
- La page des indicateurs utilise trois appels API et recharge ses données à
  chaque exécution.
- Les paramètres PostgreSQL par défaut correspondent à la base locale de
  recette `veloville`.
- Le plan de recette est identique au document fourni par le formateur.

### Corrigé
- Un second import n'enregistre plus les lignes déjà en base comme des
  doublons source ; les compteurs et le journal restent idempotents.
- Les tests utilisent un mot de passe réservé aux tests, distinct du secret de
  démonstration fourni.
- Le script de sauvegarde est au format LF et sa syntaxe Bash est vérifiée.
- L'audit décrit également les normalisations des pseudonymes, identifiants de
  vélos et types d'incident.

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

## [1.0.0] - 2026-10-13

### Ajouté
- Schéma PostgreSQL, import idempotent et fiabilisation avec journal CSV.
- API FastAPI protégée par JWT, pagination, transitions d'incidents et indicateurs.
- Interface Streamlit tabulaire pour la connexion, les stations, les incidents et les indicateurs.
- Tests unitaires et d'intégration, avec couverture des services.
- Documentation du schéma, des accès, du déploiement et des résultats d'entraînement.
- Script de sauvegarde PostgreSQL horodaté.
- Scripts d'initialisation Python et SQL ainsi qu'un journal d'audit régénérable.

### Modifié
- Dépendances Python épinglées dans `requirements.txt`.
- Port API par défaut aligné sur le contrat (8000) ; port local 8001 configurable en cas de conflit.

### Corrigé
- Les incohérences des exports sont normalisées ou rejetées selon les règles RG1 à RG8.
