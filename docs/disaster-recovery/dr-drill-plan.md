# Full Disaster Recovery Drill - Execution Plan

## 🎯 Drill Information

**Drill Type:** Full Infrastructure Loss  
**Date:** [TO BE SCHEDULED]  
**Duration:** 4-6 hours  
**Environment:** Test/Staging (NOT PRODUCTION)  

## 👥 Team Roles

### Required Roles

| Role | Responsibilities | Name | Contact |
|------|------------------|------|---------|
| **Drill Commander** | Overall coordination, decisions | _______ | _______ |
| **Infrastructure Lead** | Server provisioning, networking | _______ | _______ |
| **Application Lead** | Application deployment | _______ | _______ |
| **Data Lead** | Backup restoration | _______ | _______ |
| **Observer** | Document, time, photograph | _______ | _______ |

### Optional Roles
- **Security Liaison** - Security validations
- **Stakeholder Observer** - Business representative

## 📅 Pre-Drill Preparation (T-7 days)

### Week Before Drill

#### Day -7: Planning
- [ ] Schedule drill date/time
- [ ] Assign roles
- [ ] Book meeting rooms/video calls
- [ ] Reserve test infrastructure
- [ ] Notify stakeholders

#### Day -5: Preparation
- [ ] Verify latest backups available
- [ ] Test backup download from S3
- [ ] Prepare isolated test environment
- [ ] Review DR procedures
- [ ] Prepare communication channels

#### Day -3: Verification
- [ ] Verify all team members available
- [ ] Confirm test environment ready
- [ ] Verify backup integrity
- [ ] Print/distribute playbooks
- [ ] Set up monitoring dashboard

#### Day -1: Final Checks
- [ ] All team members briefed
- [ ] Equipment ready (laptops, access)
- [ ] Backup playbook locations
- [ ] Emergency contacts updated
- [ ] Go/No-Go decision

## 🚀 Drill Execution Timeline

### Phase 0:  Drill Kickoff (T+0, 15 minutes)

**Objective:** Brief team and commence drill

**Tasks:**
1. [ ] **Gather team** (5 min)
   - All roles present
   - Communication channels open
   - Timers ready

2. [ ] **Brief scenario** (5 min)
   - "Complete data center loss"
   - "All production systems destroyed"
   - "Only backups available"

3. [ ] **Start timer** (1 min)
   - Record official start time:  __: __
   - Begin Phase 1

4. [ ] **Confirm readiness** (4 min)
   - All playbooks available
   - All access credentials ready
   - Backup locations confirmed

**Success Criteria:**
- ✅ All team members present and briefed
- ✅ Official start time recorded
- ✅ All roles understand responsibilities

**Time Limit:** 15 minutes  
**Actual Time:** _____ minutes

---

### Phase 1: Infrastructure Provisioning (T+15, 60 minutes)

**Objective:** Provision new infrastructure

**Led by:** Infrastructure Lead

#### Step 1.1: Provision Servers (30 min)

**Tasks:**
```bash
# Record start time
echo "Phase 1.1 Start: $(date)" | tee -a drill_log.txt

# Provision main server
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.xlarge \
    --key-name dr-drill-key \
    --security-group-ids sg-dr-drill \
    --subnet-id subnet-dr-drill \
    --block-device-mappings '[{
        "DeviceName": "/dev/sda1",
        "Ebs": {"VolumeSize": 100, "VolumeType": "gp3"}
    }]' \
    --tag-specifications 'ResourceType=instance,Tags=[
        {Key=Name,Value=mcp-dr-drill},
        {Key=Purpose,Value=DR-Drill}
    ]' \
    --output json | tee instance_info.json

# Get instance ID
INSTANCE_ID=$(jq -r '.Instances[0].InstanceId' instance_info.json)
echo "Instance ID: $INSTANCE_ID" | tee -a drill_log.txt

# Wait for instance
aws ec2 wait instance-running --instance-ids $INSTANCE_ID
echo "Instance running" | tee -a drill_log.txt

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0]. Instances[0].PublicIpAddress' \
    --output text)

echo "Public IP: $PUBLIC_IP" | tee -a drill_log.txt
echo "Phase 1.1 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] Server provisioned
- [ ] Instance running
- [ ] Public IP obtained
- [ ] SSH access verified

**Issues Encountered:**
```
[Document any issues]
```

**Time:** Start: __:__ End: __:__ Duration: ___ min

#### Step 1.2: Install Dependencies (20 min)

**Tasks:**
```bash
echo "Phase 1.2 Start: $(date)" | tee -a drill_log.txt

