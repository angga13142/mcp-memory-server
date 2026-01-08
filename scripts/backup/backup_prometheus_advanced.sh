#!/bin/bash
#
# Advanced Prometheus Backup Script
# Creates snapshot, compresses, verifies, and uploads to S3
#

set -e

# Configuration
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mcp-monitoring/prometheus}"
S3_BUCKET="${S3_BUCKET:-mcp-backups}"
S3_PREFIX="${S3_PREFIX:-monitoring/prometheus}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
PROMETHEUS_DATA_DIR="${PROMETHEUS_DATA_DIR:-/var/lib/prometheus}"

# Logging
LOG_FILE="/var/log/mcp-backups/prometheus-backup.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $*"
    exit 1
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate snapshot name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_NAME="snapshot_${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DIR}/${SNAPSHOT_NAME}.tar.gz"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

log "Starting Prometheus backup: $SNAPSHOT_NAME"

# Step 1: Create Prometheus snapshot via API
log "Creating Prometheus snapshot..."
SNAPSHOT_RESPONSE=$(curl -sf -XPOST "${PROMETHEUS_URL}/api/v1/admin/tsdb/snapshot")

if [ $? -ne 0 ]; then
    error "Failed to create Prometheus snapshot"
fi

# Extract snapshot name from response
SNAPSHOT_DIR=$(echo "$SNAPSHOT_RESPONSE" | jq -r '.data.name')

if [ -z "$SNAPSHOT_DIR" ] || [ "$SNAPSHOT_DIR" = "null" ]; then
    error "Failed to parse snapshot name from response"
fi

log "Snapshot created: $SNAPSHOT_DIR"

# Step 2: Compress snapshot
log "Compressing snapshot..."
SNAPSHOT_PATH="${PROMETHEUS_DATA_DIR}/snapshots/${SNAPSHOT_DIR}"

if [ ! -d "$SNAPSHOT_PATH" ]; then
    error "Snapshot directory not found: $SNAPSHOT_PATH"
fi

tar -czf "$BACKUP_FILE" -C "${PROMETHEUS_DATA_DIR}/snapshots" "$SNAPSHOT_DIR"

if [ $? -ne 0 ]; then
    error "Failed to compress snapshot"
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup compressed: $BACKUP_SIZE"

# Step 3: Calculate checksum
log "Calculating checksum..."
sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"

if [ $? -ne 0 ]; then
    error "Failed to calculate checksum"
fi

CHECKSUM=$(cut -d' ' -f1 "$CHECKSUM_FILE")
log "Checksum: $CHECKSUM"

# Step 4: Upload to S3
if command -v aws &> /dev/null; then
    log "Uploading to S3..."
    
    aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/${S3_PREFIX}/${SNAPSHOT_NAME}.tar.gz" \
        --storage-class STANDARD_IA \
        --metadata "checksum=${CHECKSUM},timestamp=${TIMESTAMP}"
    
    if [ $? -ne 0 ]; then
        log "WARNING: Failed to upload backup to S3"
    else
        log "Backup uploaded to S3"
    fi
    
    # Upload checksum
    aws s3 cp "$CHECKSUM_FILE" "s3://${S3_BUCKET}/${S3_PREFIX}/${SNAPSHOT_NAME}.tar.gz.sha256"
else
    log "WARNING: AWS CLI not found, skipping S3 upload"
fi

# Step 5: Update latest symlink
log "Updating latest symlink..."
ln -sf "$BACKUP_FILE" "${BACKUP_DIR}/latest.tar.gz"
ln -sf "$CHECKSUM_FILE" "${BACKUP_DIR}/latest.tar.gz.sha256"

# Step 6: Cleanup old local backups
log "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "snapshot_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
find "$BACKUP_DIR" -name "snapshot_*.tar.gz.sha256" -type f -mtime +${RETENTION_DAYS} -delete

# Step 7: Cleanup snapshot directory
log "Cleaning up snapshot directory..."
rm -rf "$SNAPSHOT_PATH"

# Step 8: Verify backup integrity
log "Verifying backup integrity..."
if tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
    log "Backup integrity verified"
else
    error "Backup integrity check failed"
fi

# Step 9: Update metrics
if command -v curl &> /dev/null; then
    BACKUP_SIZE_BYTES=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE")
    # Send metrics to Prometheus pushgateway if available
    # curl -X POST http://localhost:9091/metrics/job/backup_prometheus \
    #     --data-binary "mcp_backup_last_success_timestamp_seconds $(date +%s)"
fi

log "Backup completed successfully: $BACKUP_FILE"
log "Backup size: $BACKUP_SIZE"

# Exit successfully
exit 0
