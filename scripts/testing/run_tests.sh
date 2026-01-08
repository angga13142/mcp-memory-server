#!/bin/bash

echo "🧪 Running MCP Memory Server Test Suite"
echo "========================================"
echo ""

# Determine script location and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_ROOT"
export PYTHONPATH=.

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Run all tests in a SINGLE pytest invocation for maximum efficiency
# This avoids repeated interpreter startup and module loading overhead
echo "📦 Running Unit, Integration, and E2E Tests..."
echo "-----------------------------------------------"

pytest tests/unit/ tests/integration/ tests/e2e/ \
    -v \
    --tb=short \
    --durations=15 \
    --ignore=tests/integration/test_load_testing_integration.py \
    --ignore=tests/integration/test_prometheus_integration.py \
    --ignore=tests/load/ \
    --ignore=tests/dr/ \
    --ignore=tests/ci/ \
    --ignore=tests/alerts/

RESULT=$?

# Coverage Report (separate run to avoid double-counting)
echo ""
echo "📊 GENERATING COVERAGE REPORT"
echo "------------------------------"
pytest tests/unit/ --cov=src --cov-report=term --cov-report=html -q

# Summary
echo ""
echo "========================================"
echo "TEST SUMMARY"
echo "========================================"

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "✅ Feature is ready for deployment"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "⚠️  Please review failures above"
    exit 1
fi
