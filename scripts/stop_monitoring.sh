#!/bin/bash
#
# Stop Monitoring Stack
#

set -e

echo "🛑 Stopping Monitoring Stack"
echo "============================"
echo ""

docker-compose -f docker-compose.monitoring.yml down

echo ""
echo "✅ Monitoring Stack Stopped"
