#!/usr/bin/env bash
# One-time KVM/VPS bootstrap for Franklin CRM (Ubuntu/Debian).
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo "==> Updating package index..."
apt-get update -qq

echo "==> Installing base packages..."
apt-get install -y -qq curl gnupg ca-certificates nginx python3 python3-venv python3-pip git rsync

# Node.js 20 LTS (nodesource)
if ! command -v node >/dev/null 2>&1 || [[ "$(node -v | cut -d. -f1 | tr -d v)" -lt 18 ]]; then
  echo "==> Installing Node.js 20..."
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y -qq nodejs
fi

# MongoDB 7 (official repo)
if ! command -v mongod >/dev/null 2>&1; then
  echo "==> Installing MongoDB..."
  UBUNTU_CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME:-jammy}")"
  curl -fsSL "https://www.mongodb.org/static/pgp/server-7.0.asc" \
    | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
  echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu ${UBUNTU_CODENAME}/mongodb-org/7.0 multiverse" \
    > /etc/apt/sources.list.d/mongodb-org-7.0.list
  apt-get update -qq
  apt-get install -y -qq mongodb-org
fi

systemctl enable --now mongod
systemctl enable nginx

mkdir -p /opt/franklin-crm
echo "==> Server bootstrap complete."
