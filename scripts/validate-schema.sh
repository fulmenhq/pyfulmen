#!/usr/bin/env bash

# Lightweight wrapper to validate payloads against Crucible schemas.
# Defaults to goneat when available; falls back to the PyFulmen CLI otherwise.
# Usage: scripts/validate-schema.sh <schema-id> --file <payload.json>

set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <schema-id> --file <path>" >&2
  echo "       $0 <schema-id> --data '<json>'" >&2
  exit 64
fi

SCHEMA_ID=$1
shift

HELPER=${PYFULMEN_SCHEMA_HELPER:-goneat}

if [ "$HELPER" = "goneat" ] && command -v goneat >/dev/null 2>&1; then
  SCHEMA_PATH=$(python - <<'PY'
import sys
from pyfulmen.schema import catalog

schema_id = sys.argv[1]
info = catalog.get_schema(schema_id)
print(info.path)
PY
"$SCHEMA_ID")

  if [ "$1" = "--file" ]; then
    goneat schema validate-data --schema "$SCHEMA_PATH" --file "$2"
  elif [ "$1" = "--data" ]; then
    tmp=$(mktemp)
    trap 'rm -f "$tmp"' EXIT
    printf '%s' "$2" >"$tmp"
    goneat schema validate-data --schema "$SCHEMA_PATH" --file "$tmp"
  else
    echo "Expected --file or --data" >&2
    exit 64
  fi
else
  python -m pyfulmen.schema.cli validate "$SCHEMA_ID" "$@" --no-goneat
fi
