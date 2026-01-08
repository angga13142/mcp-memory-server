#!/bin/bash
#
# Stop Monitoring Stack
#

set -e

echo "🛑 Stopping Monitoring Stack"
echo "============================"
echo "Stopping monitoring stack..."
docker-compose -f deploy/docker-compose.monitoring.yml down

echo ""
echo "✅ Monitoring Stack Stopped"
