#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-/opt/vinoth-os}"
DB="$PROJECT_DIR/data/vinoth_os.db"
BACKUP_DIR="$PROJECT_DIR/backups"
mkdir -p "$BACKUP_DIR"
if [ ! -f "$DB" ]; then
  echo "Database not found: $DB"
  exit 1
fi
STAMP=$(date +%Y%m%d-%H%M%S)
python3 - "$DB" "$BACKUP_DIR/vinoth_os-$STAMP.db" <<'PY'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
with sqlite3.connect(src) as source, sqlite3.connect(dst) as target:
    source.backup(target)
print(dst)
PY
