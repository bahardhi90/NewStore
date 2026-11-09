#!/bin/sh
set -e

# Wait for the database (max ~60s)
python - <<'PY'
import os, sys, time
import django
django.setup()
from django.db import connection
for i in range(30):
    try:
        connection.ensure_connection()
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"Waiting for database... ({exc.__class__.__name__})", flush=True)
        time.sleep(2)
sys.exit("Database is not reachable")
PY

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput
fi
if [ "${COLLECT_STATIC:-0}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

exec "$@"
