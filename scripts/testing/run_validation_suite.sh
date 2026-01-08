#!/bin/bash

echo "🚀 COMPREHENSIVE JOURNAL FEATURE VALIDATION"
echo "============================================================"
echo ""

PASSED=0
FAILED=0

run_test() {
    local test_name=$1
    local test_command=$2
    
    echo "▶ Running $test_name..."
    if eval "$test_command" > /tmp/test_output.log 2>&1; then
        echo "✅ $test_name PASSED"
        ((PASSED++))
    else
        echo "❌ $test_name FAILED"
        ((FAILED++))
        cat /tmp/test_output.log
    fi
    echo ""
}

# Phase 1: Code Structure
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 1: CODE STRUCTURE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f src/models/journal.py ] && [ -f src/services/journal_service.py ] && ls migrations/versions/*journal*.py >/dev/null 2>&1; then
    echo "✅ File Structure Check PASSED"
    ((PASSED++))
else
    echo "❌ File Structure Check FAILED"
    ((FAILED++))
fi
echo ""

# Phase 2: Models
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 2: MODEL VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "Model Validation" "uv run python test_models_validation.py"

# Phase 3: End-to-End
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 3: END-TO-END VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "E2E Validation" "uv run python test_e2e_validation.py"

# Phase 4: MCP Integration
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 4: MCP INTEGRATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "MCP Tools Integration" "uv run python test_integration_flow.py"

# Summary
echo ""
echo "============================================================"
echo "📊 VALIDATION SUMMARY"
echo "============================================================"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 ALL VALIDATIONS PASSED!"
    echo "✅ Feature validated and ready for production"
    exit 0
else
    echo "❌ SOME VALIDATIONS FAILED"
    echo "⚠️  Review failures above"
    exit 1
fi