# SSH to server
ssh -i dr-drill-key. pem ubuntu@$PUBLIC_IP

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install utilities
sudo apt-get install -y \
    git \
    curl \
    jq \
    awscli \
    sqlite3 \
    python3-pip \
    htop

# Verify installations
docker --version
docker-compose --version
aws --version
python3 --version

echo "Phase 1.2 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] System updated
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] AWS CLI configured
- [ ] All utilities installed

**Issues Encountered:**
```
[Document any issues]
```

**Time:** Start: __:__ End: __:__ Duration: ___ min

#### Step 1.3: Create Directory Structure (10 min)

**Tasks:**
```bash
echo "Phase 1.3 Start: $(date)" | tee -a drill_log.txt

# Create directories
sudo mkdir -p /var/mcp-data/{prometheus,grafana,redis}
sudo mkdir -p /var/mcp-logs
sudo mkdir -p /var/backups/mcp-monitoring/{prometheus,grafana,application}
sudo mkdir -p /opt/mcp-memory-server

# Set ownership
sudo chown -R ubuntu: ubuntu /var/mcp-data
sudo chown -R ubuntu: ubuntu /var/mcp-logs
sudo chown -R ubuntu: ubuntu /var/backups/mcp-monitoring
sudo chown -R ubuntu:ubuntu /opt/mcp-memory-server

# Set permissions
chmod -R 755 /var/mcp-data
chmod -R 755 /var/mcp-logs
chmod -R 755 /var/backups/mcp-monitoring

# Verify structure
tree -L 2 /var/mcp-data
tree -L 2 /var/backups/mcp-monitoring

echo "Phase 1.3 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] All directories created
- [ ] Permissions set correctly
- [ ] Ownership configured
- [ ] Structure verified

**Issues Encountered:**
```
[Document any issues]
```

**Time:** Start: __:__ End: __:__ Duration: ___ min

**Phase 1 Summary:**
- Start Time: __:__
- End Time: __:__
- Total Duration: ___ minutes
- Target: 60 minutes
- Status: ⬜ On Time | ⬜ Delayed | ⬜ Early

---

### Phase 2: Application Deployment (T+75, 45 minutes)

**Objective:** Deploy application code and configuration

**Led by:** Application Lead

#### Step 2.1: Clone Repository (10 min)

**Tasks:**
```bash
echo "Phase 2.1 Start: $(date)" | tee -a drill_log.txt

# Clone repository
cd /opt
git clone https://github.com/your-org/mcp-memory-server.git
cd mcp-memory-server

# Checkout production version
git checkout v1.0.0
git verify-commit HEAD  # Verify GPG signature

# Verify files
ls -la
cat README.md

echo "Phase 2.1 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] Repository cloned
- [ ] Correct version checked out
- [ ] Signature verified
- [ ] Files present

**Time:** Start: __:__ End:  __:__ Duration: ___ min

#### Step 2.2: Configure Environment (15 min)

**Tasks:**
```bash
echo "Phase 2.2 Start: $(date)" | tee -a drill_log.txt

# Download configuration from secure storage
aws s3 cp s3://mcp-dr-secrets/config.prod.yaml ./config.yaml
aws s3 cp s3://mcp-dr-secrets/docker-compose.prod.yml ./docker-compose.yml

# Create . env file
cat > .env <<EOF
ENVIRONMENT=dr-drill
GRAFANA_PASSWORD=$(aws secretsmanager get-secret-value --secret-id grafana-password --query SecretString --output text)
REDIS_PASSWORD=$(aws secretsmanager get-secret-value --secret-id redis-password --query SecretString --output text)
SLACK_WEBHOOK_URL=$(aws secretsmanager get-secret-value --secret-id slack-webhook --query SecretString --output text)

AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
AWS_DEFAULT_REGION=us-east-1
EOF

# Secure . env file
chmod 600 . env

# Verify configuration
docker-compose config

echo "Phase 2.2 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] Configuration downloaded
- [ ] .env file created
- [ ] Secrets populated
- [ ] Configuration validated

**Time:** Start: __:__ End:  __:__ Duration: ___ min

#### Step 2.3: Pull Docker Images (20 min)

**Tasks:**
```bash
echo "Phase 2.3 Start: $(date)" | tee -a drill_log.txt

