#!/bin/bash
#
# Restore Application from Backup
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mcp-monitoring/application}"
APP_DATA_DIR="${APP_DATA_DIR:-/var/lib/mcp-memory-server}"
DB_PATH="${DB_PATH:-${APP_DATA_DIR}/memory.db}"
CHROMA_PATH="${CHROMA_PATH:-${APP_DATA_DIR}/chroma_db}"
BACKUP_FILE="${1:-latest}"

# Logging
LOG_FILE="/var/log/mcp-backups/application-restore.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $*"
    exit 1
}

log "Starting application restore..."

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

# Stop application
log "Stopping application..."
docker-compose stop mcp-memory-server || true
sleep 5

# Backup current data
log "Backing up current application data..."
if [ -d "$APP_DATA_DIR" ]; then
    CURRENT_BACKUP="${APP_DATA_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    mv "$APP_DATA_DIR" "$CURRENT_BACKUP"
    log "Current data backed up to: $CURRENT_BACKUP"
fi

# Extract backup
log "Extracting backup..."
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Find backup directory
BACKUP_EXTRACT_DIR=$(find "$TEMP_DIR" -type d -name "app_*" | head -1)

if [ -z "$BACKUP_EXTRACT_DIR" ]; then
    error "Backup directory not found"
fi

# Restore database
log "Restoring database..."
mkdir -p "$(dirname "$DB_PATH")"
if [ -f "${BACKUP_EXTRACT_DIR}/memory.db" ]; then
    cp "${BACKUP_EXTRACT_DIR}/memory.db" "$DB_PATH"
    
    # Verify integrity
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
        log "✅ Database integrity verified"
    else
        error "Database integrity check failed"
    fi
else
    log "WARNING: Database not found in backup"
fi

# Restore ChromaDB
log "Restoring ChromaDB..."
if [ -d "${BACKUP_EXTRACT_DIR}/chroma_db" ]; then
    cp -r "${BACKUP_EXTRACT_DIR}/chroma_db" "$CHROMA_PATH"
    log "ChromaDB restored"
else
    log "WARNING: ChromaDB not found in backup"
fi

# Restore configuration
if [ -f "${BACKUP_EXTRACT_DIR}/config.yaml" ]; then
    cp "${BACKUP_EXTRACT_DIR}/config.yaml" "${APP_DATA_DIR}/config.yaml"
fi

# Set permissions
log "Setting permissions..."
chown -R 1000:1000 "$APP_DATA_DIR"

# Cleanup
rm -rf "$TEMP_DIR"

# Start application
log "Starting application..."
docker-compose start mcp-memory-server

# Wait for application to be ready
log "Waiting for application..."
for i in {1..30}; do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        log "✅ Application is healthy"
        break
    fi
    sleep 2
done

log "Restore completed successfully"
exit 0
