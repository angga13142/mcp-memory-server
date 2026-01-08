# Monitoring Stack for MCP Memory Server

## Quick Start

```bash
# Start main services first
docker-compose up -d

# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
# Alertmanager: http://localhost:9093
```

## Components

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **Alertmanager** - Alert management and routing
- **Node Exporter** - System metrics
- **cAdvisor** - Container metrics

## Configuration

### Prometheus

- Config: `monitoring/prometheus.yml`
- Alerts: `monitoring/alerts/*.yml`
- Port: 9090

### Grafana

- Datasources: `monitoring/grafana/datasources/`
- Dashboards: `monitoring/grafana/dashboards/`
- Port: 3000
- Default credentials: admin/admin

### Alertmanager

- Config: `monitoring/alertmanager/config.yml`
- Port: 9093
- Configure Slack webhook in `.env`: `SLACK_WEBHOOK_URL`

## Metrics Endpoints

- MCP Server: http://localhost:8080/metrics
- Prometheus: http://localhost:9090/metrics
- Node Exporter: http://localhost:9100/metrics
- cAdvisor: http://localhost:8081/metrics

## Alerts

Configured alerts:

- High session failure rate
- Reflection generation failures
- Slow reflection generation
- Too many active sessions
- Slow database queries
- Vector store embedding failures
- High memory usage
- Service down

## Troubleshooting

### Prometheus not scraping targets

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check MCP server metrics endpoint
curl http://localhost:8080/metrics
```

### Grafana cannot connect to Prometheus

```bash
# Verify network
docker network inspect mcp-network

# Check Prometheus is running
docker ps | grep prometheus
```

### Alerts not firing

```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules

# Check alertmanager
curl http://localhost:9093/api/v2/status
```
