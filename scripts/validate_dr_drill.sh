#!/bin/bash
#
# Automated DR Drill Validation
#

set -e

echo "🔍 Validating DR Drill Results"
echo "=============================="
echo ""

FAILED=0

# Test 1: Check drill completion
echo "Test 1: Drill Completion"
if [ -f "drill_log.txt" ]; then
    if grep -q "Phase 4.3 Complete" drill_log.txt; then
        echo "✅ Drill completed all phases"
    else
        echo "❌ Drill incomplete"
        ((FAILED++))
    fi
else
    echo "❌ Drill log not found"
    ((FAILED++))
fi
echo ""

# Test 2: Check RTO
echo "Test 2: RTO Validation"
if [ -f "drill_log.txt" ]; then
    START=$(grep "Phase 1.1 Start:" drill_log.txt | head -1 | awk '{print $4}')
    END=$(grep "Phase 4.3 Complete:" drill_log.txt | tail -1 | awk '{print $4}')
    
    # Calculate duration (manual or script)
    echo "Start: $START"
    echo "End: $END"
    echo "⚠️ Manual RTO calculation required"
    echo "Target: <4 hours"
fi
echo ""

# Test 3: Check services
echo "Test 3: Service Health"
if [ -n "$PUBLIC_IP" ]; then
    if curl -sf http://$PUBLIC_IP:8080/health > /dev/null; then
        echo "✅ Application healthy"
    else
        echo "❌ Application unhealthy"
        ((FAILED++))
    fi
    
    if curl -sf http://$PUBLIC_IP:9090/-/healthy > /dev/null; then
        echo "✅ Prometheus healthy"
    else
        echo "❌ Prometheus unhealthy"
        ((FAILED++))
    fi
else
    echo "⚠️ PUBLIC_IP not set, skipping service checks"
fi
echo ""

# Test 4: Check data restoration
echo "Test 4: Data Validation"
if [ -n "$PUBLIC_IP" ]; then
    DATA_POINTS=$(curl -s "http://$PUBLIC_IP:9090/api/v1/query?query=up" | \
        jq '.data.result | length' 2>/dev/null || echo 0)
    
    if [ "$DATA_POINTS" -gt 0 ]; then
        echo "✅ Prometheus has data: $DATA_POINTS time series"
    else
        echo "❌ Prometheus has no data"
        ((FAILED++))
    fi
fi
echo ""

# Test 5: Check documentation
echo "Test 5: Documentation"
REQUIRED_FILES=(
    "drill_log.txt"
    "verification_results.txt"
    "instance_info.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file present"
    else
        echo "❌ $file missing"
        ((FAILED++))
    fi
done
echo ""

echo "=============================="

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL VALIDATIONS PASSED"
    exit 0
else
    echo "❌ $FAILED VALIDATIONS FAILED"
    exit 1
fi
