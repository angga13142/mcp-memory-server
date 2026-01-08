#!/bin/bash
#
# Verify Recovery
# Comprehensive verification after restore
#

set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

FAILED=0

log "🔍 Verifying Recovery"
log "===================="
echo ""

# Check 1: Service Health
log "Check 1: Service Health"
log "----------------------"

services=("prometheus:9090/-/healthy" "grafana:3000/api/health" "mcp-memory-server:8080/health")

for service in "${services[@]}"; do
    IFS=':' read -r name endpoint <<< "$service"
    
    if curl -sf "http://localhost:${endpoint}" > /dev/null 2>&1; then
        log "✅ $name is healthy"
    else
        log "❌ $name is NOT healthy"
        ((FAILED++))
    fi
done

echo ""

# Check 2: Prometheus Data
log "Check 2: Prometheus Data"
log "------------------------"

DATA_POINTS=$(curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result | length')
log "Time series found: $DATA_POINTS"

if [ "$DATA_POINTS" -gt 0 ]; then
    log "✅ Prometheus has data"
else
    log "❌ Prometheus has NO data"
    ((FAILED++))
fi

echo ""

# Check 3: Grafana Dashboards
log "Check 3: Grafana Dashboards"
log "---------------------------"

DASHBOARD_COUNT=$(curl -s -u admin:admin http://localhost:3000/api/search?type=dash-db | jq '. | length')
log "Dashboards found: $DASHBOARD_COUNT"

if [ "$DASHBOARD_COUNT" -gt 0 ]; then
    log "✅ Grafana has dashboards"
else
    log "❌ Grafana has NO dashboards"
    ((FAILED++))
fi

echo ""

# Check 4: Application Database
log "Check 4: Application Database"
log "-----------------------------"

DB_PATH="/var/lib/mcp-memory-server/memory.db"
if [ -f "$DB_PATH" ]; then
    TABLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
    log "Database tables: $TABLE_COUNT"
    
    INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;")
    if [ "$INTEGRITY" = "ok" ]; then
        log "✅ Database integrity OK"
    else
        log "❌ Database integrity FAILED"
        ((FAILED++))
    fi
else
    log "❌ Database NOT found"
    ((FAILED++))
fi

echo ""

# Summary
log "===================="
if [ $FAILED -eq 0 ]; then
    log "✅ ALL CHECKS PASSED"
    exit 0
else
    log "❌ $FAILED CHECK(S) FAILED"
    exit 1
fi
