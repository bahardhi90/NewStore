#!/bin/sh
# Pull the latest code and restart only what changed. Run on the server:  sh update.sh
set -eu
cd "$(dirname "$0")"

git -C .. pull --ff-only
docker compose up -d --build
docker image prune -f >/dev/null
docker compose ps
