#!/bin/bash
#
# Quick Repository Audit - Condensed Version
#

# set -e

echo "🔍 REPOSITORY AUDIT - angga13142/mcp-memory-server"
echo "===================================================="
echo ""

PASS=0
FAIL=0
WARN=0

# Function definitions
check() {
    local path=$1
    local type=$2
    local critical=$3
    
    if [ "$type" = "file" ]; then
        if [ -f "$path" ]; then
            echo "✅ $path"
            ((PASS++))
            return 0
        fi
    elif [ "$type" = "dir" ]; then
        if [ -d "$path" ]; then
            echo "✅ $path"
            ((PASS++))
            return 0
        fi
    elif [ "$type" = "exec" ]; then
        if [ -x "$path" ]; then
            echo "✅ $path (executable)"
            ((PASS++))
            return 0
        fi
    fi
    
    if [ "$critical" = "CRITICAL" ]; then
        echo "❌ MISSING (CRITICAL): $path"
        ((FAIL++))
    else
        echo "⚠️  MISSING (optional): $path"
        ((WARN++))
    fi
    return 1
}

echo "═══ PHASE 3: MONITORING ═══"
check "src/monitoring/metrics/journal_metrics.py" "file" "CRITICAL"
check "src/monitoring/metrics/database_metrics.py" "file" "CRITICAL"
check "src/monitoring/metrics/vector_store_metrics.py" "file" "CRITICAL"
check "src/monitoring/metrics/system_metrics.py" "file" "CRITICAL"
check "src/monitoring/logging/formatters.py" "file" "CRITICAL"
check "src/monitoring/decorators.py" "file" "CRITICAL"
check "monitoring/prometheus.yml" "file" "CRITICAL"
check "monitoring/alerts/journal_alerts.yml" "file" "CRITICAL"
check "monitoring/grafana/dashboards" "dir" "CRITICAL"
check "deploy/docker-compose.monitoring.yml" "file" "CRITICAL"
echo ""

echo "═══ PHASE 4: BACKUP & RECOVERY ═══"
check "scripts/backup/backup_prometheus_advanced.sh" "exec" "CRITICAL"
check "scripts/backup/backup_grafana_advanced.sh" "exec" "CRITICAL"
check "scripts/backup/backup_application.sh" "exec" "CRITICAL"
check "scripts/backup/restore_prometheus.sh" "exec" "CRITICAL"
check "scripts/backup/restore_grafana.sh" "exec" "CRITICAL"
check "scripts/backup/restore_application.sh" "exec" "CRITICAL"
check "scripts/backup/verify_recovery.sh" "exec" "CRITICAL"
check "docs/disaster-recovery/complete-loss-recovery.md" "file" "CRITICAL"
echo ""

echo "═══ PHASE 5.1: SYSTEM METRICS ═══"
check "src/monitoring/metrics/system_metrics.py" "file" "CRITICAL"
check "src/monitoring/collectors.py" "file" "CRITICAL"
check "tests/unit/test_system_metrics.py" "file" "CRITICAL"
echo ""

echo "═══ PHASE 5.2: LOAD TESTING ═══"
check "tests/load/test_metrics_performance.py" "file" "CRITICAL"
check "tests/load/conftest.py" "file" "CRITICAL"
check "scripts/load_testing/run_load_tests.sh" "exec" "CRITICAL"
echo ""

echo "═══ PHASE 5.3: CI/CD ═══"
check ".github/workflows/monitoring-ci.yml" "file" "CRITICAL"
check ".github/workflows/pr-validation.yml" "file" "CRITICAL"
check ".pre-commit-config.yaml" "file" "CRITICAL"
check ".codecov.yml" "file" ""
check "scripts/ci/run_ci_locally.sh" "exec" "CRITICAL"
echo ""

echo "═══ PHASE 5.4: DR DRILL ═══"
check "docs/disaster-recovery/dr-drill-plan.md" "file" "CRITICAL"
check "scripts/dr/simulate_dr_drill.sh" "exec" "CRITICAL"
check "tests/dr/test_dr_procedures.py" "file" "CRITICAL"
echo ""

echo "===================================================="
echo "SUMMARY:"
echo "  ✅ Passed:    $PASS"
echo "  ❌ Failed:   $FAIL (critical)"
echo "  ⚠️  Warnings: $WARN (optional)"
echo ""

TOTAL=$((PASS + FAIL + WARN))
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$((PASS * 100 / TOTAL))
    echo "  Success Rate: ${SUCCESS_RATE}%"
fi
echo ""

if [ $FAIL -eq 0 ]; then
    echo "🎉 RESULT: PASS - All critical components present!"
    exit 0
elif [ $FAIL -le 5 ]; then
    echo "⚠️  RESULT:  PARTIAL - $FAIL critical items missing"
    exit 1
else
    echo "❌ RESULT: FAIL - $FAIL critical items missing"
    exit 2
fi
