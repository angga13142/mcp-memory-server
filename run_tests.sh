#!/bin/bash

echo "🧪 Running MCP Memory Server Test Suite"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
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

# Unit Tests
echo "📦 UNIT TESTS"
echo "-------------"
run_test_suite "Model Tests" "pytest tests/unit/test_journal_models.py -v"
run_test_suite "Repository Tests" "pytest tests/unit/test_journal_repository.py -v"
run_test_suite "Service Tests" "pytest tests/unit/test_journal_service.py -v"

# Integration Tests
echo "🔗 INTEGRATION TESTS"
echo "--------------------"
run_test_suite "Database Integration" "pytest tests/integration/test_journal_database_integration.py -v"
run_test_suite "Service Integration" "pytest tests/integration/test_journal_service_integration.py -v"
run_test_suite "MCP Integration" "pytest tests/integration/test_mcp_integration.py -v"

# E2E Tests
echo "🎬 END-TO-END TESTS"
echo "-------------------"
run_test_suite "User Scenarios" "pytest tests/e2e/test_user_scenarios.py -v -s"

# Coverage Report
echo "📊 GENERATING COVERAGE REPORT"
echo "------------------------------"
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Summary
echo ""
echo "========================================"
echo "TEST SUMMARY"
echo "========================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "✅ Feature is ready for deployment"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "⚠️  Please review failures above"
    exit 1
fi
