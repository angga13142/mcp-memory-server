#!/bin/bash

echo "🧪 Running Monitoring & Observability Tests"
echo "============================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

run_test_suite() {
    local name=$1
    local command=$2
    
    echo "Running $name..."
    if eval "$command"; then
        echo -e "${GREEN}✅ $name PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $name FAILED${NC}"
        ((FAILED++))
    fi
    echo ""
}

echo "📦 Ensuring monitoring stack is running..."
docker-compose -f docker-compose.monitoring.yml up -d 2>/dev/null || docker-compose up -d
sleep 10

echo "🔬 UNIT TESTS"
echo "-------------"
run_test_suite "Metrics Unit Tests" "pytest tests/unit/test_metrics.py -v"
run_test_suite "Logging Unit Tests" "pytest tests/unit/test_logging.py -v"

echo "🔗 INTEGRATION TESTS"
echo "--------------------"
run_test_suite "Prometheus Integration" "pytest tests/integration/test_prometheus_integration.py -v -s"
run_test_suite "Grafana Integration" "pytest tests/integration/test_grafana_integration.py -v -s"

echo "⚡ PERFORMANCE TESTS"
echo "--------------------"
run_test_suite "Metrics Performance" "pytest tests/load/test_metrics_performance.py -v -s"

echo "🚨 ALERT TESTS (Quick)"
echo "----------------------"
run_test_suite "Alert Configuration" "pytest tests/alerts/test_alert_scenarios.py -v -s -m 'not slow'"

echo "📊 GENERATING COVERAGE REPORT"
echo "------------------------------"
pytest tests/unit/ tests/integration/ \
    --cov=src.utils.metrics \
    --cov=src.utils.structured_logging \
    --cov-report=html \
    --cov-report=term

echo ""
echo "============================================"
echo "TEST SUMMARY"
echo "============================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "✅ Monitoring system tested and ready"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "⚠️  Please review failures above"
    exit 1
fi