# Pull all images
docker-compose -f docker-compose.monitoring.yml pull
docker-compose -f docker-compose.yml pull

# List images
docker images

# Verify images
docker images | grep -E "prometheus|grafana|redis|mcp-memory-server"

echo "Phase 2.3 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] All images pulled
- [ ] No pull errors
- [ ] Images verified

**Time:** Start: __:__ End: __:__ Duration: ___ min

**Phase 2 Summary:**
- Start Time: __:__
- End Time: __:__
- Total Duration: ___ minutes
- Target: 45 minutes
- Status: ⬜ On Time | ⬜ Delayed | ⬜ Early

---

### Phase 3: Data Recovery (T+120, 90 minutes)

**Objective:** Restore all data from backups

**Led by:** Data Lead

#### Step 3.1: Download Backups (20 min)

**Tasks:**
```bash
echo "Phase 3.1 Start: $(date)" | tee -a drill_log.txt

# Download Prometheus backups
aws s3 sync s3://mcp-backups/monitoring/prometheus/ \
    /var/backups/mcp-monitoring/prometheus/ \
    --exclude "*" \
    --include "snapshot_*.tar.gz" \
    --include "snapshot_*.sha256"

# Download Grafana backups
aws s3 sync s3://mcp-backups/monitoring/grafana/ \
    /var/backups/mcp-monitoring/grafana/ \
    --exclude "*" \
    --include "grafana_*.tar.gz" \
    --include "grafana_*.sha256"

# Download Application backups
aws s3 sync s3://mcp-backups/monitoring/application/ \
    /var/backups/mcp-monitoring/application/ \
    --exclude "*" \
    --include "app_*.tar.gz" \
    --include "app_*.sha256"

# List downloaded backups
find /var/backups/mcp-monitoring -type f -name "*.tar.gz" -exec ls -lh {} \;

# Verify checksums
cd /var/backups/mcp-monitoring/prometheus
for backup in *.tar.gz; do
    if [ -f "$backup. sha256" ]; then
        sha256sum -c "$backup. sha256" && echo "✅ $backup OK" || echo "❌ $backup FAILED"
    fi
done

echo "Phase 3.1 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] Prometheus backups downloaded
- [ ] Grafana backups downloaded
- [ ] Application backups downloaded
- [ ] All checksums verified

**Time:** Start:  __:__ End: __:__ Duration: ___ min

#### Step 3.2: Start Services (15 min)

**Tasks:**
```bash
echo "Phase 3.2 Start: $(date)" | tee -a drill_log.txt

# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services
sleep 30

# Check status
docker-compose -f docker-compose.monitoring.yml ps

# Verify services
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health  # Grafana
redis-cli ping  # Redis

echo "Phase 3.2 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] Services started
- [ ] All containers running
- [ ] Health checks passed

**Time:** Start: __:__ End: __:__ Duration: ___ min

#### Step 3.3: Restore Prometheus (25 min)

**Tasks:**
```bash
echo "Phase 3.3 Start: $(date)" | tee -a drill_log.txt

# Find latest Prometheus backup
LATEST_PROM=$(ls -t /var/backups/mcp-monitoring/prometheus/snapshot_*.tar.gz | head -1)
echo "Restoring from: $LATEST_PROM"

# Stop Prometheus
docker-compose -f docker-compose. monitoring.yml stop prometheus

# Extract backup
TEMP_DIR=$(mktemp -d)
tar -xzf "$LATEST_PROM" -C "$TEMP_DIR"

# Find snapshot directory
SNAPSHOT_DIR=$(find "$TEMP_DIR" -type d -name "snapshot_*" | head -1)

# Copy to Prometheus data directory
sudo cp -r "$SNAPSHOT_DIR"/* /var/mcp-data/prometheus/

# Set permissions
sudo chown -R 65534:65534 /var/mcp-data/prometheus

# Cleanup
rm -rf "$TEMP_DIR"

# Start Prometheus
docker-compose -f docker-compose.monitoring.yml start prometheus

# Wait and verify
sleep 15
curl http://localhost:9090/-/healthy

# Check data
curl -s 'http://localhost:9090/api/v1/query? query=up' | jq '. data.result | length'

echo "Phase 3.3 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] Backup extracted
- [ ] Data restored
- [ ] Prometheus started
- [ ] Health check passed
- [ ] Data queryable

**Time:** Start: __:__ End: __:__ Duration: ___ min

#### Step 3.4: Restore Grafana (15 min)

**Tasks:**
```bash
echo "Phase 3.4 Start: $(date)" | tee -a drill_log.txt

