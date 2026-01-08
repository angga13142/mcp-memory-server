# DR Drill Execution Plan

## Team Roles

| Role | Responsibility |
|------|----------------|
| Drill Commander | Overall coordination, timing, and escalation |
| Infrastructure Lead | AWS resources, networking, compute |
| Application Lead | Deployment, configuration, service health |
| Data Lead | Backup restoration, data validation |
| Observer | Documentation, timing, issue tracking |

---

## Phase 0: Pre-Drill Preparation (30 min)
- [ ] Verify backup availability in S3
- [ ] Confirm team availability
- [ ] Prepare communication channels
- [ ] Review runbook

```bash
# Check backup status
aws s3 ls s3://mcp-backups/latest/ --recursive
```

## Phase 1: Infrastructure (60 min)
- [ ] Provision AWS EC2 instance
- [ ] Install dependencies
- [ ] Configure directories

```bash
# Launch instance
aws ec2 run-instances --image-id ami-xxx --instance-type t3.medium

# Install Docker
sudo apt-get update && sudo apt-get install -y docker.io docker-compose
```

## Phase 2: Deployment (45 min)
- [ ] Clone repository
- [ ] Configure environment
- [ ] Pull Docker images

```bash
# Clone and setup
git clone https://github.com/angga13142/mcp-memory-server.git
cd mcp-memory-server
cp .env.example .env
docker-compose pull
```

## Phase 3: Data Recovery (90 min)
- [ ] Download backups from S3
- [ ] Restore Prometheus
- [ ] Restore Grafana
- [ ] Restore Application

```bash
# Download backups
aws s3 cp s3://mcp-backups/latest/prometheus.tar.gz .
aws s3 cp s3://mcp-backups/latest/grafana.tar.gz .

# Restore
tar xzf prometheus.tar.gz -C /var/lib/prometheus
tar xzf grafana.tar.gz -C /var/lib/grafana
```

## Phase 4: Verification (30 min)
- [ ] Run verify_recovery.sh
- [ ] Manual checks
- [ ] End-to-end test

```bash
# Run verification
./scripts/dr/verify_recovery.sh

# Check services
curl http://localhost:8080/health
curl http://localhost:9090/-/healthy
```

---

## Success Criteria

- [ ] All services responding
- [ ] Metrics data visible in Grafana
- [ ] Application accepts requests
- [ ] RTO < 4 hours achieved
- [ ] RPO < 1 hour achieved
