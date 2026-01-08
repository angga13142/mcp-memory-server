# Phase 4: Backup & Recovery Strategy

## 🎯 Objective

Implement comprehensive backup and disaster recovery procedures for the monitoring and observability infrastructure to ensure:

- **Zero data loss** for critical metrics
- **Rapid recovery** (<1 hour RTO)
- **Minimal data loss** (<5 minutes RPO)
- **Automated backups** with validation
- **Tested recovery procedures**

---

## 📋 TABLE OF CONTENTS

1. [Backup Strategy](#backup-strategy)
2. [Backup Implementation](#backup-implementation)
3. [Recovery Procedures](#recovery-procedures)
4. [Disaster Recovery](#disaster-recovery)
5. [Testing & Validation](#testing--validation)

---

## 📊 SECTION 1: BACKUP STRATEGY

### 1.1 What Needs to Be Backed Up

#### Critical Data (Must Backup)

| Component           | Data                | Frequency | Retention | Priority    |
| ------------------- | ------------------- | --------- | --------- | ----------- |
| **Prometheus TSDB** | Time series data    | Hourly    | 30 days   | 🔴 Critical |
| **Grafana**         | Dashboards          | Daily     | 90 days   | 🟠 High     |
| **Grafana**         | Datasources         | Daily     | 90 days   | 🟠 High     |
| **Grafana**         | Users               | Daily     | 90 days   | 🟡 Medium   |
| **Alertmanager**    | Configuration       | Daily     | 90 days   | 🟠 High     |
| **Application**     | Configuration files | Daily     | 90 days   | 🔴 Critical |
| **Application**     | SQLite database     | Hourly    | 30 days   | 🔴 Critical |
| **Vector Store**    | ChromaDB data       | Daily     | 30 days   | 🟠 High     |

#### Configuration (Version Controlled)

| Item                   | Backup Method | Location                              |
| ---------------------- | ------------- | ------------------------------------- |
| **Prometheus config**  | Git           | monitoring/prometheus.yml             |
| **Alert rules**        | Git           | monitoring/alerts/\*.yml              |
| **Dashboard JSON**     | Git           | monitoring/grafana/dashboards/\*.json |
| **Docker Compose**     | Git           | docker-compose\*.yml                  |
| **Application config** | Git           | config\*.yaml                         |

---

### 1.2 Backup Requirements

#### Recovery Time Objective (RTO)

| Scenario                         | Target RTO | Maximum Acceptable |
| -------------------------------- | ---------- | ------------------ |
| **Prometheus data loss**         | 30 minutes | 1 hour             |
| **Grafana unavailable**          | 15 minutes | 30 minutes         |
| **Complete infrastructure loss** | 4 hours    | 8 hours            |
| **Configuration corruption**     | 5 minutes  | 15 minutes         |

#### Recovery Point Objective (RPO)

| Data Type            | Target RPO | Maximum Data Loss |
| -------------------- | ---------- | ----------------- |
| **Metrics data**     | 5 minutes  | 15 minutes        |
| **Configuration**    | 0 (Git)    | 0                 |
| **Dashboards**       | 24 hours   | 48 hours          |
| **Application data** | 15 minutes | 1 hour            |

---

### 1.3 Backup Storage Strategy

#### Storage Locations

```
Primary Backup (Local):
/var/backups/mcp-monitoring/
├── prometheus/
│   ├── snapshots/
│   │   ├── snapshot_20250108_100000.tar.gz
│   │   ├── snapshot_20250108_110000.tar.gz
│   │   └── ...
│   └── latest -> snapshot_20250108_120000.tar.gz
├── grafana/
│   ├── dashboards_20250108.tar.gz
│   ├── datasources_20250108.tar.gz
│   └── sqlite_20250108.db.gz
├── application/
│   ├── database_20250108_100000.db.gz
│   ├── config_20250108.tar.gz
│   └── chroma_20250108.tar.gz
└── logs/
    └── backup_20250108.log

Secondary Backup (Off-site):
s3://mcp-backups/monitoring/
├── prometheus/
├── grafana/
└── application/
```

#### Retention Policy

```yaml
Retention Rules:
  Hourly Backups:
    keep: 24 # Last 24 hours

  Daily Backups:
    keep: 7 # Last 7 days

  Weekly Backups:
    keep: 4 # Last 4 weeks

  Monthly Backups:
    keep: 12 # Last 12 months

  Yearly Backups:
    keep: 3 # Last 3 years
```

---

## 🔧 SECTION 2: BACKUP IMPLEMENTATION

### 2.1 Prometheus Backup

#### Automated Backup Script

**File:** scripts/backup_prometheus_advanced.sh

```bash
#!/bin/bash
#
# Advanced Prometheus Backup Script
# - Creates snapshots via API
# - Compresses and archives
# - Uploads to off-site storage
# - Validates backup integrity
# - Implements retention policy
#

set -euo pipefail

BACKUP_DIR="/var/backups/mcp-monitoring/prometheus"
PROMETHEUS_URL="http://localhost:9090"
S3_BUCKET="s3://mcp-backups/monitoring/prometheus"
RETENTION_HOURS=24
RETENTION_DAYS=7
LOG_FILE="/var/backups/mcp-monitoring/logs/prometheus_backup.log"

mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔄 Starting Prometheus backup..."

log "Step 1: Creating Prometheus snapshot..."

SNAPSHOT_RESPONSE=$(curl -s -X POST "$PROMETHEUS_URL/api/v1/admin/tsdb/snapshot" || true)

if [ $? -ne 0 ]; then
    log "❌ ERROR: Failed to create snapshot"
    exit 1
fi

SNAPSHOT_NAME=$(echo "$SNAPSHOT_RESPONSE" | jq -r '.data.name')

if [ -z "$SNAPSHOT_NAME" ] || [ "$SNAPSHOT_NAME" == "null" ]; then
    log "❌ ERROR: Invalid snapshot response"
    exit 1
fi

log "✅ Snapshot created: $SNAPSHOT_NAME"

log "Step 2: Copying snapshot from container..."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="snapshot_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

docker cp prometheus:/prometheus/snapshots/$SNAPSHOT_NAME "$BACKUP_PATH"

if [ $? -ne 0 ]; then
    log "❌ ERROR: Failed to copy snapshot"
    exit 1
fi

log "✅ Snapshot copied to $BACKUP_PATH"

log "Step 3: Compressing backup..."

tar -czf "${BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
BACKUP_SIZE=$(du -h "${BACKUP_PATH}.tar.gz" | cut -f1)

log "✅ Backup compressed (${BACKUP_SIZE})"

log "Step 4: Calculating checksum..."

CHECKSUM=$(sha256sum "${BACKUP_PATH}.tar.gz" | cut -d' ' -f1)
echo "$CHECKSUM" > "${BACKUP_PATH}.tar.gz.sha256"

log "✅ Checksum: $CHECKSUM"

if command -v aws &> /dev/null; then
    log "Step 5: Uploading to S3..."

    aws s3 cp "${BACKUP_PATH}.tar.gz" \
        "${S3_BUCKET}/$(basename ${BACKUP_PATH}.tar.gz)" \
        --storage-class STANDARD_IA

    aws s3 cp "${BACKUP_PATH}.tar.gz.sha256" \
        "${S3_BUCKET}/$(basename ${BACKUP_PATH}.tar.gz.sha256)"

    log "✅ Uploaded to S3"
else
    log "⚠️ WARNING: AWS CLI not found, skipping S3 upload"
fi

log "Step 6: Cleaning up..."

rm -rf "$BACKUP_PATH"

log "✅ Cleanup complete"

log "Step 7: Applying retention policy..."

find "$BACKUP_DIR" -name "snapshot_*.tar.gz" -mmin +$((RETENTION_HOURS * 60)) -delete
DELETED_COUNT=$(find "$BACKUP_DIR" -name "snapshot_*.tar.gz" -mmin +$((RETENTION_HOURS * 60)) | wc -l)

log "✅ Deleted $DELETED_COUNT old backups"

log "Step 8: Updating latest symlink..."

ln -sf "${BACKUP_PATH}.tar.gz" "${BACKUP_DIR}/latest.tar.gz"

log "✅ Latest symlink updated"

log "Step 9: Verifying backup integrity..."

if tar -tzf "${BACKUP_PATH}.tar.gz" > /dev/null 2>&1; then
    log "✅ Backup integrity verified"
else
    log "❌ ERROR: Backup integrity check failed"
    exit 1
fi

log "================================================"
log "✅ BACKUP COMPLETED SUCCESSFULLY"
log "================================================"
log "Backup file: ${BACKUP_PATH}.tar.gz"
log "Size: ${BACKUP_SIZE}"
log "Checksum: $CHECKSUM"
log "================================================"

if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ Prometheus backup completed: ${BACKUP_SIZE}\"}"
fi

exit 0
```

Make executable:

```bash
chmod +x scripts/backup_prometheus_advanced.sh
```

---

#### Cron Job Configuration

**File:** /etc/cron.d/mcp-prometheus-backup

```cron
# Prometheus Backup Schedule
# Runs every hour at :05 past the hour

5 * * * * root /opt/mcp-memory-server/scripts/backup_prometheus_advanced.sh >> /var/log/prometheus-backup.log 2>&1
0 2 * * * root /opt/mcp-memory-server/scripts/verify_backups.sh >> /var/log/backup-verification.log 2>&1
```

---

### 2.2 Grafana Backup

#### Grafana Backup Script

**File:** scripts/backup_grafana_advanced.sh

```bash
#!/bin/bash
#
# Advanced Grafana Backup Script
# - Exports all dashboards
# - Exports datasources
# - Backs up SQLite database
# - Backs up configuration
#

set -euo pipefail

BACKUP_DIR="/var/backups/mcp-monitoring/grafana"
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
LOG_FILE="/var/backups/mcp-monitoring/logs/grafana_backup.log"

mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔄 Starting Grafana backup..."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/grafana_${TIMESTAMP}"
mkdir -p "$BACKUP_PATH"

log "Step 1: Exporting dashboards..."

DASHBOARD_UIDS=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    "$GRAFANA_URL/api/search?type=dash-db" | jq -r '.[].uid')

DASHBOARD_COUNT=0
for uid in $DASHBOARD_UIDS; do
    DASHBOARD_JSON=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        "$GRAFANA_URL/api/dashboards/uid/$uid")

    DASHBOARD_TITLE=$(echo "$DASHBOARD_JSON" | jq -r '.dashboard.title' | tr ' ' '_')

    echo "$DASHBOARD_JSON" > "$BACKUP_PATH/dashboard_${uid}_${DASHBOARD_TITLE}.json"

    ((DASHBOARD_COUNT++))
done

log "✅ Exported $DASHBOARD_COUNT dashboards"

log "Step 2: Exporting datasources..."

curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    "$GRAFANA_URL/api/datasources" > "$BACKUP_PATH/datasources.json"

DATASOURCE_COUNT=$(jq '. | length' "$BACKUP_PATH/datasources.json")

log "✅ Exported $DATASOURCE_COUNT datasources"

log "Step 3: Backing up Grafana database..."

docker cp grafana:/var/lib/grafana/grafana.db "$BACKUP_PATH/grafana.db"

if [ -f "$BACKUP_PATH/grafana.db" ]; then
    gzip "$BACKUP_PATH/grafana.db"
    log "✅ Database backed up and compressed"
else
    log "❌ ERROR: Failed to backup database"
    exit 1
fi

log "Step 4: Backing up configuration..."

docker cp grafana:/etc/grafana/grafana.ini "$BACKUP_PATH/grafana.ini" 2>/dev/null || true

docker cp grafana:/etc/grafana/provisioning "$BACKUP_PATH/provisioning" 2>/dev/null || true

log "✅ Configuration backed up"

log "Step 5: Compressing backup..."

tar -czf "${BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR" "$(basename $BACKUP_PATH)"
BACKUP_SIZE=$(du -h "${BACKUP_PATH}.tar.gz" | cut -f1)

log "✅ Backup compressed (${BACKUP_SIZE})"

CHECKSUM=$(sha256sum "${BACKUP_PATH}.tar.gz" | cut -d' ' -f1)
echo "$CHECKSUM" > "${BACKUP_PATH}.tar.gz.sha256"

log "✅ Checksum: $CHECKSUM"

if command -v aws &> /dev/null; then
    log "Step 7: Uploading to S3..."

    aws s3 cp "${BACKUP_PATH}.tar.gz" \
        "s3://mcp-backups/monitoring/grafana/$(basename ${BACKUP_PATH}.tar.gz)"

    log "✅ Uploaded to S3"
fi

rm -rf "$BACKUP_PATH"

log "✅ Cleanup complete"

find "$BACKUP_DIR" -name "grafana_*.tar.gz" -mtime +30 -delete

log "✅ Retention policy applied"

log "================================================"
log "✅ GRAFANA BACKUP COMPLETED"
log "================================================"
log "Dashboards: $DASHBOARD_COUNT"
log "Datasources: $DATASOURCE_COUNT"
log "Size: ${BACKUP_SIZE}"
log "================================================"

exit 0
```

---

### 2.3 Application Data Backup

#### Application Backup Script

**File:** scripts/backup_application.sh

```bash
#!/bin/bash
#
# Application Data Backup Script
# - SQLite database
# - ChromaDB vector store
# - Configuration files
# - Log files
#

set -euo pipefail

BACKUP_DIR="/var/backups/mcp-monitoring/application"
LOG_FILE="/var/backups/mcp-monitoring/logs/application_backup.log"
APP_DATA_DIR="/var/mcp-data"

mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔄 Starting application backup..."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/app_${TIMESTAMP}"
mkdir -p "$BACKUP_PATH"

log "Step 1: Backing up SQLite database..."

docker exec mcp-memory-server sqlite3 /app/data/memory.db ".backup '$BACKUP_PATH/memory.db'"

if [ -f "$BACKUP_PATH/memory.db" ]; then
    gzip "$BACKUP_PATH/memory.db"
    log "✅ Database backed up ($(du -h "$BACKUP_PATH/memory.db.gz" | cut -f1))"
else
    log "❌ ERROR: Database backup failed"
    exit 1
fi

log "Step 2: Backing up ChromaDB..."

docker cp mcp-memory-server:/app/data/chroma_db "$BACKUP_PATH/chroma_db"

CHROMA_SIZE=$(du -sh "$BACKUP_PATH/chroma_db" | cut -f1)
log "✅ ChromaDB backed up (${CHROMA_SIZE})"

log "Step 3: Backing up configuration..."

cp config.yaml "$BACKUP_PATH/config.yaml"
cp config.prod.yaml "$BACKUP_PATH/config.prod.yaml" 2>/dev/null || true

log "✅ Configuration backed up"

log "Step 4: Compressing..."

tar -czf "${BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR" "$(basename $BACKUP_PATH)"
BACKUP_SIZE=$(du -h "${BACKUP_PATH}.tar.gz" | cut -f1)

log "✅ Compressed (${BACKUP_SIZE})"

CHECKSUM=$(sha256sum "${BACKUP_PATH}.tar.gz" | cut -d' ' -f1)
echo "$CHECKSUM" > "${BACKUP_PATH}.tar.gz.sha256"

if command -v aws &> /dev/null; then
    aws s3 cp "${BACKUP_PATH}.tar.gz" \
        "s3://mcp-backups/monitoring/application/$(basename ${BACKUP_PATH}.tar.gz)"
    log "✅ Uploaded to S3"
fi

rm -rf "$BACKUP_PATH"

find "$BACKUP_DIR" -name "app_*.tar.gz" -mmin +$((24 * 60)) -delete

log "================================================"
log "✅ APPLICATION BACKUP COMPLETED"
log "================================================"
log "Size: ${BACKUP_SIZE}"
log "Checksum: $CHECKSUM"
log "================================================"

exit 0
```

---

### 2.4 Backup Monitoring & Alerting

#### Backup Health Check Script

**File:** scripts/check_backup_health.sh

```bash
#!/bin/bash
#
# Backup Health Check Script
# Monitors backup status and alerts on failures
#

set -euo pipefail

BACKUP_BASE="/var/backups/mcp-monitoring"
ALERT_FILE="/tmp/backup_alerts.txt"

> "$ALERT_FILE"

check_prometheus_backup() {
    LATEST_BACKUP=$(find "$BACKUP_BASE/prometheus" -name "snapshot_*.tar.gz" -mmin -120 | head -1)

    if [ -z "$LATEST_BACKUP" ]; then
        echo "❌ CRITICAL: No Prometheus backup in last 2 hours" >> "$ALERT_FILE"
        return 1
    fi

    echo "✅ Prometheus backup OK"
    return 0
}

check_grafana_backup() {
    LATEST_BACKUP=$(find "$BACKUP_BASE/grafana" -name "grafana_*.tar.gz" -mtime -2 | head -1)

    if [ -z "$LATEST_BACKUP" ]; then
        echo "⚠️ WARNING: No Grafana backup in last 2 days" >> "$ALERT_FILE"
        return 1
    fi

    echo "✅ Grafana backup OK"
    return 0
}

check_application_backup() {
    LATEST_BACKUP=$(find "$BACKUP_BASE/application" -name "app_*.tar.gz" -mmin -120 | head -1)

    if [ -z "$LATEST_BACKUP" ]; then
        echo "❌ CRITICAL: No application backup in last 2 hours" >> "$ALERT_FILE"
        return 1
    fi

    echo "✅ Application backup OK"
    return 0
}

check_s3_sync() {
    if ! command -v aws &> /dev/null; then
        echo "⚠️ WARNING: AWS CLI not installed, cannot check S3" >> "$ALERT_FILE"
        return 0
    fi

    S3_COUNT=$(aws s3 ls s3://mcp-backups/monitoring/ --recursive | wc -l)

    if [ "$S3_COUNT" -lt 10 ]; then
        echo "⚠️ WARNING: Low S3 backup count: $S3_COUNT" >> "$ALERT_FILE"
        return 1
    fi

    echo "✅ S3 sync OK ($S3_COUNT files)"
    return 0
}

echo "🔍 Checking backup health..."
echo ""

FAILED=0

check_prometheus_backup || ((FAILED++))
check_grafana_backup || ((FAILED++))
check_application_backup || ((FAILED++))
check_s3_sync || ((FAILED++))

echo ""

if [ $FAILED -gt 0 ]; then
    echo "❌ BACKUP HEALTH CHECK FAILED"
    echo ""
    cat "$ALERT_FILE"

    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        ALERT_TEXT=$(tr '\n' ' ' < "$ALERT_FILE")
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"🚨 Backup Health Alert: $ALERT_TEXT\"}"
    fi

    exit 1
else
    echo "✅ ALL BACKUP CHECKS PASSED"
    exit 0
fi
```

---

## 🛠️ SECTION 3: RECOVERY PROCEDURES

### 3.1 Prometheus Recovery

- Full restore (checksum + health checks): scripts/restore_prometheus.sh

```bash
sudo ./scripts/restore_prometheus.sh /var/backups/mcp-monitoring/prometheus/snapshot_20250108_120000.tar.gz
# or
sudo ./scripts/restore_prometheus.sh latest
```

- Rapid restore (minimal validation): scripts/restore_prometheus_quick.sh

```bash
sudo ./scripts/restore_prometheus_quick.sh
```

What it does: verify archive, stop Prometheus, backup current data, extract snapshot, set ownership 65534:65534, start container, verify /-/healthy.

### 3.2 Grafana Recovery

- Full restore (datasources, dashboards, optional DB): scripts/restore_grafana.sh

```bash
./scripts/restore_grafana.sh latest
# or specific file
./scripts/restore_grafana.sh /var/backups/mcp-monitoring/grafana/grafana_20250108_010000.tar.gz
```

What it does: checksum verify, start Grafana if needed, restore datasources (recreates IDs), restore dashboards (overwrite=true), optional DB replace, Slack notify.

### 3.3 Application Recovery

- Full restore (SQLite + ChromaDB + configs): scripts/restore_application.sh

```bash
sudo ./scripts/restore_application.sh latest
# or
sudo ./scripts/restore_application.sh /var/backups/mcp-monitoring/application/app_20250108_120000.tar.gz
```

What it does: checksum verify, stop app, backup current DB/vector store, restore memory.db, integrity check, restore chroma_db and configs, restart and health check.

### 3.4 Point-in-Time Recovery

- Aligns Prometheus, app, Grafana to closest backups before a timestamp: scripts/restore_point_in_time.sh

```bash
sudo ./scripts/restore_point_in_time.sh "2025-01-08 14:30:00"
```

### 3.5 Post-Recovery Verification

- Validate stack health after any restore: scripts/verify_recovery.sh

```bash
./scripts/verify_recovery.sh
```

Checks: service health (app/prom/grafana/alertmanager), metric count, Prometheus series count, Grafana dashboards present, DB integrity, alert rules loaded.

---

## 🌪️ SECTION 4: DISASTER RECOVERY

### 4.1 DR Scenarios

- **Total node loss:** Re-provision host, pull images, restore latest backups.
- **Prometheus TSDB corruption:** Stop Prometheus, restore latest snapshot, verify scrape targets.
- **Grafana outage:** Restore Grafana backup, re-import datasource/dashboards if needed.
- **S3 unavailable:** Rely on local backups; delay restores until S3 returns.

### 4.2 DR Playbook (Abbreviated)

1. Declare incident, page on-call SRE.
2. Identify blast radius (Prometheus/Grafana/app).
3. Choose latest valid backup (check checksums).
4. Restore component(s) per recovery scripts.
5. Validate: health endpoints, dashboards, alerts, metrics freshness.
6. Communicate status and resolution.

---

## ✅ SECTION 5: TESTING & VALIDATION

### 5.1 Backup Verification

- Nightly job runs `scripts/verify_backups.sh` (future) to:
  - List latest backups per component.
  - Validate checksums.
  - Test tar extraction.
  - Alert via Slack on failure.

### 5.2 Restore Drills

- Quarterly restore test:
  - Restore Prometheus from snapshot to staging.
  - Restore Grafana dashboards and datasource.
  - Restore application DB + ChromaDB.
  - Run smoke tests (metrics scraped, dashboards load, alerts evaluate).

### 5.3 Monitoring

- Grafana dashboard for backups:
  - Backup success/failure counts.
  - Age of latest backup per component.
  - S3 sync lag.

---

**Status:** Ready for implementation ✅

**Last Updated:** 2025-01-08
