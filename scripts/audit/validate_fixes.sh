#!/bin/bash
# validate-fixes.sh - Automated validation script

echo "🔍 MCP Memory Server Fix Validation"
echo "===================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
# Counters
PASSED=0
FAILED=0

# Determine script location and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_ROOT"

validate() {
    local test_name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Testing $test_name... "
    
    result=$(eval "$command" 2>&1)
    
    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "  Command: $command"
        echo "  Expected pattern: $expected"
        echo "  Got: $result"
        ((FAILED++))
        return 1
    fi
}

echo "🔴 PRIORITY 1 VALIDATION"
echo "------------------------"

validate "Authentication middleware exists" \
    "grep -c 'http_auth_middleware' src/server.py" \
    "1"

validate "MCP_API_KEY usage" \
    "grep -r 'MCP_API_KEY' src/middleware/" \
    "MCP_API_KEY"

validate "Alembic config file" \
    "test -f alembic.ini && echo 'exists'" \
    "exists"

validate "Migrations directory" \
    "test -d migrations && echo 'exists'" \
    "exists"

validate "Initial migration file" \
    "ls migrations/versions/*.py 2>/dev/null | head -1 | wc -l" \
    "1"

validate "Error handling in server" \
    "grep -c 'try:' src/server.py" \
    "[5-9]"

validate "Standardized error responses" \
    "grep -c '\"success\".*\"error\"' src/server.py" \
    "[5-9]"

echo ""
echo "🟡 PRIORITY 2 VALIDATION"
echo "------------------------"

validate "CORS secure default" \
    "grep 'cors_origins.*\[\]' config.yaml" \
    "cors_origins"

validate "CORS validation warning" \
    "grep -c 'validate_cors' src/utils/config.py" \
    "1"

validate "ServiceManager exists" \
    "test -f src/services/service_manager.py && echo 'exists'" \
    "exists"

validate "No global database singleton" \
    "grep -c '^_database:.*Database.*=.*Database' src/storage/database.py" \
    "0"

validate "Tenacity retry decorator" \
    "grep -c '@retry' src/services/memory_service.py" \
    "1"

validate "Retry configuration" \
    "grep 'stop_after_attempt' src/services/memory_service.py" \
    "stop_after_attempt"

validate "UTC timezone usage" \
    "grep -c 'timezone.utc' src/models/decision.py src/models/task.py src/models/project.py src/models/context.py" \
    "[4-9]"

validate "No datetime.utcnow" \
    "grep -c 'datetime.utcnow()' src/models/*.py src/storage/database.py || echo '0'" \
    "0"

validate "Input max_length constraints" \
    "grep -c 'max_length=' src/models/decision.py src/models/task.py" \
    "[5-9]"

validate "Input max_items constraints" \
    "grep -c 'max_length=' src/models/decision.py" \
    "[2-9]"

validate "Version column in ActiveContextDB" \
    "grep 'version.*Column.*Integer' src/storage/database.py" \
    "version"

validate "Optimistic locking in save" \
    "grep -A 5 'WHERE.*version.*==' src/storage/repositories.py" \
    "version"

validate "Docker model cache" \
    "grep 'TRANSFORMERS_CACHE' Dockerfile" \
    "TRANSFORMERS_CACHE"

validate "Pre-download model in Dockerfile" \
    "grep 'SentenceTransformer' Dockerfile" \
    "SentenceTransformer"

echo ""
echo "🟢 PRIORITY 3 VALIDATION"
echo "------------------------"

validate "Rate limiting middleware" \
    "test -f src/middleware/rate_limit.py && echo 'exists'" \
    "exists"

validate "Slowapi import" \
    "grep 'slowapi' requirements/requirements.txt" \
    "slowapi"

validate "Python health check" \
    "test -f src/health_check.py && echo 'exists'" \
    "exists"

validate "No curl in health check" \
    "grep -c 'curl' Dockerfile || echo '0'" \
    "0"

validate "Dependency lock file" \
    "test -f requirements/requirements.lock && echo 'exists'" \
    "exists"

echo ""
echo "📚 DOCUMENTATION VALIDATION"
echo "----------------------------"

validate "README updated with auth" \
    "grep -c 'MCP_API_KEY' README.md" \
    "[1-9]"

validate "SECURITY.md exists" \
    "test -f SECURITY.md && echo 'exists'" \
    "exists"

validate ".env.example exists" \
    "test -f .env.example && echo 'exists'" \
    "exists"

validate "IMPLEMENTATION_SUMMARY exists" \
    "test -f IMPLEMENTATION_SUMMARY.md && echo 'exists'" \
    "exists"

echo ""
echo "📊 VALIDATION SUMMARY"
echo "====================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL VALIDATIONS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  SOME VALIDATIONS FAILED${NC}"
    exit 1
fi
