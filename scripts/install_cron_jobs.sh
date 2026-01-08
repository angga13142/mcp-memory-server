#!/bin/bash
#
# Install Backup Cron Jobs
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing backup cron jobs..."

# Create cron file
cat > /tmp/mcp-backups.cron <<EOF
# MCP Memory Server Backup Jobs

# Prometheus backup - every hour at 5 minutes past
5 * * * * root ${PROJECT_DIR}/scripts/backup_prometheus_advanced.sh >> /var/log/mcp-backups/cron.log 2>&1

# Grafana backup - daily at 3 AM
0 3 * * * root ${PROJECT_DIR}/scripts/backup_grafana_advanced.sh >> /var/log/mcp-backups/cron.log 2>&1

# Application backup - every hour at 10 minutes past
10 * * * * root ${PROJECT_DIR}/scripts/backup_application.sh >> /var/log/mcp-backups/cron.log 2>&1

# Backup health check - every 4 hours
0 */4 * * * root ${PROJECT_DIR}/scripts/check_backup_health.sh >> /var/log/mcp-backups/cron.log 2>&1
EOF

# Install cron file
sudo cp /tmp/mcp-backups.cron /etc/cron.d/mcp-backups
sudo chmod 644 /etc/cron.d/mcp-backups

# Create log directory
sudo mkdir -p /var/log/mcp-backups
sudo chmod 755 /var/log/mcp-backups

echo "✅ Cron jobs installed"
echo ""
echo "Backup schedule:"
echo "  Prometheus:   Hourly (xx:05)"
echo "  Grafana:      Daily (03:00)"
echo "  Application:  Hourly (xx:10)"
echo "  Health Check: Every 4 hours"
echo ""
echo "Logs: /var/log/mcp-backups/cron.log"
