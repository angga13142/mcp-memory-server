#!/bin/bash
#
# Check Backup Health
# Verifies backups are recent and valid
#

set -e

# Configuration
BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-/var/backups/mcp-monitoring}"
MAX_AGE_HOURS="${MAX_AGE_HOURS:-2}"  # Alert if backup older than 2 hours
S3_BUCKET="${S3_BUCKET:-mcp-backups}"

# Logging
LOG_FILE="/var/log/mcp-backups/health-check.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

ISSUES_FOUND=0

# Function to check backup age
check_backup_age() {
    local component=$1
    local backup_dir="${BACKUP_BASE_DIR}/${component}"
    local latest_link="${backup_dir}/latest.tar.gz"
    
    log "Checking $component backup..."
    
    if [ ! -L "$latest_link" ]; then
        log "ERROR: No latest backup found for $component"
        ((ISSUES_FOUND++))
        return 1
    fi
    
    local backup_file=$(readlink -f "$latest_link")
    
    if [ ! -f "$backup_file" ]; then
        log "ERROR: Backup file not found: $backup_file"
        ((ISSUES_FOUND++))
        return 1
    fi
    
    # Check age
    local backup_timestamp=$(stat -c %Y "$backup_file" 2>/dev/null || stat -f %m "$backup_file")
    local current_timestamp=$(date +%s)
    local age_hours=$(( (current_timestamp - backup_timestamp) / 3600 ))
    
    log "$component backup age: ${age_hours} hours"
    
    if [ $age_hours -gt $MAX_AGE_HOURS ]; then
        log "WARNING: $component backup is older than ${MAX_AGE_HOURS} hours"
        ((ISSUES_FOUND++))
    else
        log "✅ $component backup age OK"
    fi
    
    # Verify checksum
    local checksum_file="${backup_file}.sha256"
    if [ -f "$checksum_file" ]; then
        cd "$(dirname "$backup_file")"
        if sha256sum -c "$(basename "$checksum_file")" > /dev/null 2>&1; then
            log "✅ $component checksum verified"
        else
            log "ERROR: $component checksum verification failed"
            ((ISSUES_FOUND++))
        fi
    else
        log "WARNING: No checksum file for $component"
    fi
}

# Function to check S3 sync
check_s3_sync() {
    if ! command -v aws &> /dev/null; then
        log "WARNING: AWS CLI not available, skipping S3 check"
        return 0
    fi
    
    log "Checking S3 sync..."
    
    for component in prometheus grafana application; do
        local backup_dir="${BACKUP_BASE_DIR}/${component}"
        local latest_link="${backup_dir}/latest.tar.gz"
        
        if [ ! -L "$latest_link" ]; then
            continue
        fi
        
        local backup_file=$(readlink -f "$latest_link")
        local backup_name=$(basename "$backup_file")
        local s3_key="monitoring/${component}/${backup_name}"
        
        if aws s3 ls "s3://${S3_BUCKET}/${s3_key}" > /dev/null 2>&1; then
            log "✅ $component backup synced to S3"
        else
            log "WARNING: $component backup not found in S3"
            ((ISSUES_FOUND++))
        fi
    done
}

# Main checks
log "Starting backup health check..."
log "================================"

check_backup_age "prometheus"
check_backup_age "grafana"
check_backup_age "application"

check_s3_sync

log "================================"

if [ $ISSUES_FOUND -eq 0 ]; then
    log "✅ All backup health checks passed"
    exit 0
else
    log "⚠️ Found $ISSUES_FOUND issue(s) with backups"
    
    # Send alert (example with curl to webhook)
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"⚠️ Backup health check found $ISSUES_FOUND issue(s)\"}"
    fi
    
    exit 1
fi
