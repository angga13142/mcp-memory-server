# Operator Guide - Monitoring & Observability

For system administrators and DevOps engineers deploying and operating the monitoring stack.

## Installation

1. Clone and enter repo:

```bash
git clone https://github.com/your-org/mcp-memory-server.git
cd mcp-memory-server
```

2. Configure environment (`.env`):

- GRAFANA_PASSWORD
- SLACK_WEBHOOK_URL
- REDIS_PASSWORD (if used)

3. Prepare host dirs (example):

```bash
sudo mkdir -p /var/mcp-data /var/mcp-logs /var/mcp-redis
sudo chown -R $USER:$USER /var/mcp-data /var/mcp-logs /var/mcp-redis
```

4. Deploy:

```bash
docker-compose up -d
docker-compose -f docker-compose.monitoring.yml up -d
docker-compose ps
```

5. Verify:

```bash
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
curl -s http://localhost:3000/api/health | jq .
curl http://localhost:8080/metrics | head -20
```

## Configuration

- Prometheus: monitoring/prometheus.yml (scrape intervals, targets)
- Grafana: monitoring/grafana/datasources and dashboards
- Alertmanager: monitoring/alertmanager/config.yml (routes, receivers)
- Alerts: monitoring/alerts/\*.yml

Reload Prometheus without restart:

```bash
curl -X POST http://localhost:9090/-/reload
```

Reset Grafana admin password:

```bash
docker-compose exec grafana grafana-cli admin reset-admin-password newpassword
```

Import Grafana datasource via API:

```bash
curl -X POST http://admin:admin@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{"name":"Prometheus","type":"prometheus","url":"http://prometheus:9090","access":"proxy","isDefault":true}'
```

## Operations

Daily checklist (sample):

- `docker-compose ps` (healthy containers)
- Prometheus targets: `curl -s http://localhost:9090/api/v1/targets`
- Active alerts: `curl -s http://localhost:9090/api/v1/alerts`
- Disk usage: `df -h /var/mcp-data /var/mcp-logs`
- Recent errors: `docker-compose logs --tail=100 mcp-memory-server | grep -i error | tail -5`

Resource checks:

- Container usage: `docker stats --no-stream`
- Prometheus storage: `du -sh /var/mcp-data/prometheus`
- Log sizes: `du -sh /var/mcp-logs/*`

Backups (example Prometheus snapshot):

```bash
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
SNAP=$(curl -s http://localhost:9090/api/v1/admin/tsdb/snapshot | jq -r '.data.name')
docker cp prometheus:/prometheus/snapshots/$SNAP /var/backups/mcp-prometheus/snapshot_$(date +%Y%m%d_%H%M%S)
```

## Upgrades

1. Backup data (Prometheus snapshots, Grafana dashboards, Alertmanager config).
2. Pull images: `docker-compose -f docker-compose.monitoring.yml pull`
3. Restart stack: `docker-compose -f docker-compose.monitoring.yml up -d --force-recreate`
4. Verify health (Prometheus targets, Grafana API, metrics endpoint).
5. Rollback: redeploy previous images and restore backups if needed.

## Incident Response

- Service down: check `docker-compose ps`, inspect logs, restart service, verify `/health`.
- High memory: `docker stats`, inspect top memory processes inside container, check vector store size, restart with limits if necessary.
- Prometheus disk full: inspect `df -h`, reduce retention or remove old TSDB blocks, adjust retention flag/config.

## Capacity Planning (guidelines)

- Prometheus storage: ~500MB/day; plan 30d -> ~15GB. Increase retention or volume as needed.
- Grafana DB: ~100MB typical; consider pruning annotations/dashboards monthly.
- Logs: ~50MB/day typical; rotate at filesystem or docker level.

## Reference Commands

Prometheus:

- Config: `curl http://localhost:9090/api/v1/status/config`
- TSDB stats: `curl http://localhost:9090/api/v1/status/tsdb`

Grafana:

- List plugins: `docker-compose exec grafana grafana-cli plugins ls`
- Reset admin password: `docker-compose exec grafana grafana-cli admin reset-admin-password <new>`

Alertmanager:

- Active alerts: `curl http://localhost:9093/api/v1/alerts`
- Silences: `curl http://localhost:9093/api/v1/silences`