# Find latest Grafana backup
LATEST_GRAFANA=$(ls -t /var/backups/mcp-monitoring/grafana/grafana_*.tar.gz | head -1)
echo "Restoring from: $LATEST_GRAFANA"

# Run restore script
cd /opt/mcp-memory-server
./scripts/restore_grafana.sh "$LATEST_GRAFANA"

# Verify
curl -u admin:$GRAFANA_PASSWORD http://localhost:3000/api/search | jq '. | length'

echo "Phase 3.4 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] Grafana restored
- [ ] Dashboards imported
- [ ] Datasources configured
- [ ] UI accessible

**Time:** Start: __:__ End: __:__ Duration: ___ min

#### Step 3.5: Restore Application (15 min)

**Tasks:**
```bash
echo "Phase 3.5 Start: $(date)" | tee -a drill_log.txt

# Find latest application backup
LATEST_APP=$(ls -t /var/backups/mcp-monitoring/application/app_*.tar.gz | head -1)
echo "Restoring from: $LATEST_APP"

# Start application
docker-compose up -d mcp-memory-server
sleep 20

# Stop for restore
docker-compose stop mcp-memory-server

# Run restore script
./scripts/restore_application.sh "$LATEST_APP"

# Verify
curl http://localhost:8080/health

echo "Phase 3.5 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] Application restored
- [ ] Database restored
- [ ] ChromaDB restored
- [ ] Health check passed

**Time:** Start: __:__ End: __:__ Duration: ___ min

**Phase 3 Summary:**
- Start Time: __:__
- End Time: __:__
- Total Duration: ___ minutes
- Target: 90 minutes
- Status: ⬜ On Time | ⬜ Delayed | ⬜ Early

---

### Phase 4: Verification (T+210, 30 minutes)

**Objective:** Verify all systems operational

**Led by:** Drill Commander

#### Step 4.1: Run Verification Script (10 min)

**Tasks:**
```bash
echo "Phase 4.1 Start: $(date)" | tee -a drill_log.txt

# Run comprehensive verification
./scripts/verify_recovery.sh | tee verification_results.txt

echo "Phase 4.1 Complete: $(date)" | tee -a drill_log.txt
```

**Checklist:**
- [ ] All services healthy
- [ ] Metrics collecting
- [ ] Prometheus has data
- [ ] Grafana dashboards load
- [ ] Application functional

**Time:** Start: __: __ End: __:__ Duration:  ___ min

#### Step 4.2: Manual Verification (15 min)

**Tasks:**
```bash
echo "Phase 4.2 Start: $(date)" | tee -a drill_log.txt

# Test each component manually
echo "Testing Prometheus..."
curl -s http://localhost:9090/api/v1/query? query=mcp_journal_sessions_total | jq . 

echo "Testing Grafana..."
curl -u admin:$GRAFANA_PASSWORD http://localhost:3000/api/dashboards/home | jq .

echo "Testing Application..."
curl -s http://localhost:8080/metrics | grep mcp_journal | head -5

echo "Testing Database..."
docker exec mcp-memory-server sqlite3 /app/data/memory.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"

echo "Phase 4.2 Complete: $(date)" | tee -a drill_log. txt
```

**Checklist:**
- [ ] Prometheus queries work
- [ ] Grafana UI accessible
- [ ] Application metrics present
- [ ] Database intact

**Time:** Start: __: __ End: __:__ Duration:  ___ min

#### Step 4.3: End-to-End Test (5 min)

**Tasks:**
```bash
echo "Phase 4.3 Start: $(date)" | tee -a drill_log.txt

# Generate test activity
# (This would involve actual API calls to your application)

