#!/bin/bash
#
# Run Complete Test Suite
# =======================
# Comprehensive test runner with coverage reporting
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COVERAGE_THRESHOLD=85
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="${PROJECT_ROOT}"

echo -e "${BLUE}🧪 COMPREHENSIVE TEST SUITE${NC}"
echo "============================"
echo ""
echo "Project Root: $PROJECT_ROOT"
echo "Coverage Threshold: ${COVERAGE_THRESHOLD}%"
echo ""

# Create test results directory
mkdir -p test-results

# Function to run test suite
run_tests() {
    local name=$1
    local path=$2
    local extra_args=$3

    echo -e "${YELLOW}▶ Running ${name}...${NC}"
    
    if pytest "$path" -v \
        --tb=short \
        --junitxml="test-results/${name// /_}.xml" \
        $extra_args; then
        echo -e "${GREEN}✓ ${name} PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ ${name} FAILED${NC}"
        return 1
    fi
}

# Track results
FAILED=0

# 1. Unit Tests with Coverage
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}📦 PHASE 1: UNIT TESTS${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

if ! pytest tests/unit/ -v \
    --tb=short \
    --cov=src \
    --cov-report=term \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --junitxml=test-results/unit-tests.xml; then
    ((FAILED++))
fi

# 2. Integration Tests
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}🔗 PHASE 2: INTEGRATION TESTS${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

if ! pytest tests/integration/ -v \
    --tb=short \
    --junitxml=test-results/integration-tests.xml \
    --ignore=tests/integration/test_load_testing_integration.py \
    --ignore=tests/integration/test_prometheus_integration.py \
    --ignore=tests/integration/test_grafana_integration.py \
    --ignore=tests/integration/api/; then
    ((FAILED++))
fi

# 3. E2E Tests
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}🎬 PHASE 3: END-TO-END TESTS${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

if ! pytest tests/e2e/ -v \
    --tb=short \
    --junitxml=test-results/e2e-tests.xml; then
    ((FAILED++))
fi

# 4. CI/DR Tests
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}🔧 PHASE 4: CI/DR TESTS${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

if ! pytest tests/ci/ tests/dr/ -v \
    --tb=short \
    --junitxml=test-results/ci-dr-tests.xml; then
    ((FAILED++))
fi

# Coverage validation
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}📊 COVERAGE REPORT${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

# Show coverage summary
coverage report

# Check coverage threshold
if coverage report --fail-under=${COVERAGE_THRESHOLD}; then
    echo -e "${GREEN}✓ Coverage meets threshold (>=${COVERAGE_THRESHOLD}%)${NC}"
else
    echo -e "${RED}✗ Coverage below threshold (<${COVERAGE_THRESHOLD}%)${NC}"
    ((FAILED++))
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}📋 TEST SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

echo "Reports generated:"
echo "  - Coverage HTML: htmlcov/index.html"
echo "  - Coverage XML:  coverage.xml"
echo "  - JUnit Reports: test-results/*.xml"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}══════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 ALL TEST PHASES PASSED!${NC}"
    echo -e "${GREEN}══════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}══════════════════════════════════════${NC}"
    echo -e "${RED}❌ ${FAILED} TEST PHASE(S) FAILED${NC}"
    echo -e "${RED}══════════════════════════════════════${NC}"
    exit 1
fi
