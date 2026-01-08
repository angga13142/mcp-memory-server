#!/bin/bash
#
# Continuous load test - runs indefinitely for stress testing
#

echo "🔥 CONTINUOUS LOAD TEST"
echo "======================="
echo "Press Ctrl+C to stop"
echo ""

ITERATION=1

while true; do
    echo "Iteration $ITERATION - $(date)"
    
    # Run quick load test
    pytest tests/load/test_metrics_performance.py::TestMetricsEndpointLoad::test_metrics_endpoint_concurrent_requests \
        -v \
        --tb=line \
        -q
    
    if [ $? -ne 0 ]; then
        echo "❌ Load test failed at iteration $ITERATION"
        exit 1
    fi
    
    echo "✅ Iteration $ITERATION passed"
    echo ""
    
    ((ITERATION++))
    sleep 30
done
