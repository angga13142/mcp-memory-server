#!/bin/bash
#
# Restore Grafana from Backup
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mcp-monitoring/grafana}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
BACKUP_FILE="${1:-latest}"

# Logging
LOG_FILE="/var/log/mcp-backups/grafana-restore.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $*"
    exit 1
}

log "Starting Grafana restore..."

# Determine backup file
if [ "$BACKUP_FILE" = "latest" ]; then
    BACKUP_FILE="${BACKUP_DIR}/latest.tar.gz"
elif [ ! -f "$BACKUP_FILE" ]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
fi

log "Using backup: $BACKUP_FILE"

# Verify checksum
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "$CHECKSUM_FILE" ]; then
    log "Verifying checksum..."
    cd "$(dirname "$BACKUP_FILE")"
    if ! sha256sum -c "$(basename "$CHECKSUM_FILE")"; then
        error "Checksum verification failed"
    fi
    log "Checksum verified"
fi

# Extract backup
log "Extracting backup..."
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Find backup directory
BACKUP_EXTRACT_DIR=$(find "$TEMP_DIR" -type d -name "grafana_*" | head -1)

if [ -z "$BACKUP_EXTRACT_DIR" ]; then
    error "Backup directory not found"
fi

# Wait for Grafana to be ready
log "Waiting for Grafana..."
for i in {1..30}; do
    if curl -sf "${GRAFANA_URL}/api/health" > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Restore dashboards
log "Restoring dashboards..."
DASHBOARD_COUNT=0

if [ -d "${BACKUP_EXTRACT_DIR}/dashboards" ]; then
    for dashboard_file in "${BACKUP_EXTRACT_DIR}/dashboards"/*.json; do
        if [ -f "$dashboard_file" ]; then
            log "Restoring dashboard: $(basename "$dashboard_file")"
            
            # Extract dashboard JSON
            DASHBOARD_JSON=$(jq '.dashboard' "$dashboard_file")
            
            # Create import payload
            IMPORT_PAYLOAD=$(jq -n \
                --argjson dashboard "$DASHBOARD_JSON" \
                '{dashboard: $dashboard, overwrite: true}')
            
            # Import dashboard
            curl -sf -X POST \
                -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
                -H "Content-Type: application/json" \
                -d "$IMPORT_PAYLOAD" \
                "${GRAFANA_URL}/api/dashboards/db" > /dev/null
            
            if [ $? -eq 0 ]; then
                ((DASHBOARD_COUNT++))
            else
                log "WARNING: Failed to restore dashboard: $(basename "$dashboard_file")"
            fi
        fi
    done
fi

log "Restored $DASHBOARD_COUNT dashboards"

# Restore datasources
log "Restoring datasources..."
if [ -f "${BACKUP_EXTRACT_DIR}/datasources.json" ]; then
    jq -c '.[]' "${BACKUP_EXTRACT_DIR}/datasources.json" | while read datasource; do
        DS_NAME=$(echo "$datasource" | jq -r '.name')
        log "Restoring datasource: $DS_NAME"
        
        curl -sf -X POST \
            -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
            -H "Content-Type: application/json" \
            -d "$datasource" \
            "${GRAFANA_URL}/api/datasources" > /dev/null || true
    done
fi

# Cleanup
rm -rf "$TEMP_DIR"

log "Restore completed successfully"
log "Restored $DASHBOARD_COUNT dashboards"

exit 0
