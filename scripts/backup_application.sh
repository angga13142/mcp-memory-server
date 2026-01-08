#!/bin/bash
#
# Application Backup Script
# Backs up SQLite database and ChromaDB
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mcp-monitoring/application}"
S3_BUCKET="${S3_BUCKET:-mcp-backups}"
S3_PREFIX="${S3_PREFIX:-monitoring/application}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
APP_DATA_DIR="${APP_DATA_DIR:-/var/lib/mcp-memory-server}"
DB_PATH="${DB_PATH:-${APP_DATA_DIR}/memory.db}"
CHROMA_PATH="${CHROMA_PATH:-${APP_DATA_DIR}/chroma_db}"

# Logging
LOG_FILE="/var/log/mcp-backups/application-backup.log"
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
BACKUP_NAME="app_${TIMESTAMP}"
BACKUP_WORK_DIR="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "$BACKUP_WORK_DIR"

log "Starting application backup: $BACKUP_NAME"

# Step 1: Backup SQLite database
log "Backing up SQLite database..."
if [ -f "$DB_PATH" ]; then
    # Use SQLite backup command for consistent backup
    sqlite3 "$DB_PATH" ".backup '${BACKUP_WORK_DIR}/memory.db'"
    
    if [ $? -eq 0 ]; then
        DB_SIZE=$(du -h "${BACKUP_WORK_DIR}/memory.db" | cut -f1)
        log "Database backed up: $DB_SIZE"
        
        # Verify database integrity
        sqlite3 "${BACKUP_WORK_DIR}/memory.db" "PRAGMA integrity_check;" | grep -q "ok"
        if [ $? -eq 0 ]; then
            log "Database integrity verified"
        else
            error "Database integrity check failed"
        fi
    else
        error "Failed to backup database"
    fi
else
    log "WARNING: Database not found at $DB_PATH"
fi

# Step 2: Backup ChromaDB
log "Backing up ChromaDB..."
if [ -d "$CHROMA_PATH" ]; then
    cp -r "$CHROMA_PATH" "${BACKUP_WORK_DIR}/chroma_db"
    
    if [ $? -eq 0 ]; then
        CHROMA_SIZE=$(du -sh "${BACKUP_WORK_DIR}/chroma_db" | cut -f1)
        log "ChromaDB backed up: $CHROMA_SIZE"
    else
        error "Failed to backup ChromaDB"
    fi
else
    log "WARNING: ChromaDB not found at $CHROMA_PATH"
fi

# Step 3: Backup configuration
log "Backing up configuration..."
if [ -f "${APP_DATA_DIR}/config.yaml" ]; then
    cp "${APP_DATA_DIR}/config.yaml" "${BACKUP_WORK_DIR}/config.yaml"
fi

# Step 4: Create metadata
log "Creating backup metadata..."
cat > "${BACKUP_WORK_DIR}/metadata.json" <<EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$TIMESTAMP",
  "database_path": "$DB_PATH",
  "chroma_path": "$CHROMA_PATH",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

# Step 5: Compress backup
log "Compressing backup..."
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
tar -czf "$BACKUP_FILE" -C "$BACKUP_DIR" "$BACKUP_NAME"

if [ $? -ne 0 ]; then
    error "Failed to compress backup"
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup compressed: $BACKUP_SIZE"

# Step 6: Calculate checksum
log "Calculating checksum..."
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"
CHECKSUM=$(cut -d' ' -f1 "$CHECKSUM_FILE")
log "Checksum: $CHECKSUM"

# Step 7: Upload to S3
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

# Step 8: Cleanup
log "Cleaning up temporary files..."
rm -rf "$BACKUP_WORK_DIR"

# Update latest symlink
ln -sf "$BACKUP_FILE" "${BACKUP_DIR}/latest.tar.gz"
ln -sf "$CHECKSUM_FILE" "${BACKUP_DIR}/latest.tar.gz.sha256"

# Cleanup old backups
log "Cleaning up old backups..."
find "$BACKUP_DIR" -name "app_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
find "$BACKUP_DIR" -name "app_*.tar.gz.sha256" -type f -mtime +${RETENTION_DAYS} -delete

log "Backup completed successfully: $BACKUP_FILE"
log "Backup size: $BACKUP_SIZE"

exit 0
