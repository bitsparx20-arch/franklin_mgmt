#!/usr/bin/env bash
# Full install when you only have KVM/web console on the server (no local SSH).
# On the server as root:
#   curl -fsSL -o /tmp/franklin.tgz "URL_TO_YOUR_TARBALL"
#   bash /tmp/install-from-tarball.sh /tmp/franklin.tgz
#
# Or copy franklin-crm-deploy.tgz via SCP first, then:
#   bash deploy/install-from-tarball.sh /tmp/franklin-crm-deploy.tgz

set -euo pipefail
TARBALL="${1:-/tmp/franklin-crm-deploy.tgz}"
SRC="/tmp/franklin-crm-src"

if [[ ! -f "$TARBALL" ]]; then
  echo "Missing tarball: $TARBALL"
  exit 1
fi

rm -rf "$SRC" && mkdir -p "$SRC"
tar xzf "$TARBALL" -C "$SRC"
bash "$SRC/deploy/setup-server.sh"
bash "$SRC/deploy/install-app.sh"

if [[ -f "$SRC/backend/.env.production" ]]; then
  cp "$SRC/backend/.env.production" /opt/franklin-crm/backend/.env
  systemctl restart franklin-backend
fi

echo "Open http://$(hostname -I | awk '{print $1}')/"
