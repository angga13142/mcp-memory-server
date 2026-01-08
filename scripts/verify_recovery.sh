#!/bin/bash
# Post-recovery verification

set -euo pipefail

FAILED=0

echo "🔍 Post-Recovery Verification"
echo "============================="

test_service() {
  local name=$1 url=$2
  if curl -sf "$url" >/dev/null 2>&1; then
    echo "✅ $name healthy"
  else
    echo "❌ $name NOT healthy"
    ((FAILED++))
  fi
}

test_service "MCP Memory Server" "http://localhost:8080/health"
test_service "Prometheus" "http://localhost:9090/-/healthy"
test_service "Grafana" "http://localhost:3000/api/health"
test_service "Alertmanager" "http://localhost:9093/-/healthy"

echo ""
echo "Test 2: Metrics collection"
METRIC_COUNT=$(curl -s http://localhost:8080/metrics | grep -c '^mcp_' || echo 0)
if [ "$METRIC_COUNT" -gt 50 ]; then
  echo "✅ Metrics present: $METRIC_COUNT"
else
  echo "❌ Metrics low: $METRIC_COUNT"
  ((FAILED++))
fi

echo ""
echo "Test 3: Prometheus data"
TS_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result | length' 2>/dev/null || echo 0)
if [ "$TS_COUNT" -gt 0 ]; then
  echo "✅ Prometheus has data: $TS_COUNT"
else
  echo "❌ Prometheus has no data"
  ((FAILED++))
fi

echo ""
echo "Test 4: Grafana dashboards"
DASH_COUNT=$(curl -s -u admin:${GRAFANA_PASSWORD:-admin} http://localhost:3000/api/search 2>/dev/null | jq '. | length' 2>/dev/null || echo 0)
if [ "$DASH_COUNT" -gt 0 ]; then
  echo "✅ Grafana dashboards: $DASH_COUNT"
else
  echo "❌ No Grafana dashboards found"
  ((FAILED++))
fi

echo ""
echo "Test 5: Application DB"
if docker exec mcp-memory-server sqlite3 /app/data/memory.db "PRAGMA integrity_check;" | grep -q "ok"; then
  echo "✅ DB integrity OK"
else
  echo "❌ DB integrity failed"
  ((FAILED++))
fi
TABLE_COUNT=$(docker exec mcp-memory-server sqlite3 /app/data/memory.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo 0)
echo "Tables: $TABLE_COUNT"

echo ""
echo "Test 6: Alert rules"
RULES=$(curl -s http://localhost:9090/api/v1/rules | jq '.data.groups | map(.rules | length) | add' 2>/dev/null || echo 0)
if [ "$RULES" -gt 0 ]; then
  echo "✅ Alert rules loaded: $RULES"
else
  echo "❌ No alert rules loaded"
  ((FAILED++))
fi

echo ""
echo "============================="
if [ $FAILED -eq 0 ]; then
  echo "✅ ALL CHECKS PASSED"
  exit 0
else
  echo "❌ $FAILED CHECK(S) FAILED"
  exit 1
fi
