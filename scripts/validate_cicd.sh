#!/bin/bash
#
# Automated CI/CD Pipeline Validation
#

set -e

echo "🔍 Validating CI/CD Pipeline"
echo "============================="
echo ""

FAILED=0

# Test 1: Check workflow files exist
echo "Test 1: Workflow Files"
REQUIRED_WORKFLOWS=(
    ".github/workflows/monitoring-ci.yml"
    ".github/workflows/pr-validation.yml"
    ".github/workflows/nightly-build.yml"
)

for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        echo "✅ $workflow exists"
    else
        echo "❌ $workflow missing"
        ((FAILED++))
    fi
done
echo ""

# Test 2: Validate YAML syntax
echo "Test 2: YAML Syntax"
for workflow in .github/workflows/*.yml; do
    if python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null; then
        echo "✅ $(basename $workflow): Valid"
    else
        echo "❌ $(basename $workflow): Invalid"
        ((FAILED++))
    fi
done
echo ""

# Test 3: Check required files
echo "Test 3: Required Configuration Files"
REQUIRED_FILES=(
    ".markdownlint.json"
    ".codecov.yml"
    ".pre-commit-config.yaml"
    "scripts/run_ci_locally.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        ((FAILED++))
    fi
done
echo ""

# Test 4: Check script permissions
echo "Test 4: Script Permissions"
if [ -x "scripts/run_ci_locally.sh" ]; then
    echo "✅ run_ci_locally.sh is executable"
else
    echo "❌ run_ci_locally.sh not executable"
    ((FAILED++))
fi
echo ""

# Test 5: Run local CI
echo "Test 5: Local CI Execution"
# Use a shorter check if possible or run full if user requested
# The logic here assumes run_ci_locally is correct. 
# We'll suppress massive output but show failure
if ./scripts/run_ci_locally.sh > /tmp/ci_output.log 2>&1; then
    echo "✅ Local CI passed"
else
    echo "❌ Local CI failed"
    echo "Check /tmp/ci_output.log for details"
    # Print the last few lines of the log for context
    tail -n 10 /tmp/ci_output.log
    ((FAILED++))
fi
echo ""

# Test 6: Pre-commit hooks
echo "Test 6: Pre-commit Hooks"
if command -v pre-commit &> /dev/null; then
    # Create a temporary config to avoid massive file changes or just check if installed
    # The user logic runs --all-files. This can take time.
    # We will just check if pre-commit can run on a single file or just check version
    if pre-commit run --all-files > /tmp/precommit_output.log 2>&1; then
        echo "✅ Pre-commit hooks pass"
    else
        echo "⚠️  Pre-commit hooks have issues"
        echo "Check /tmp/precommit_output.log"
    fi
else
    echo "⚠️  Pre-commit not installed"
    echo "Install with: pip install pre-commit"
fi
echo ""

# Test 7: GitHub CLI available
echo "Test 7: GitHub CLI"
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI installed"
    
    # Check authentication
    if gh auth status &> /dev/null; then
        echo "✅ GitHub CLI authenticated"
    else
        echo "⚠️  GitHub CLI not authenticated"
        echo "Run: gh auth login"
    fi
else
    echo "⚠️  GitHub CLI not installed"
    echo "Install from: https://cli.github.com/"
fi
echo ""

# Test 8: Check latest workflow runs
echo "Test 8: Recent Workflow Runs"
if command -v gh &> /dev/null && gh auth status &> /dev/null; then
    RECENT_RUNS=$(gh run list --limit 5 --json conclusion --jq '.[].conclusion' 2>/dev/null | grep -c "success" || echo 0)
    
    if [ "$RECENT_RUNS" -gt 0 ]; then
        echo "✅ Recent workflow runs: $RECENT_RUNS successful"
    else
        echo "⚠️  No recent successful runs"
    fi
else
    echo "⚠️  Cannot check workflow runs (GitHub CLI not configured)"
fi
echo ""

echo "============================="

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL VALIDATIONS PASSED"
    exit 0
else
    echo "❌ $FAILED VALIDATIONS FAILED"
    exit 1
fi
