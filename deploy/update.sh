#!/bin/sh
# Pull the latest code and restart only what changed. Run on the server:  sh update.sh
set -eu
cd "$(dirname "$0")"

git -C .. pull --ff-only
docker compose up -d --build
# Caddy doesn't notice an edited Caddyfile by itself; reload it (no downtime).
docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile >/dev/null 2>&1 || true
docker image prune -f >/dev/null
docker compose ps
