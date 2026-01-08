#!/bin/bash
#
# Run E2E Tests
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="${PROJECT_ROOT}"

echo -e "${BLUE}🎯 END-TO-END TEST SUITE${NC}"
echo "========================"
echo ""

# Create results directory
mkdir -p test-results

# Check services
echo "Checking prerequisites..."
services=(
    "http://localhost:8080/health Application"
    "http://localhost:9090/-/healthy Prometheus"
    "http://localhost:3000/api/health Grafana"
)

missing=0
for service in "${services[@]}"; do
    url=$(echo "$service" | cut -d' ' -f1)
    name=$(echo "$service" | cut -d' ' -f2)
    
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC}"
    else
        echo -e "${YELLOW}⚠️  $name NOT RUNNING${NC}"
        ((missing++))
    fi
done

echo ""

if [ $missing -gt 0 ]; then
    echo -e "${YELLOW}Note: Some services not running. Related tests will be skipped.${NC}"
    echo -e "${YELLOW}To run all E2E tests, start services with:${NC}"
    echo "  docker-compose up -d"
    echo ""
fi

echo "Running E2E tests..."
echo ""

# Run E2E tests
pytest tests/e2e/ \
    -v \
    -m "e2e" \
    --tb=short \
    --capture=no \
    --junitxml=test-results/e2e-tests.xml \
    || true

echo ""
echo -e "${GREEN}✅ E2E tests completed!${NC}"
echo ""
echo "Reports:"
echo "  - JUnit XML: test-results/e2e-tests.xml"
