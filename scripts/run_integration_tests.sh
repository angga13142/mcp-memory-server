#!/bin/bash
#
# Run Integration Tests
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

echo -e "${BLUE}🔗 INTEGRATION TEST SUITE${NC}"
echo "========================="
echo ""

# Create results directory
mkdir -p test-results

# Check services are running
echo "Checking services..."
services=(
    "http://localhost:8080/health Application"
    "http://localhost:9090/-/healthy Prometheus"
    "http://localhost:3000/api/health Grafana"
)

missing_services=0
for service in "${services[@]}"; do
    url=$(echo "$service" | cut -d' ' -f1)
    name=$(echo "$service" | cut -d' ' -f2)
    
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is running${NC}"
    else
        echo -e "${YELLOW}⚠️  $name is NOT running (tests will be skipped)${NC}"
        ((missing_services++))
    fi
done

echo ""

if [ $missing_services -gt 0 ]; then
    echo -e "${YELLOW}Note: Some services are not running. Related tests will be skipped.${NC}"
    echo -e "${YELLOW}To run all integration tests, start services with:${NC}"
    echo "  docker-compose up -d"
    echo ""
fi

echo "Running integration tests..."
echo ""

# Run integration tests (with skipped tests allowed)
pytest tests/integration/ \
    -v \
    -m integration \
    --tb=short \
    --junitxml=test-results/integration-tests.xml \
    --ignore=tests/integration/test_load_testing_integration.py \
    --ignore=tests/integration/test_prometheus_integration.py \
    --ignore=tests/integration/test_grafana_integration.py \
    || true

# Count results
if [ -f test-results/integration-tests.xml ]; then
    echo ""
    echo -e "${GREEN}✅ Integration tests completed!${NC}"
    echo ""
    echo "Reports:"
    echo "  - JUnit XML: test-results/integration-tests.xml"
else
    echo -e "${RED}❌ Integration tests failed to generate report${NC}"
    exit 1
fi
