#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root relative to this script, so it works from any CWD
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

COMPOSE_FILE=${COMPOSE_FILE:-"${REPO_ROOT}/docker-compose.ci.yml"}
WEB_URL=${WEB_URL:-http://localhost:8000}

echo "[ci] Using compose file: ${COMPOSE_FILE}"
echo "[ci] Bringing up services"
docker compose -f "$COMPOSE_FILE" up -d

wait_for_http() {
  local url="$1"; local timeout="${2:-120}"; local start=$(date +%s)
  echo "[ci] Waiting for ${url} to be ready (timeout ${timeout}s)"
  until curl -sS -o /dev/null "$url"; do
    sleep 2
    now=$(date +%s); if (( now - start > timeout )); then
      echo "[ci] Timeout waiting for ${url}" >&2
      docker compose -f "$COMPOSE_FILE" logs web || true
      exit 1
    fi
  done
}

# The web container runs migrations before starting the server in CI compose.
wait_for_http "${WEB_URL}" 180

echo "[ci] Running API smoke checks"

# Expect 200 OK for public endpoints
http_code=$(curl -sS -o /dev/null -w "%{http_code}" "${WEB_URL}/api/pois/")
echo "[ci] GET /api/pois/ -> ${http_code}"
test "$http_code" = "200"

http_code=$(curl -sS -o /dev/null -w "%{http_code}" "${WEB_URL}/api/import-batches/statistics/")
echo "[ci] GET /api/import-batches/statistics/ -> ${http_code}"
test "$http_code" = "200"

echo "[ci] CI smoke passed"

echo "[ci] Tearing down compose stack"
docker compose -f "$COMPOSE_FILE" down -v
