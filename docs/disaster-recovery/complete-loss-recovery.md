# Complete Infrastructure Loss - Recovery Playbook

## 🎯 Scenario

Complete loss of monitoring infrastructure:

- All servers destroyed or inaccessible
- Need to rebuild from scratch
- Only off-site S3 backups are available

**RTO Target:** 4 hours  
**RPO Target:** 1 hour

---

## 📋 Pre-Requisites

### What You Need

- [ ] Access to off-site backups (S3)
- [ ] New server/infrastructure provisioned
- [ ] AWS credentials
- [ ] Git repository access
- [ ] Secrets/credentials from vault
- [ ] This playbook

### Team Required

- Incident Commander (1)
- Infrastructure Engineer (1-2)
- Application Engineer (1)
- QA/Verification (1)

---

## 🚀 Recovery Steps

### Phase 1: Infrastructure Setup (≈60 minutes)

#### Step 1.1: Provision New Server

```bash
# Example: AWS EC2
aws ec2 run-instances \
  --image-id ami-xxxxx \
  --instance-type t3.xlarge \
  --key-name mcp-key \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx \
  --block-device-mappings '[]'

# Wait for instance
aws ec2 wait instance-running --instance-ids <instance-id>

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids <instance-id> \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Server ready at: $PUBLIC_IP"
```

Checklist:

- [ ] Server provisioned
- [ ] Public IP obtained
- [ ] Security groups configured
- [ ] SSH access verified

#### Step 1.2: Install Dependencies

```bash
ssh -i mcp-key.pem ubuntu@$PUBLIC_IP

sudo apt-get update
sudo apt-get upgrade -y

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

sudo apt-get install -y git curl jq awscli sqlite3 htop

docker --version
docker-compose --version
aws --version
```

Checklist:

- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] AWS CLI configured
- [ ] Utilities available

#### Step 1.3: Create Directory Structure

```bash
sudo mkdir -p /var/mcp-data/{prometheus,grafana,redis}
sudo mkdir -p /var/mcp-logs
sudo mkdir -p /var/backups/mcp-monitoring/{prometheus,grafana,application,logs}

sudo chown -R $USER:$USER /var/mcp-data /var/mcp-logs /var/backups/mcp-monitoring
chmod -R 755 /var/mcp-data /var/mcp-logs /var/backups/mcp-monitoring
```

Checklist:

- [ ] Directories created
- [ ] Permissions set
- [ ] Ownership configured

---

### Phase 2: Application Deployment (≈45 minutes)

#### Step 2.1: Clone Repository

```bash
cd /opt
sudo git clone https://github.com/your-org/mcp-memory-server.git
sudo chown -R $USER:$USER mcp-memory-server
cd mcp-memory-server
git checkout v1.0.0
ls -la
```

Checklist:

- [ ] Repository cloned
- [ ] Correct ref checked out
- [ ] Files present

#### Step 2.2: Configure Environment

```bash
cat > .env <<'EOF'
ENVIRONMENT=production
GRAFANA_PASSWORD=<from-vault>
REDIS_PASSWORD=<from-vault>
SLACK_WEBHOOK_URL=<from-vault>
MCP_API_KEY=<from-vault>
AWS_ACCESS_KEY_ID=<from-vault>
AWS_SECRET_ACCESS_KEY=<from-vault>
AWS_DEFAULT_REGION=us-east-1
EOF
chmod 600 .env
source .env
```

Checklist:

- [ ] .env created
- [ ] Secrets populated
- [ ] Permissions correct

#### Step 2.3: Restore Configuration Files

```bash
aws s3 cp s3://mcp-backups/config/config.prod.yaml ./config.yaml
aws s3 cp s3://mcp-backups/config/docker-compose.prod.yml ./docker-compose.yml
aws s3 cp s3://mcp-backups/config/prometheus.yml ./monitoring/prometheus.yml
aws s3 cp s3://mcp-backups/config/alertmanager.yml ./monitoring/alertmanager/config.yml

docker-compose config
```

Checklist:

- [ ] Config files restored
- [ ] Validation passed
- [ ] No syntax errors

---

### Phase 3: Data Recovery (≈90 minutes)

#### Step 3.1: Download Backups from S3

