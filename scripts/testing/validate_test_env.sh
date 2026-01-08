#!/bin/bash

# Test Environment Validation Script
# Checks if the testing environment is properly configured

echo "🔍 Validating Test Environment"
echo "=============================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Status counters
# Determine script location and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_ROOT"

CHECKS_PASSED=0
CHECKS_FAILED=0

check_command() {
    local cmd=$1
    local name=$2
    
    if command -v $cmd &> /dev/null; then
        echo -e "${GREEN}✅ $name installed${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $name not found${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_python_module() {
    local module=$1
    local name=$2
    
    if python3 -c "import $module" 2>/dev/null; then
        echo -e "${GREEN}✅ $name installed${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $name not installed${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_file() {
    local file=$1
    local name=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $name exists${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $name not found${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_directory() {
    local dir=$1
    local name=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $name exists${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $name not found${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# Check system dependencies
echo "📦 System Dependencies"
echo "---------------------"
check_command python3 "Python 3"
check_command pip3 "pip3"
echo ""

# Check Python modules
echo "🐍 Python Modules"
echo "-----------------"
check_python_module pytest "pytest"
check_python_module pytest_asyncio "pytest-asyncio"
check_python_module pytest_cov "pytest-cov"
check_python_module sqlalchemy "SQLAlchemy"
check_python_module aiosqlite "aiosqlite"
check_python_module chromadb "ChromaDB"
echo ""

# Check test directories
echo "📂 Test Structure"
echo "-----------------"
check_directory "tests" "tests/"
check_directory "tests/unit" "tests/unit/"
check_directory "tests/integration" "tests/integration/"
check_directory "tests/e2e" "tests/e2e/"
echo ""

# Check test files
echo "📝 Test Files"
echo "-------------"
check_file "tests/unit/test_journal_models.py" "Unit: Models"
check_file "tests/unit/test_journal_repository.py" "Unit: Repository"
check_file "tests/unit/test_journal_service.py" "Unit: Service"
check_file "tests/integration/test_journal_database_integration.py" "Integration: Database"
check_file "tests/integration/test_journal_service_integration.py" "Integration: Service"
check_file "tests/integration/test_mcp_integration.py" "Integration: MCP"
check_file "tests/e2e/test_user_scenarios.py" "E2E: Scenarios"
echo ""

# Check configuration files
echo "⚙️  Configuration"
echo "-----------------"
check_file "pytest.ini" "pytest.ini"
check_file ".coveragerc" ".coveragerc"
check_file "run_tests.sh" "run_tests.sh"

# Check if run_tests.sh is executable
if [ -x "run_tests.sh" ]; then
    echo -e "${GREEN}✅ run_tests.sh is executable${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠️  run_tests.sh not executable (run: chmod +x run_tests.sh)${NC}"
fi
echo ""

# Check source files
echo "📦 Source Code"
echo "--------------"
check_file "src/models/journal.py" "Journal models"
check_file "src/storage/repositories.py" "Repositories"
check_file "src/services/journal_service.py" "Journal service"
check_file "src/server.py" "MCP Server"
echo ""

# Test collection
echo "🧪 Test Collection"
echo "------------------"
if python3 -m pytest --collect-only -q tests/unit/ 2>/dev/null | grep -q "error"; then
    echo -e "${RED}❌ Unit tests have collection errors${NC}"
    ((CHECKS_FAILED++))
else
    UNIT_COUNT=$(python3 -m pytest --collect-only -q tests/unit/ 2>/dev/null | grep -c "test_")
    echo -e "${GREEN}✅ Unit tests collected: $UNIT_COUNT tests${NC}"
    ((CHECKS_PASSED++))
fi

# Summary
echo ""
echo "=============================="
echo "VALIDATION SUMMARY"
echo "=============================="
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Environment is ready for testing!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./run_tests.sh"
    echo "  2. View coverage: open htmlcov/index.html"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  Some checks failed${NC}"
    echo ""
    echo "To fix issues:"
    echo "  1. Install dependencies: pip install -r requirements/requirements.txt -r requirements/requirements-dev.txt"
    echo "  2. Make script executable: chmod +x run_tests.sh"
    echo "  3. Re-run validation: ./validate_test_env.sh"
    echo ""
    exit 1
fi
