#!/usr/bin/env bash
# SHIELD one-command demo reset (Sprint 6 T8).
#
# Tears the stack down INCLUDING volumes (a clean slate), rebuilds, waits for the
# full-matrix /ready probe (T3) to go all-green, reseeds the coherent Atlas demo
# story (4 services + a synthesized Risk Register, all released + downloadable),
# and prints the URLs + logins.
#
#   bash scripts/demo-reset.sh
#
# WARNING: `docker compose down -v` DELETES all demo data (Postgres, MinIO,
# Redis). That is the point of a reset — do not run against data you want to
# keep. Live AI is optional: put ANTHROPIC_API_KEY in .env first.
set -euo pipefail

# Docker CLI is not on the Git Bash PATH by default on Windows dev machines.
export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

step() { printf '\n>> %s\n' "$1"; }

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon not running. Start Docker, then re-run." >&2
  exit 1
fi

echo "============================================================"
echo "  SHIELD by Kentro - resetting the demo stack (down -v)"
echo "============================================================"

# 1) Full teardown INCLUDING volumes (clean slate).
step "Tearing down (docker compose down -v)..."
docker compose down -v

# 2) Rebuild + start the full stack.
step "Building + starting containers (docker compose up -d --build)..."
docker compose up -d --build

# 3) Wait for the FULL-MATRIX readiness probe to go all-green (T3): every
#    required dependency (db, redis, minio, keycloak, llm) must report ok.
step "Waiting for /ready (full dependency matrix) to be all-green..."
ready=false
offenders=""
for _ in $(seq 1 80); do
  body="$(curl -fsS --max-time 3 http://localhost:8000/ready 2>/dev/null || true)"
  if [ -n "$body" ]; then
    case "$body" in
      *'"ready":true'*) ready=true; break ;;
    esac
    # Best-effort offender extraction for the failure message.
    offenders="$(printf '%s' "$body" | sed -n 's/.*"offenders":\[\([^]]*\)\].*/\1/p')"
  fi
  sleep 3
done
if [ "$ready" != true ]; then
  echo "Stack not ready in time. Offenders: ${offenders}" >&2
  echo "Inspect: docker compose logs api" >&2
  exit 1
fi
echo "All dependencies ready."

# 4) Seed the coherent Atlas demo (idempotent, but the DB is fresh here).
step "Seeding the Atlas demo story..."
docker compose exec -T api python scripts/seed_demo.py

# 5) Give the web app a moment (first build is slow; non-fatal if not ready yet).
step "Waiting for the web app..."
for _ in $(seq 1 40); do
  if curl -fsS --max-time 3 http://localhost:3000 >/dev/null 2>&1; then break; fi
  sleep 3
done

# 6) Print the banner.
cat <<'EOF'

============================================================
  SHIELD by Kentro - demo reset complete
============================================================
  Web app:     http://localhost:3000
  API + docs:  http://localhost:8000/docs
  Readiness:   http://localhost:8000/ready
  MailHog:     http://localhost:8025

  ADMIN  login: admin@kentro.example   /  DemoPass!2026
  CLIENT login: client@atlas.example   /  DemoPass!2026
============================================================
  Demo story: 4 services + Risk Register, released + downloadable
  See it on:  /home and /documents (client) - reports download
  Live AI (optional): put ANTHROPIC_API_KEY in .env, then re-run.

EOF
