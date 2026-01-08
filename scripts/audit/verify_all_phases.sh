#!/bin/bash
#
# Comprehensive Verification of All Phases
#

# NOT using set -e to allow gathering all failures
# set -e

echo "🔍 COMPREHENSIVE PHASE VERIFICATION"
echo "===================================="
echo ""

TOTAL_PASS=0
TOTAL_FAIL=0

check() {
    if $1; then
        echo "✅ $2"
        TOTAL_PASS=$((TOTAL_PASS + 1))
    else
        echo "❌ $2"
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
    fi
}

# Phase 3: Monitoring & Observability
echo "PHASE 3: Monitoring & Observability"
echo "-----------------------------------"
check "test -f src/monitoring/metrics/system_metrics.py" "System metrics"
check "test -f monitoring/prometheus.yml" "Prometheus config"
check "test -f monitoring/alerts/journal_alerts.yml" "Alert rules"
echo ""

# Phase 4: Backup & Recovery
echo "PHASE 4: Backup & Recovery"
echo "--------------------------"
check "test -x scripts/backup_prometheus_advanced.sh" "Prometheus backup"
check "test -x scripts/restore_prometheus.sh" "Prometheus restore"
check "test -x scripts/verify_recovery.sh" "Recovery verification"
echo ""

# Phase 5.1: System Metrics
echo "PHASE 5.1: System Metrics"
echo "-------------------------"
check "test -f src/monitoring/collectors.py" "Collectors"
check "test -f tests/unit/test_system_metrics.py" "Tests"
echo ""

# Phase 5.2: Load Testing
echo "PHASE 5.2: Load Testing"
echo "-----------------------"
check "test -f tests/load/test_metrics_performance.py" "Load tests"
check "test -x scripts/run_load_tests.sh" "Test runner"
echo ""

# Phase 5.3: CI/CD
echo "PHASE 5.3: CI/CD Pipeline"
echo "-------------------------"
check "test -f .github/workflows/monitoring-ci.yml" "CI workflow"
check "test -f .pre-commit-config.yaml" "Pre-commit"
echo ""

# Phase 5.4: DR Drill
echo "PHASE 5.4: DR Drill"
echo "-------------------"
check "test -f docs/disaster-recovery/dr-drill-plan.md" "DR plan"
check "test -x scripts/simulate_dr_drill.sh" "Simulation"
echo ""

echo "===================================="
echo "TOTAL: $TOTAL_PASS passed, $TOTAL_FAIL failed"
echo ""

if [ $TOTAL_FAIL -eq 0 ]; then
    echo "🎉 ALL PHASES VERIFIED!"
    exit 0
else
    echo "⚠️ Some components missing"
    exit 1
fi