echo "Phase 4.3 Complete: $(date)" | tee -a drill_log. txt
```

**Checklist:**
- [ ] Can create new data
- [ ] Data appears in metrics
- [ ] Data appears in Prometheus
- [ ] Data appears in Grafana

**Time:** Start:  __:__ End: __:__ Duration: ___ min

**Phase 4 Summary:**
- Start Time: __:__
- End Time: __:__
- Total Duration: ___ minutes
- Target: 30 minutes
- Status: ⬜ On Time | ⬜ Delayed | ⬜ Early

---

### Phase 5: Drill Conclusion (T+240, 30 minutes)

**Objective:** Wrap up, debrief, document

**Led by:** Drill Commander

#### Step 5.1: Stop Timer (1 min)

**Tasks:**
- [ ] Record official end time:  __:__
- [ ] Calculate total duration: ___ hours ___ minutes
- [ ] Compare to RTO target: 4 hours

#### Step 5.2: Team Debrief (20 min)

**Discussion Points:**
1. What went well?
2. What were the challenges?
3. What unexpected issues occurred?
4. What should be improved?
5. Was the playbook accurate?

**Notes:**
```
[Team feedback here]
```

#### Step 5.3: Document Results (9 min)

**Tasks:**
- [ ] Collect all logs
- [ ] Take screenshots
- [ ] Archive drill data
- [ ] Create initial report

**Phase 5 Summary:**
- Drill officially ended:  __:__
- Total drill duration: ___ hours ___ minutes

---

## 📊 Drill Metrics

### Time Tracking

| Phase | Target | Actual | Variance | Status |
|-------|--------|--------|----------|--------|
| Phase 0:  Kickoff | 15 min | ___ min | ___ | ⬜ |
| Phase 1: Infrastructure | 60 min | ___ min | ___ | ⬜ |
| Phase 2: Deployment | 45 min | ___ min | ___ | ⬜ |
| Phase 3: Data Recovery | 90 min | ___ min | ___ | ⬜ |
| Phase 4: Verification | 30 min | ___ min | ___ | ⬜ |
| Phase 5: Conclusion | 30 min | ___ min | ___ | ⬜ |
| **Total** | **270 min (4.5 hr)** | **___ min** | **___** | **⬜** |

### Success Criteria

| Criterion | Target | Actual | Met?  |
|-----------|--------|--------|------|
| **RTO** | <4 hours | ___ hours | ⬜ |
| **All services restored** | 100% | ___% | ⬜ |
| **Data loss** | <1 hour | ___ min | ⬜ |
| **Team executed** | Yes | ⬜ Yes ⬜ No | ⬜ |
| **Playbook accurate** | Yes | ⬜ Yes ⬜ No | ⬜ |

### Data Recovery

| Component | Backup Age | Data Loss | Status |
|-----------|------------|-----------|--------|
| Prometheus | ___ | ___ min | ⬜ |
| Grafana | ___ | ___ min | ⬜ |
| Application | ___ | ___ min | ⬜ |

---

## 🐛 Issues Log

| # | Phase | Issue | Impact | Resolved?  | Notes |
|---|-------|-------|--------|-----------|-------|
| 1 | | | | ⬜ | |
| 2 | | | | ⬜ | |
| 3 | | | | ⬜ | |

---

## ✅ Post-Drill Actions

### Immediate (Within 24 hours)
- [ ] Complete drill report
- [ ] Share with stakeholders
- [ ] Create tickets for issues found
- [ ] Update playbooks if needed

### Short-term (Within 1 week)
- [ ] Hold detailed retrospective
- [ ] Update DR procedures
- [ ] Fix identified issues
- [ ] Improve documentation

### Long-term (Within 1 month)
- [ ] Schedule next drill
- [ ] Implement improvements
- [ ] Train on lessons learned
- [ ] Update RTO/RPO if needed

---

## 📸 Documentation

### Required Evidence
- [ ] Start/end time photos
- [ ] Team photos
- [ ] Screen recordings (key steps)
- [ ] Log files
- [ ] Screenshots of restored systems

### Files to Archive
- [ ] drill_log.txt
- [ ] verification_results.txt
- [ ] instance_info.json
- [ ] All command outputs
- [ ] Drill report

---

**Drill Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete

**Final RTO:** ___ hours ___ minutes  
**Target Met:** ⬜ YES | ⬜ NO  
**Overall Success:** ⬜ YES | ⬜ PARTIAL | ⬜ NO
