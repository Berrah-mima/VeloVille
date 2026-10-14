#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v pg_dump >/dev/null 2>&1; then
  echo "Erreur : pg_dump est introuvable. Installez le client PostgreSQL." >&2
  exit 1
fi
if ! command -v python >/dev/null 2>&1; then
  echo "Erreur : Python est requis pour lire DATABASE_URL." >&2
  exit 1
fi

mapfile -t PG_SETTINGS < <(python "$ROOT/scripts/postgres_settings.py")
if [[ "${#PG_SETTINGS[@]}" -ne 5 || -z "${PG_SETTINGS[2]}" || -z "${PG_SETTINGS[3]}" ]]; then
  echo "Erreur : DATABASE_URL doit préciser la base et l'utilisateur PostgreSQL." >&2
  exit 1
fi
export PGHOST="${PG_SETTINGS[0]}"
export PGPORT="${PG_SETTINGS[1]}"
export PGDATABASE="${PG_SETTINGS[2]}"
export PGUSER="${PG_SETTINGS[3]}"
export PGPASSWORD="${PG_SETTINGS[4]}"
unset PG_SETTINGS

DOSSIER="${BACKUP_DIR:-$ROOT/sauvegardes}"
HORODATAGE="$(date '+%Y%m%d_%H%M%S')"
FICHIER="$DOSSIER/veloville_$HORODATAGE.dump"
mkdir -p "$DOSSIER"

if ! pg_dump --format=custom --file="$FICHIER"; then
  rm -f "$FICHIER"
  echo "Erreur : la sauvegarde PostgreSQL a échoué." >&2
  exit 1
fi
echo "Sauvegarde créée : $FICHIER"
