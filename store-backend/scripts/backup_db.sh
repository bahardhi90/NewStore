#!/bin/sh
# PostgreSQL backup with retention. Run daily from cron on the server, e.g.:
#   0 3 * * * cd /srv/store-backend && ./scripts/backup_db.sh >> /var/log/store-backup.log 2>&1
# Restore:
#   gunzip -c backups/store-YYYYmmdd-HHMM.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" "$POSTGRES_DB"
set -eu

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
STAMP="$(date +%Y%m%d-%H%M)"

mkdir -p "$BACKUP_DIR"
docker compose -f "$COMPOSE_FILE" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" --no-owner "$POSTGRES_DB"' \
  | gzip > "$BACKUP_DIR/store-$STAMP.sql.gz"

find "$BACKUP_DIR" -name 'store-*.sql.gz' -mtime +"$RETENTION_DAYS" -delete
echo "Backup written: $BACKUP_DIR/store-$STAMP.sql.gz"
# Copy offsite (recommended), e.g.: rclone copy "$BACKUP_DIR" remote:store-backups
