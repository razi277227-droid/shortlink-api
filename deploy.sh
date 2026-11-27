#!/usr/bin/env bash
set -eu
cd /opt/shortlink-api

sha="${1:-}"
if [[ ! "$sha" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Передай нормальны SHA коммита" >&2
  exit 2
fi

export SHORTLINK_IMAGE="ghcr.io/razi277227-droid/shortlink-api:$sha"

docker pull "$SHORTLINK_IMAGE"
docker compose -f compose.yaml -f compose.prod.yaml run --rm -T --no-deps --pull never api alembic upgrade head
docker compose -f compose.yaml -f compose.prod.yaml up -d --no-deps --no-build --pull never api

curl -fsS --retry 10 --retry-connrefused --retry-delay 1 --max-time 5 -o /dev/null http://127.0.0.1:8001/openapi.json
docker inspect -f '{{.Config.Image}}' shortlink-api-api-1