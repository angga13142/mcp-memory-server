#!/bin/bash

set -euo pipefail

echo "🧹 Cleaning up Monitoring & Observability Code"
echo "=============================================="
echo ""

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

# Step 1: Reorganize files
echo "📁 Step 1: Ensuring directory structure..."
mkdir -p src/monitoring/{metrics,logging,health,security}
echo "✅ Directories ensured"

# Step 2: Run auto-formatters
if command -v black >/dev/null 2>&1; then
  echo "🎨 Step 2: Running code formatters..."
  black src/monitoring/
  echo "✅ Code formatted"
else
  echo "⚠️  Black not installed; skipping formatting"
fi

# Step 3: Type checking
if command -v mypy >/dev/null 2>&1; then
  echo "🔍 Step 3: Running type checker..."
  mypy src/monitoring/ --install-types --non-interactive || echo "⚠️  Type errors found (review manually)"
else
  echo "⚠️  mypy not installed; skipping type check"
fi

# Step 4: Linting
if command -v ruff >/dev/null 2>&1; then
  echo "🔎 Step 4: Running linter..."
  ruff check src/monitoring/ --fix || echo "⚠️  Lint errors found (review manually)"
else
  echo "⚠️  Ruff not installed; skipping lint"
fi

# Step 5: Security check
if command -v bandit >/dev/null 2>&1; then
  echo "🔒 Step 5: Running security check..."
  bandit -r src/monitoring/ -f json -o bandit-report.json || echo "⚠️  Security issues found (review manually)"
else
  echo "⚠️  Bandit not installed; skipping security scan"
fi

# Step 6: Remove unused imports
if command -v autoflake >/dev/null 2>&1; then
  echo "🗑️  Step 6: Removing unused imports..."
  autoflake --remove-all-unused-imports --in-place --recursive src/monitoring/
  echo "✅ Unused imports removed"
else
  echo "⚠️  autoflake not installed; skipping unused import cleanup"
fi

# Step 7: Run tests
if command -v pytest >/dev/null 2>&1; then
  echo "🧪 Step 7: Running tests..."
  PYTHONPATH=. pytest tests/unit/test_metrics.py tests/unit/test_logging.py -v || echo "⚠️  Tests failed (review manually)"
else
  echo "⚠️  pytest not installed; skipping tests"
fi

echo ""
echo "=============================================="
echo "✅ CLEANUP COMPLETE!"
echo "=============================================="
echo ""
echo "📝 Next steps:"
echo "   1. Review type errors in mypy output"
echo "   2. Review lint errors in ruff output"
echo "   3. Review security issues in bandit-report.json"
echo "   4. Commit changes"
