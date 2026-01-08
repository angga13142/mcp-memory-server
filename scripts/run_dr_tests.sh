#!/bin/bash
#
# Run DR drill tests
#

set -e

echo "🧪 Running DR Drill Tests"
echo "========================="
echo ""

# Create tests/dr directory if it doesn't exist
mkdir -p tests/dr

# Unit tests
echo "Running DR procedure tests..."
pytest tests/dr/test_dr_procedures.py -v

echo ""

# Run simulation test
echo "Running DR simulation..."
pytest tests/dr/test_dr_procedures.py::TestDRSimulation::test_simulation_script_runs -v -s

echo ""
echo "========================="
echo "✅ All DR tests passed!"