```bash
cat > /tmp/download_backups.sh <<'SCRIPT'
#!/bin/bash
set -euo pipefail

echo "📥 Downloading backups from S3..."
aws s3 sync s3://mcp-backups/monitoring/prometheus/ /var/backups/mcp-monitoring/prometheus/ \
  --exclude "*" --include "snapshot_*.tar.gz" --include "snapshot_*.sha256"
aws s3 sync s3://mcp-backups/monitoring/grafana/ /var/backups/mcp-monitoring/grafana/ \
  --exclude "*" --include "grafana_*.tar.gz" --include "grafana_*.sha256"
aws s3 sync s3://mcp-backups/monitoring/application/ /var/backups/mcp-monitoring/application/ \
  --exclude "*" --include "app_*.tar.gz" --include "app_*.sha256"

ls -lht /var/backups/mcp-monitoring/prometheus/snapshot_*.tar.gz | head -1
ls -lht /var/backups/mcp-monitoring/grafana/grafana_*.tar.gz | head -1
ls -lht /var/backups/mcp-monitoring/application/app_*.tar.gz | head -1
SCRIPT
chmod +x /tmp/download_backups.sh
/tmp/download_backups.sh
```

Checklist:

- [ ] Backups downloaded
- [ ] Checksums available
- [ ] Integrity validated

#### Step 3.2: Start Infrastructure Services

```bash
docker-compose -f docker-compose.monitoring.yml up -d
sleep 30
docker-compose ps
```

Checklist:

- [ ] Prometheus running
- [ ] Grafana running
- [ ] Alertmanager running
- [ ] Containers healthy

#### Step 3.3: Restore Prometheus Data

```bash
sudo ./scripts/restore_prometheus.sh latest
```

Checklist:

- [ ] Data restored
- [ ] Health check passed
- [ ] Queries return data

#### Step 3.4: Restore Grafana Data

```bash
./scripts/restore_grafana.sh latest
curl -u admin:$GRAFANA_PASSWORD http://localhost:3000/api/search
```

Checklist:

- [ ] Dashboards restored
- [ ] Datasources configured
- [ ] UI accessible

#### Step 3.5: Restore Application Data

```bash
sudo ./scripts/restore_application.sh latest
```

Checklist:

- [ ] Database restored
- [ ] Vector store restored
- [ ] Health check passed

---

### Phase 4: Verification (≈30 minutes)

```bash
./scripts/verify_recovery.sh
curl http://localhost:8080/metrics | head -20
curl http://localhost:9090/-/healthy
curl -u admin:$GRAFANA_PASSWORD http://localhost:3000/api/health
```

Checklist:

- [ ] All services healthy
- [ ] Metrics flowing
- [ ] Prometheus has data
- [ ] Grafana dashboards load
- [ ] Alerts configured

---

### Phase 5: Monitoring & Handoff (≈15 minutes)

#### Step 5.1: Configure Backup Cron Jobs

```cron
5 * * * * /opt/mcp-memory-server/scripts/backup_prometheus_advanced.sh
0 2 * * * /opt/mcp-memory-server/scripts/backup_application.sh
0 3 * * * /opt/mcp-memory-server/scripts/backup_grafana_advanced.sh
0 */4 * * * /opt/mcp-memory-server/scripts/check_backup_health.sh
```

Checklist:

- [ ] Cron jobs set
- [ ] Monitoring enabled
- [ ] Alerts active

#### Step 5.2: Document Recovery

Create a recovery report capturing timeline, RTO/RPO achieved, issues, and action items.

#### Step 5.3: Notify Stakeholders

Send a status update (Slack/email) with recovery time, data loss (if any), and current system health.

---

## 📊 Recovery Metrics

| Metric        | Target  | Actual | Status |
| ------------- | ------- | ------ | ------ |
| **RTO**       | 4 hours | **\_** | ⬜     |
| **RPO**       | 1 hour  | **\_** | ⬜     |
| **Data Loss** | Minimal | **\_** | ⬜     |
| **Team Size** | 4-5     | **\_** | ⬜     |

---

## ✅ Final Checklist

- [ ] All services running
- [ ] All data restored
- [ ] Verification passed
- [ ] DNS updated (if applicable)
- [ ] Backups configured
- [ ] Monitoring active
- [ ] Documentation updated
- [ ] Stakeholders notified
- [ ] Post-mortem scheduled

---

**Recovery Complete!**
