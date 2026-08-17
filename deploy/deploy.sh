#!/usr/bin/env bash
# Deploy EpiGuard AI to VPS at http://4.168.192.169/
# Run on the server as root or a user in the docker group:
#   curl -fsSL ... | bash
# Or copy repo to /opt/epiguard-ai and run:
#   sudo bash deploy/deploy.sh

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/epiguard-ai}"
REPO_URL="${REPO_URL:-}"

echo "=== EpiGuard AI deployment ==="

if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
fi

if ! docker compose version &>/dev/null; then
  echo "Docker Compose plugin required."
  exit 1
fi

mkdir -p "$APP_DIR"
cd "$APP_DIR"

if [ -n "$REPO_URL" ] && [ ! -d .git ]; then
  git clone "$REPO_URL" .
elif [ ! -f docker-compose.prod.yml ]; then
  echo "Place project files in $APP_DIR (docker-compose.prod.yml missing)."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env 2>/dev/null || true
  echo "Created .env — review settings if needed."
fi

echo "Building and starting services..."
docker compose -f docker-compose.prod.yml up -d --build

echo "Waiting for health check..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "API healthy on port 8000"
    break
  fi
  sleep 2
done

if curl -sf http://localhost/health >/dev/null 2>&1; then
  echo "Nginx proxy healthy on port 80"
else
  echo "Warning: port 80 health check failed — verify firewall allows HTTP"
fi

echo ""
echo "=== Deploy complete ==="
echo "  Demo:    http://4.168.192.169/"
echo "  Swagger: http://4.168.192.169/docs"
echo "  Health:  http://4.168.192.169/health"
echo ""
docker compose -f docker-compose.prod.yml ps
