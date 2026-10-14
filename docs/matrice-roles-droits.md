# Matrice des rôles et des droits

`200` signifie que la route est autorisée lorsque l'objet existe et que les
paramètres sont valides. Les routes protégées renvoient `401` à un anonyme
ou lorsque le jeton est absent, invalide ou expiré. Un refus lié au rôle
renvoie `403`.

| Méthode et route | Anonyme | Exploitant | Direction |
|---|---:|---:|---:|
| GET `/sante` | 200 | 200 | 200 |
| POST `/auth/login` | 200 / 401 | 200 / 401 | 200 / 401 |
| GET `/stations` | 401 | 200 | 200 |
| GET `/stations/{station_id}` | 401 | 200 / 404 | 200 / 404 |
| GET `/trajets` | 401 | 200 | 200 |
| GET `/incidents` | 401 | 200 | 200 |
| PUT `/incidents/{incident_id}/statut` | 401 | 200 / 404 / 422 | 403 |
| GET `/indicateurs/activite-par-jour` | 401 | 200 | 200 |
| GET `/indicateurs/stations-actives` | 401 | 200 | 200 |
| GET `/indicateurs/incidents-par-statut` | 401 | 200 | 200 |

Les paramètres hors bornes ou invalides renvoient `422`. La modification
d'incident est limitée à `exploitant`, avec le message contractuel
`Acces reserve au role exploitant`.

## Données sensibles

- **Mots de passe** : seuls les hachages bcrypt sont conservés en base ; les
  mots de passe en clair ne sont ni stockés ni journalisés.
- **`usager_ref`** : pseudonyme indirect conservé uniquement pour les
  abonnés, jamais affiché par le front de restitution. Aucune donnée
  directement identifiante n'est importée.
- **Jeton JWT** : transmis dans l'en-tête Bearer, gardé dans la session
  Streamlit, jamais ajouté aux URL ni affiché à l'écran. Sa durée de vie est
  configurable et sa signature dépend de `JWT_SECRET`.
- **Secrets de déploiement** : `DATABASE_URL` et `JWT_SECRET` résident dans
  `.env`, ignoré par Git. `.env.example` ne contient que des valeurs
  indicatives à remplacer.
