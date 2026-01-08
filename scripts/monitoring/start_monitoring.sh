#!/bin/bash
#
# Start Monitoring Stack
#

set -e

echo "🚀 Starting Monitoring Stack"
echo "============================"
echo ""

# Check if monitoring network exists
if ! docker network inspect mcp-memory-server_monitoring >/dev/null 2>&1; then
    echo "Creating monitoring network..."
    docker network create mcp-memory-server_monitoring
fi

# Start monitoring services
echo "Starting Prometheus, Grafana, and Alertmanager..."
docker-compose -f deploy/docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to start..."
sleep 10

# Check Prometheus
echo -n "Checking Prometheus... "
if curl -sf http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Check Grafana
echo -n "Checking Grafana... "
if curl -sf http://localhost:3000/api/health > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Check Alertmanager
echo -n "Checking Alertmanager... "
if curl -sf http://localhost:9093/-/healthy > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

echo ""
echo "============================"
echo "✅ Monitoring Stack Started"
echo ""
echo "Access URLs:"
echo "  Prometheus:     http://localhost:9090"
echo "  Grafana:       http://localhost:3000 (admin/admin)"
echo "  Alertmanager:  http://localhost:9093"
echo ""
echo "To view logs:"
echo "  docker-compose -f deploy/docker-compose.monitoring.yml logs -f"
echo ""
