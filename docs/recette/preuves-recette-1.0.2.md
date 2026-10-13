# Preuves de recette — VéloVille 1.0.2

Campagne locale du 13/10/2026. Les commandes ont utilisé la configuration
PostgreSQL locale de `.env`. Aucun identifiant ni jeton n'est conservé ici.

## REC-01 et REC-02 — Import et journal

```powershell
python scripts/importer.py
python scripts/importer.py
```

Comptages PostgreSQL avant et après le second passage : `station=120`,
`trajet=2002`, `incident=177` (inchangés).

| Source | Lignes | Importées | Rejetées | Doublons source |
|---|---:|---:|---:|---:|
| `stations.csv` | 120 | 120 | 0 | 0 |
| `trajets.csv` | 2 030 | 2 002 | 16 | 12 |
| `incidents.csv` | 180 | 177 | 3 | 0 |

Le journal `docs/journal_import.csv` porte les six colonnes demandées. La
requête des trajets dont la station d'arrivée renseignée n'existe pas renvoie
`0`.

## REC-03 à REC-08 — API et PostgreSQL

Requêtes exécutées avec FastAPI `TestClient` connecté à la base PostgreSQL :

- `/sante` : `200`; `/stations` sans jeton : `401`.
- Connexion des deux rôles : `200`; identifiants invalides et utilisateur
  absent : `401` avec le même corps.
- Direction sur une transition d'incident : `403`; exploitant : transition
  autorisée `200`, répétition invalide `422`. L'incident de test a été remis
  à son état et à ses champs initiaux.
- Pagination stations : page 1 `50/120`, page 3 `20`; Lille `46`;
  `page=0` et `taille_page=101` : `422`.
- Station `S001` : `200`, nom `Lille - Gare`; station `S999` : `404`.

## REC-09 — Indicateur comparé au SQL

Sur la période 2026-08-24 à 2026-08-30, la réponse
`GET /indicateurs/activite-par-jour` a été comparée à :

```sql
SELECT depart_horodatage::date AS jour, count(*) AS nb_trajets
FROM trajet
WHERE depart_horodatage::date BETWEEN '2026-08-24' AND '2026-08-30'
GROUP BY jour
ORDER BY jour;
```

Les lignes et comptages étaient identiques ; la somme était `2002`, égale au
`total` de `GET /trajets` sur les mêmes dates.

## REC-10 — Front et panne API

Interface Streamlit ouverte dans le navigateur sur la base chargée :

- Connexion direction réussie.
- Page Stations 7 : message « Aucun résultat pour ces critères. »
- API arrêtée : Stations et Indicateurs affichent
  « L'API est injoignable. Vérifiez qu'elle est démarrée. », sans traceback.
- API redémarrée : le tableau Stations se recharge avec les données.

## Tests automatisés

```powershell
python -m pytest --cov=api/services --cov-report=term-missing
```

Résultat : `51 passed`, couverture des services `92 %`.
