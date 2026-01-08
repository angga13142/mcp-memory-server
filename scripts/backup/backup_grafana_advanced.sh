#!/bin/bash
#
# Advanced Grafana Backup Script
# Backs up dashboards, datasources, and database
#

set -e

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mcp-monitoring/grafana}"
S3_BUCKET="${S3_BUCKET:-mcp-backups}"
S3_PREFIX="${S3_PREFIX:-monitoring/grafana}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
GRAFANA_DATA_DIR="${GRAFANA_DATA_DIR:-/var/lib/grafana}"

# Logging
LOG_FILE="/var/log/mcp-backups/grafana-backup.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $*"
    exit 1
}

# Create backup directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="grafana_${TIMESTAMP}"
BACKUP_WORK_DIR="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "$BACKUP_WORK_DIR"

log "Starting Grafana backup: $BACKUP_NAME"

# Step 1: Export all dashboards
log "Exporting dashboards..."
DASHBOARDS_DIR="${BACKUP_WORK_DIR}/dashboards"
mkdir -p "$DASHBOARDS_DIR"

# Get all dashboard UIDs
DASHBOARD_UIDS=$(curl -sf -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    "${GRAFANA_URL}/api/search?type=dash-db" | jq -r '.[].uid')

if [ -z "$DASHBOARD_UIDS" ]; then
    log "WARNING: No dashboards found"
else
    DASHBOARD_COUNT=0
    for uid in $DASHBOARD_UIDS; do
        log "Exporting dashboard: $uid"
        curl -sf -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
            "${GRAFANA_URL}/api/dashboards/uid/${uid}" \
            > "${DASHBOARDS_DIR}/${uid}.json"
        
        if [ $? -eq 0 ]; then
            ((DASHBOARD_COUNT++))
        else
            log "WARNING: Failed to export dashboard: $uid"
        fi
    done
    log "Exported $DASHBOARD_COUNT dashboards"
fi

# Step 2: Export datasources
log "Exporting datasources..."
curl -sf -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    "${GRAFANA_URL}/api/datasources" \
    > "${BACKUP_WORK_DIR}/datasources.json"

if [ $? -ne 0 ]; then
    log "WARNING: Failed to export datasources"
fi

# Step 3: Backup Grafana database (SQLite)
log "Backing up Grafana database..."
if [ -f "${GRAFANA_DATA_DIR}/grafana.db" ]; then
    cp "${GRAFANA_DATA_DIR}/grafana.db" "${BACKUP_WORK_DIR}/grafana.db"
    log "Database backed up"
else
    log "WARNING: Grafana database not found at ${GRAFANA_DATA_DIR}/grafana.db"
fi

# Step 4: Backup configuration
log "Backing up configuration..."
if [ -f "/etc/grafana/grafana.ini" ]; then
    cp "/etc/grafana/grafana.ini" "${BACKUP_WORK_DIR}/grafana.ini"
elif [ -f "${GRAFANA_DATA_DIR}/grafana.ini" ]; then
    cp "${GRAFANA_DATA_DIR}/grafana.ini" "${BACKUP_WORK_DIR}/grafana.ini"
fi

# Step 5: Create metadata
log "Creating backup metadata..."
cat > "${BACKUP_WORK_DIR}/metadata.json" <<EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$TIMESTAMP",
  "grafana_version": "$(curl -sf "${GRAFANA_URL}/api/health" | jq -r '.version' || echo 'unknown')",
  "dashboard_count": $DASHBOARD_COUNT,
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

# Step 6: Compress backup
log "Compressing backup..."
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
tar -czf "$BACKUP_FILE" -C "$BACKUP_DIR" "$BACKUP_NAME"

if [ $? -ne 0 ]; then
    error "Failed to compress backup"
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup compressed: $BACKUP_SIZE"

# Step 7: Calculate checksum
log "Calculating checksum..."
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"
CHECKSUM=$(cut -d' ' -f1 "$CHECKSUM_FILE")
log "Checksum: $CHECKSUM"

# Step 8: Upload to S3
if command -v aws &> /dev/null; then
    log "Uploading to S3..."
    
    aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_NAME}.tar.gz" \
        --storage-class STANDARD_IA
    
    if [ $? -eq 0 ]; then
        log "Backup uploaded to S3"
        aws s3 cp "$CHECKSUM_FILE" "s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_NAME}.tar.gz.sha256"
    else
        log "WARNING: Failed to upload to S3"
    fi
else
    log "WARNING: AWS CLI not found, skipping S3 upload"
fi

# Step 9: Cleanup
log "Cleaning up temporary files..."
rm -rf "$BACKUP_WORK_DIR"

# Update latest symlink
ln -sf "$BACKUP_FILE" "${BACKUP_DIR}/latest.tar.gz"
ln -sf "$CHECKSUM_FILE" "${BACKUP_DIR}/latest.tar.gz.sha256"

# Cleanup old backups
log "Cleaning up old backups..."
find "$BACKUP_DIR" -name "grafana_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
find "$BACKUP_DIR" -name "grafana_*.tar.gz.sha256" -type f -mtime +${RETENTION_DAYS} -delete

log "Backup completed successfully: $BACKUP_FILE"
log "Backup size: $BACKUP_SIZE"

exit 0
