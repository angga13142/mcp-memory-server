#!/bin/bash
#
# Run CI checks locally before pushing
#

set -e

echo "🚀 Running CI Checks Locally"
echo "============================"
echo ""

FAILED=0

# Code formatting
echo "🎨 Checking code formatting..."
if black --check src/monitoring/ tests/; then
    echo "✅ Black formatting OK"
else
    echo "❌ Black formatting failed"
    echo "Run: black src/monitoring/ tests/"
    ((FAILED++))
fi
echo ""

# Import sorting
echo "📦 Checking import sorting..."
if isort --check-only src/monitoring/ tests/; then
    echo "✅ Import sorting OK"
else
    echo "❌ Import sorting failed"
    echo "Run: isort src/monitoring/ tests/"
    ((FAILED++))
fi
echo ""

# Linting
echo "🔍 Linting code..."
if ruff check src/monitoring/ tests/; then
    echo "✅ Linting OK"
else
    echo "❌ Linting failed"
    ((FAILED++))
fi
echo ""

# Type checking
echo "🔬 Type checking..."
if mypy src/monitoring/ --ignore-missing-imports; then
    echo "✅ Type checking OK"
else
    echo "⚠️ Type checking has issues (not blocking)"
fi
echo ""

# Security scan
echo "🔐 Security scanning..."
if bandit -r src/monitoring/ -ll; then
    echo "✅ Security scan OK"
else
    echo "❌ Security issues found"
    ((FAILED++))
fi
echo ""

# Unit tests
echo "🧪 Running unit tests..."
if pytest tests/unit/ -v --cov=src.monitoring --cov-report=term-missing --cov-fail-under=40; then
    echo "✅ Unit tests OK"
else
    echo "❌ Unit tests failed"
    ((FAILED++))
fi
echo ""

# Documentation validation
echo "📝 Validating documentation..."
if python3 scripts/validate_documentation.py; then
    echo "✅ Documentation OK"
else
    echo "❌ Documentation validation failed"
    ((FAILED++))
fi
echo ""

echo "============================"
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL CI CHECKS PASSED!"
    echo ""
    echo "Ready to push!  🚀"
    exit 0
else
    echo "❌ $FAILED CHECK(S) FAILED"
    echo ""
    echo "Please fix issues before pushing"
    exit 1
fi
