#!/bin/bash
#
# Run tests for CI/CD configuration
#

set -e

echo "🧪 Testing CI/CD Configuration"
echo "==============================="
echo ""

# Unit tests for workflows
echo "Running workflow configuration tests..."
pytest tests/ci/test_workflows.py -v

echo ""

# Integration tests
echo "Running CI integration tests..."
pytest tests/ci/test_ci_integration.py -v

echo ""

# Validate workflows
echo "Validating CI/CD setup..."
./scripts/validate_cicd.sh

echo ""
echo "==============================="
echo "✅ All CI/CD tests passed!"
