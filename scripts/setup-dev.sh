#!/usr/bin/env bash
# One-shot local dev bootstrap. Assumes Node 20+, Python 3.11+, Docker installed.
set -euo pipefail

echo "Installing JS workspace dependencies (apps/web, services/gateway, packages/*)..."
npm install

for service in speech-pipeline clinical-nlp vision-service orchestrator; do
  echo "Setting up services/${service} virtualenv..."
  python3 -m venv "services/${service}/.venv"
  "services/${service}/.venv/bin/pip" install -r "services/${service}/requirements-dev.txt"
done

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — fill in real values before running services."
fi

echo "Done. Run 'docker compose -f infra/docker/docker-compose.dev.yml up' to start Postgres/Redis/MinIO."
