#!/bin/bash
#
# Automated System Metrics Validation
#

set -e

echo "🔍 Validating System Metrics Implementation"
echo "==========================================="
echo ""

FAILED=0

# Test 1: Check metrics endpoint
echo "Test 1: Metrics Endpoint"
if curl -sf http://localhost:8080/metrics | grep -q "mcp_system_memory_usage_bytes"; then
    echo "✅ Memory metric found"
else
    echo "❌ Memory metric not found"
    ((FAILED++))
fi

if curl -sf http://localhost:8080/metrics | grep -q "mcp_system_cpu_usage_percent"; then
    echo "✅ CPU metric found"
else
    echo "❌ CPU metric not found"
    ((FAILED++))
fi

echo ""

# Test 2: Check Prometheus
echo "Test 2: Prometheus Integration"
# We use a timeout to prevent hanging if Prometheus is down
PROM_DATA=$(curl -m 5 -s 'http://localhost:9090/api/v1/query?query=mcp_system_memory_usage_bytes' || echo "{}")
if echo "$PROM_DATA" | jq -e '.data.result[0].value[1]' > /dev/null 2>&1; then
    MEMORY_VALUE=$(echo "$PROM_DATA" | jq -r '.data.result[0].value[1]')
    echo "✅ Prometheus has memory data: $MEMORY_VALUE bytes"
else
    echo "❌ Prometheus has no memory data or is unreachable"
    ((FAILED++))
fi

echo ""

# Test 3: Check alert rules
echo "Test 3: Alert Rules"
ALERT_COUNT=$(curl -m 5 -s http://localhost:9090/api/v1/rules | \
  jq '[.data.groups[] | select(.name=="system_alerts") | .rules[]] | length')

if [ "$ALERT_COUNT" -eq 4 ]; then
    echo "✅ All 4 system alert rules loaded"
else
    echo "❌ Expected 4 alert rules, found $ALERT_COUNT"
    ((FAILED++))
fi

echo ""

# Test 4: Check metric values are realistic
echo "Test 4: Metric Value Validation"
MEMORY_MB=$(curl -s http://localhost:8080/metrics | \
  grep "^mcp_system_memory_usage_bytes" | \
  awk '{print $2}' | \
  awk '{print int($1/1024/1024)}')

if [ "$MEMORY_MB" -gt 10 ] && [ "$MEMORY_MB" -lt 64000 ]; then
    echo "✅ Memory value is realistic: ${MEMORY_MB}MB"
else
    echo "⚠️  Memory value may be incorrect: ${MEMORY_MB}MB"
fi

CPU_PERCENT=$(curl -s http://localhost:8080/metrics | \
  grep "^mcp_system_cpu_usage_percent" | \
  awk '{print $2}')

if (( $(echo "$CPU_PERCENT >= 0 && $CPU_PERCENT <= 100" | bc -l) )); then
    echo "✅ CPU value is valid: ${CPU_PERCENT}%"
else
    echo "❌ CPU value is invalid: ${CPU_PERCENT}%"
    ((FAILED++))
fi

echo ""

# Test 5: Check background collection
echo "Test 5: Background Collection"
echo "Waiting 20 seconds to verify collection..."

BEFORE=$(curl -s 'http://localhost:9090/api/v1/query?query=mcp_system_cpu_usage_percent' | \
  jq -r '.data.result[0].value[0]' || echo "0")

sleep 20

AFTER=$(curl -s 'http://localhost:9090/api/v1/query?query=mcp_system_cpu_usage_percent' | \
  jq -r '.data.result[0].value[0]' || echo "0")

if [ "$AFTER" != "$BEFORE" ] && [ "$AFTER" != "0" ]; then
    echo "✅ Metrics are updating (timestamp changed)"
else
    echo "⚠️  Metrics may not be updating properly"
fi

echo ""
echo "==========================================="

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL VALIDATIONS PASSED"
    exit 0
else
    echo "❌ $FAILED VALIDATIONS FAILED"
    exit 1
fi
