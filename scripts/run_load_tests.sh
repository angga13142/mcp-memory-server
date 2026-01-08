#!/bin/bash
set -e
echo "🔥 Running Load Tests..."
# Ensure we are in project root and PYTHONPATH includes src
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/load/test_metrics_performance.py -v -m load --tb=short
