#!/usr/bin/env bash
# Run ON THE SERVER (KVM console or existing SSH session) to allow passwordless deploys.
# Paste your public key as the first argument, or pipe it:
#   echo "ssh-ed25519 AAAA... deploy@lms" | bash authorize-ssh-key.sh

set -euo pipefail
PUBKEY="${1:-}"
if [[ -z "$PUBKEY" ]]; then
  read -r PUBKEY
fi
if [[ -z "$PUBKEY" ]]; then
  echo "Usage: authorize-ssh-key.sh 'ssh-ed25519 AAAA... comment'"
  exit 1
fi
mkdir -p /root/.ssh
chmod 700 /root/.ssh
grep -qF "$PUBKEY" /root/.ssh/authorized_keys 2>/dev/null || echo "$PUBKEY" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
echo "Authorized key added for root."
