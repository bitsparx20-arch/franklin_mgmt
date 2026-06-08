#!/usr/bin/env bash
# Install or update Franklin CRM app under /opt/franklin-crm
set -euo pipefail

APP_ROOT="/opt/franklin-crm"
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DEPLOY_DIR")"

cd "$PROJECT_ROOT"

echo "==> Syncing application to ${APP_ROOT}..."
mkdir -p "$APP_ROOT"
rsync -a --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'frontend/node_modules' \
  --exclude 'backend/.venv' \
  --exclude 'backend/__pycache__' \
  --exclude 'frontend/build' \
  --exclude '.env' \
  "$PROJECT_ROOT/" "$APP_ROOT/"

# Preserve production .env if already on server; otherwise copy from example
if [[ ! -f "${APP_ROOT}/backend/.env" ]]; then
  if [[ -f "${APP_ROOT}/backend/.env.production" ]]; then
    cp "${APP_ROOT}/backend/.env.production" "${APP_ROOT}/backend/.env"
  else
    cp "${APP_ROOT}/backend/.env.example" "${APP_ROOT}/backend/.env"
    echo "WARNING: Created ${APP_ROOT}/backend/.env from example — edit secrets before going live."
  fi
fi

echo "==> Python backend..."
cd "${APP_ROOT}/backend"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

echo "==> Frontend build..."
cd "${APP_ROOT}/frontend"
npm install --legacy-peer-deps --silent
npm install ajv@8 --legacy-peer-deps --silent
# Same-origin nginx proxy — no REACT_APP_BACKEND_URL needed
NODE_ENV=production npm run build

echo "==> systemd + nginx..."
cp "${APP_ROOT}/deploy/franklin-backend.service" /etc/systemd/system/franklin-backend.service
cp "${APP_ROOT}/deploy/nginx-franklin.conf" /etc/nginx/sites-available/franklin-crm
ln -sf /etc/nginx/sites-available/franklin-crm /etc/nginx/sites-enabled/franklin-crm
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable franklin-backend
systemctl restart franklin-backend
nginx -t
systemctl reload nginx

echo ""
echo "==> Deployment complete."
echo "    App URL:  http://$(hostname -I | awk '{print $1}')/"
echo "    API docs: http://$(hostname -I | awk '{print $1}')/docs"
systemctl --no-pager status franklin-backend | head -5
