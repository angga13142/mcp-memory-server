#!/bin/bash
# Ransomware recovery: isolate, wipe, rebuild from clean backups

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_URL=$(git -C "$REPO_DIR" config --get remote.origin.url 2>/dev/null || echo "")
GIT_REF=${1:-v1.0.0}
BACKUP_BASE="/var/backups/mcp-monitoring"
COMPOSE_APP="docker-compose.yml"
COMPOSE_MON="docker-compose.monitoring.yml"

confirm() {
  local prompt=$1
  read -r -p "$prompt" reply
  [[ $reply == "$2" ]]
}

if ! confirm "Type 'RECOVER' to proceed with ransomware recovery: " "RECOVER"; then
  echo "Cancelled"
  exit 0
fi

if ! confirm "This will WIPE local data. Type 'WIPE' to continue: " "WIPE"; then
  echo "Cancelled"
  exit 0
fi

[ -n "$REPO_URL" ] || { echo "Missing repo URL; cannot re-clone"; exit 1; }

echo "🔒 Isolating and shutting down services"
if [ -f "$REPO_DIR/$COMPOSE_APP" ]; then (cd "$REPO_DIR" && docker-compose -f "$COMPOSE_APP" down || true); fi
if [ -f "$REPO_DIR/$COMPOSE_MON" ]; then (cd "$REPO_DIR" && docker-compose -f "$COMPOSE_MON" down || true); fi
sudo systemctl stop docker || true

echo "🗑️  Wiping compromised data"
sudo rm -rf /var/mcp-data/* /var/mcp-logs/* "$REPO_DIR" "$BACKUP_BASE"

echo "🔧 Recreating directories"
sudo mkdir -p /var/mcp-data/{prometheus,grafana,redis} /var/mcp-logs "$BACKUP_BASE"/{prometheus,grafana,application,logs}
sudo chown -R $USER:$USER /var/mcp-data /var/mcp-logs "$BACKUP_BASE"
sudo chmod -R 755 /var/mcp-data /var/mcp-logs "$BACKUP_BASE"

echo "🚀 Restarting Docker"
sudo systemctl start docker

echo "📥 Cloning clean code"
cd /opt
sudo git clone "$REPO_URL" mcp-memory-server
sudo chown -R $USER:$USER mcp-memory-server
cd mcp-memory-server
git checkout "$GIT_REF"

echo "📥 Downloading backups from S3"
aws s3 sync s3://mcp-backups/monitoring/prometheus/ "$BACKUP_BASE/prometheus/" --exclude "*" --include "snapshot_*.tar.gz" --include "snapshot_*.sha256"
aws s3 sync s3://mcp-backups/monitoring/grafana/ "$BACKUP_BASE/grafana/" --exclude "*" --include "grafana_*.tar.gz" --include "grafana_*.sha256"
aws s3 sync s3://mcp-backups/monitoring/application/ "$BACKUP_BASE/application/" --exclude "*" --include "app_*.tar.gz" --include "app_*.sha256"

echo "🔍 Verifying checksums"
for f in $(find "$BACKUP_BASE" -name '*.tar.gz'); do
  if [ -f "$f.sha256" ]; then
    exp=$(cat "$f.sha256")
    act=$(sha256sum "$f" | cut -d' ' -f1)
    [ "$exp" = "$act" ] || { echo "Checksum mismatch: $f"; exit 1; }
  fi
done

echo "🏗️  Rebuilding infrastructure"
docker-compose -f docker-compose.monitoring.yml up -d
docker-compose up -d
sleep 30

if command -v clamscan >/dev/null 2>&1; then
  echo "🔍 Scanning backups with ClamAV"
  clamscan -r "$BACKUP_BASE" || true
fi

echo "💾 Restoring data"
sudo ./scripts/restore_prometheus.sh latest
./scripts/restore_grafana.sh latest
sudo ./scripts/restore_application.sh latest

echo "✅ Running verification"
./scripts/verify_recovery.sh || true

echo "⚠️  IMPORTANT: rotate all secrets (Grafana, Redis, API keys, SSH keys) and perform a full security audit."

cat <<'NEXT'
CRITICAL NEXT STEPS:
1) Change ALL passwords and keys
2) Review access logs and run forensics
3) Notify stakeholders and, if required, authorities
4) File incident report and improve security posture
NEXT
