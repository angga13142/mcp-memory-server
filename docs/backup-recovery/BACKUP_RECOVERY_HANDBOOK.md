# Backup & Recovery Handbook
## MCP Memory Server - Monitoring & Observability

**Version:** 1.0  
**Last Updated:** 2025-01-08  
**Maintainer:** DevOps Team

---

## 📖 Table of Contents

1. [Introduction](#1-introduction)
2. [Backup Strategy](#2-backup-strategy)
3. [Backup Procedures](#3-backup-procedures)
4. [Recovery Procedures](#4-recovery-procedures)
5. [Disaster Recovery](#5-disaster-recovery)
6. [Testing & Validation](#6-testing--validation)
7. [Operational Procedures](#7-operational-procedures)
8. [Troubleshooting](#8-troubleshooting)
9. [Reference](#9-reference)

---

## 1. INTRODUCTION

### 1.1 Purpose

This handbook provides comprehensive guidance for backup and recovery operations of the MCP Memory Server monitoring infrastructure. It covers:

- Daily backup operations
- Recovery procedures for all scenarios
- Disaster recovery planning
- Testing and validation
- Troubleshooting common issues

### 1.2 Audience

This handbook is intended for: 

- **System Administrators** - Daily operations
- **DevOps Engineers** - Automation and tooling
- **On-Call Engineers** - Incident response
- **SRE Team** - Reliability and planning
- **Security Team** - Security and compliance

### 1.3 Scope

**In Scope:**
- Prometheus time series database
- Grafana dashboards and configuration
- Application SQLite database
- ChromaDB vector store
- Configuration files

**Out of Scope:**
- Source code (managed via Git)
- Container images (managed via registry)
- Operating system backups
- Network configuration

### 1.4 Key Definitions

| Term | Definition |
|------|------------|
| **RTO** | Recovery Time Objective - Maximum acceptable downtime |
| **RPO** | Recovery Point Objective - Maximum acceptable data loss |
| **Backup** | Copy of data stored separately from primary storage |
| **Restore** | Process of recovering data from backup |
| **DR** | Disaster Recovery - Recovery from catastrophic failure |
| **Snapshot** | Point-in-time copy of data |

---

## 2. BACKUP STRATEGY

### 2.1 Backup Architecture

```
┌──────────────────────────────────────────────────┐
│           Production Systems                      │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │Prometheus│  │ Grafana  │  │   App    │      │
│  │   TSDB   │  │Dashboards│  │ Database │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
└───────┼─────────────┼─────────────┼─────────────┘
        │             │             │
        │  Hourly     │  Daily      │  Hourly
        │             │             │
        ▼             ▼             ▼
┌──────────────────────────────────────────────────┐
│         Local Backup Storage                      │
│      /var/backups/mcp-monitoring/                │
│                                                   │
│  ├── prometheus/  (Snapshots)                    │
│  ├── grafana/     (Dashboards + DB)              │
│  └── application/ (SQLite + ChromaDB)            │
└────────────────────┬─────────────────────────────┘
                     │
                     │  Real-time sync
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│         Off-Site Storage (S3)                     │
│      s3://mcp-backups/monitoring/                │
│                                                   │
│  ├── prometheus/                                  │
│  ├── grafana/                                     │
│  └── application/                                 │
└──────────────────────────────────────────────────┘
```

### 2.2 Backup Schedule

| Component | Frequency | Time | Retention |
|-----------|-----------|------|-----------|
| **Prometheus** | Hourly | xx:05 | 24 hourly, 7 daily |
| **Application** | Hourly | xx:10 | 24 hourly, 7 daily |
| **Grafana** | Daily | 03:00 | 30 daily, 12 monthly |
| **Configuration** | On-change | Real-time (Git) | Infinite |

### 2.3 What Gets Backed Up

#### Prometheus (High Priority)
```
prometheus/
├── chunks_head/          # Current chunks
├── wal/                  # Write-ahead log
├── 01HXXX*/             # Historical blocks
└── queries.active       # Active queries
```
- **Size:** 500MB - 5GB per backup
- **Critical:** Yes
- **Compression:** gzip

#### Grafana (Medium Priority)
```
grafana/
├── dashboards/           # All dashboards (JSON)
├── datasources.json      # Datasource configs
├── grafana.db           # SQLite database
└── grafana.ini          # Configuration
```
- **Size:** 10-50MB per backup
- **Critical:** Medium
- **Compression:** gzip

#### Application (High Priority)
```
application/
├── memory.db            # SQLite database
├── chroma_db/           # Vector store
└── config.yaml          # Configuration
```
- **Size:** 100MB - 1GB per backup
- **Critical:** Yes
- **Compression:** gzip

### 2.4 Retention Policy

```yaml
Retention Strategy:
  Hourly: 
    keep: 24              # Last 24 hours
    applies_to: [prometheus, application]
    
  Daily:
    keep: 7               # Last 7 days
    applies_to: [all]
    
  Weekly: 
    keep: 4               # Last 4 weeks
    applies_to: [all]
    day: Sunday
    
  Monthly:
    keep: 12              # Last 12 months
    applies_to: [grafana, application]
    day: 1st
    
  Yearly:
    keep: 3               # Last 3 years
    applies_to: [application]
    day: January 1st
```

### 2.5 Storage Requirements

**Current State:**
- Local storage: 50GB allocated
- S3 storage: 100GB used
- Monthly growth: ~5%

**Projections (12 months):**
- Local: 80GB required
- S3: 160GB required
- Cost: ~$10/month S3 storage

---

## 3. BACKUP PROCEDURES

### 3.1 Prometheus Backup

#### Automated Backup

Backup runs automatically via cron: 
```cron
5 * * * * /opt/mcp-memory-server/scripts/backup_prometheus_advanced.sh
```

#### Manual Backup

```bash
# Navigate to project directory
cd /opt/mcp-memory-server

# Run backup script
sudo ./scripts/backup_prometheus_advanced.sh

# Check backup was created
ls -lh /var/backups/mcp-monitoring/prometheus/

# Verify checksum
cd /var/backups/mcp-monitoring/prometheus
LATEST=$(ls -t snapshot_*.tar.gz | head -1)
sha256sum -c ${LATEST}.sha256
```

#### Verify Backup

```bash
# Check backup integrity
tar -tzf /var/backups/mcp-monitoring/prometheus/latest.tar.gz | head

# Check S3 upload
aws s3 ls s3://mcp-backups/monitoring/prometheus/ | tail -5

# Check backup size
du -sh /var/backups/mcp-monitoring/prometheus/latest.tar.gz
```

**Expected Output:**
```
✅ Snapshot created successfully
✅ Backup compressed (250MB)
✅ Checksum: abc123... 
✅ Uploaded to S3
```

---

### 3.2 Grafana Backup

#### Automated Backup

```cron
0 3 * * * /opt/mcp-memory-server/scripts/backup_grafana_advanced.sh
```

#### Manual Backup

```bash
# Set Grafana credentials
export GRAFANA_PASSWORD="your-password"

# Run backup
sudo ./scripts/backup_grafana_advanced.sh

# Verify dashboards exported
tar -tzf /var/backups/mcp-monitoring/grafana/latest.tar.gz | grep dashboard
```

#### Export Single Dashboard (Manual)

```bash
# List all dashboards
curl -s -u admin:$GRAFANA_PASSWORD \
  http://localhost:3000/api/search | jq '.[] | {title: .title, uid: .uid}'

# Export specific dashboard
DASHBOARD_UID="journal-overview"
curl -s -u admin:$GRAFANA_PASSWORD \
  "http://localhost:3000/api/dashboards/uid/$DASHBOARD_UID" \
  > dashboard_backup_$(date +%Y%m%d).json
```

---

### 3.3 Application Backup

#### Automated Backup

```cron
10 * * * * /opt/mcp-memory-server/scripts/backup_application.sh
```

#### Manual Backup

```bash
# Run backup script
sudo ./scripts/backup_application.sh

# Verify database backup
tar -tzf /var/backups/mcp-monitoring/application/latest.tar.gz | grep memory.db

# Check database integrity
LATEST_BACKUP=$(ls -t /var/backups/mcp-monitoring/application/app_*.tar.gz | head -1)
TEMP_DIR=$(mktemp -d)
tar -xzf $LATEST_BACKUP -C $TEMP_DIR
gunzip -c $TEMP_DIR/*/memory.db.gz | sqlite3 /tmp/test.db "PRAGMA integrity_check;"
rm -rf $TEMP_DIR /tmp/test.db
```

---

### 3.4 Configuration Backup

Configuration files are version controlled in Git:

```bash
# Check what's tracked
git ls-files | grep -E "(config|yml|yaml|json)"

# Commit configuration changes
git add config*.yaml monitoring/*.yml
git commit -m "Update monitoring configuration"
git push origin main

# Tag important versions
git tag -a config-v1.0 -m "Production configuration v1.0"
git push origin --tags
```

---

### 3.5 Monitoring Backup Health

#### Check Backup Status

```bash
# Run health check
sudo ./scripts/check_backup_health.sh

# View backup dashboard
# Open: http://localhost:3000/d/backup-health
```

#### Backup Metrics

```promql
# Last successful backup (seconds ago)
time() - mcp_backup_last_success_timestamp_seconds

# Backup success rate (last 24h)
rate(mcp_backup_total{status="success"}[24h]) / rate(mcp_backup_total[24h])

# Backup size trend
mcp_backup_size_bytes
```

---

## 4. RECOVERY PROCEDURES

### 4.1 Prometheus Recovery

#### Quick Recovery (Latest Backup)

```bash
# Stop Prometheus
docker-compose -f docker-compose.monitoring.yml stop prometheus

# Restore from latest backup
sudo ./scripts/restore_prometheus.sh latest

# Verify
curl http://localhost:9090/-/healthy
curl -s 'http://localhost:9090/api/v1/query?query=up'
```

**Time:** 15-20 minutes  
**Data Loss:** <1 hour

#### Recovery from Specific Backup

```bash
# List available backups
ls -lht /var/backups/mcp-monitoring/prometheus/snapshot_*.tar.gz

# Restore specific backup
BACKUP_FILE="/var/backups/mcp-monitoring/prometheus/snapshot_20250108_100000.tar.gz"
sudo ./scripts/restore_prometheus.sh $BACKUP_FILE

# Verify data range
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.'
```

#### Recovery from S3

```bash
# Download specific backup from S3
aws s3 cp s3://mcp-backups/monitoring/prometheus/snapshot_20250108_100000.tar.gz \
  /var/backups/mcp-monitoring/prometheus/

# Restore
sudo ./scripts/restore_prometheus.sh /var/backups/mcp-monitoring/prometheus/snapshot_20250108_100000.tar.gz
```

---

### 4.2 Grafana Recovery

#### Restore Dashboards

```bash
# Restore all dashboards and datasources
sudo ./scripts/restore_grafana.sh latest

# Verify dashboards
curl -s -u admin:$GRAFANA_PASSWORD http://localhost:3000/api/search | jq '.[] | .title'
```

**Time:** 10-15 minutes

#### Restore Single Dashboard

```bash
# Import dashboard JSON
curl -X POST http://admin:$GRAFANA_PASSWORD@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @dashboard_backup.json
```

#### Complete Grafana Restore (Database)

```bash
# CAUTION: This replaces ALL Grafana data

# Stop Grafana
docker-compose -f docker-compose.monitoring.yml stop grafana

# Restore database
sudo ./scripts/restore_grafana.sh latest
# When prompted, answer 'y' to restore database

# Start Grafana
docker-compose -f docker-compose.monitoring.yml start grafana
```

---

### 4.3 Application Recovery

#### Restore Application Data

```bash
# Stop application
docker-compose stop mcp-memory-server

# Restore from backup
sudo ./scripts/restore_application.sh latest

# Application automatically restarted by script

# Verify
curl http://localhost:8080/health
```

**Time:** 10-15 minutes  
**Data Loss:** <1 hour

#### Database-Only Recovery

```bash
# Stop application
docker-compose stop mcp-memory-server

# Extract database from backup
LATEST_BACKUP=$(ls -t /var/backups/mcp-monitoring/application/app_*.tar.gz | head -1)
TEMP_DIR=$(mktemp -d)
tar -xzf $LATEST_BACKUP -C $TEMP_DIR
gunzip -c $TEMP_DIR/*/memory.db.gz > /var/mcp-data/memory.db

# Set permissions
sudo chown 1000:1000 /var/mcp-data/memory.db

# Start application
docker-compose start mcp-memory-server

# Cleanup
rm -rf $TEMP_DIR
```

---

### 4.4 Point-in-Time Recovery

Restore system to specific timestamp:

```bash
# Restore to specific time
sudo ./scripts/restore_point_in_time.sh "2025-01-08 14:30:00"

# Script will:
# 1. Find closest backups for each component
# 2. Confirm with you
# 3. Restore all components
# 4. Verify system health
```

**Time:** 30-45 minutes  
**Data Loss:** Depends on backup frequency

---

### 4.5 Recovery Verification

After any recovery, run verification: 

```bash
# Comprehensive verification
sudo ./scripts/verify_recovery.sh

# Manual checks
curl http://localhost:8080/health        # Application
curl http://localhost:9090/-/healthy     # Prometheus
curl http://localhost:3000/api/health    # Grafana

# Check metrics collection
curl http://localhost:8080/metrics | grep mcp_journal

# Check Prometheus data
curl -s 'http://localhost:9090/api/v1/query?query=mcp_journal_sessions_total'

# Check Grafana dashboards
curl -s -u admin:$GRAFANA_PASSWORD http://localhost:3000/api/search
```

**Success Criteria:**
- ✅ All health checks return 200
- ✅ Metrics being collected
- ✅ Prometheus has data
- ✅ Grafana dashboards load
- ✅ No errors in logs

---

## 5. DISASTER RECOVERY

### 5.1 Complete Infrastructure Loss

**Scenario:** Data center destroyed, all servers lost

**Playbook:** `docs/disaster-recovery/complete-loss-recovery.md`

**Recovery Steps Summary:**

**Phase 1: Infrastructure (60 min)**
1. Provision new server
2. Install dependencies (Docker, etc.)
3. Create directory structure

**Phase 2: Deploy Application (45 min)**
4. Clone repository
5. Configure environment
6. Download configurations from S3

**Phase 3: Restore Data (90 min)**
7. Download all backups from S3
8. Restore Prometheus data
9. Restore Grafana dashboards
10. Restore application database

**Phase 4: Verification (30 min)**
11. Run health checks
12. Test functionality
13. Update DNS

**Phase 5: Handoff (15 min)**
14. Configure ongoing backups
15. Document recovery
16. Notify stakeholders

**Total Time:** ~4 hours  
**Data Loss:** <1 hour

**Quick Reference Card:**

```bash
# 1. Provision infrastructure
aws ec2 run-instances [...]

# 2. Install dependencies
curl -fsSL https://get.docker.com | sh

# 3. Clone repository
git clone https://github.com/your-org/mcp-memory-server
cd mcp-memory-server

# 4. Download backups
aws s3 sync s3://mcp-backups/monitoring/ /var/backups/mcp-monitoring/

# 5. Deploy and restore
docker-compose up -d
./scripts/restore_prometheus.sh latest
./scripts/restore_grafana.sh latest
./scripts/restore_application.sh latest

# 6. Verify
./scripts/verify_recovery.sh
```

---

### 5.2 Database Corruption

**Scenario:** SQLite database corrupted

**Script:** `scripts/recover_database_corruption.sh`

**Steps:**
1. Detect corruption
2. Stop application
3. Backup corrupted database
4. Attempt SQLite recovery
5. If recovery fails, restore from backup
6. Verify integrity
7. Restart application

**Time:** 1 hour  
**Data Loss:** <1 hour

**Manual Recovery:**

```bash
# Verify corruption
docker exec mcp-memory-server sqlite3 /app/data/memory.db "PRAGMA integrity_check;"

# If corrupted, run recovery script
sudo ./scripts/recover_database_corruption.sh
```

---

### 5.3 Ransomware Attack

**Scenario:** Systems compromised by ransomware

**Script:** `scripts/recover_ransomware.sh`

**Critical Steps:**
1. **IMMEDIATE:** Isolate all systems
2. Stop all services
3. Wipe all local data
4. Download clean code from Git
5. Restore from off-site backups
6. Scan backups for threats
7. Rebuild infrastructure
8. **Change all passwords/keys**
9. Security hardening
10. Forensic analysis

**Time:** 8 hours  
**Data Loss:** Depends on backup age

**⚠️ IMPORTANT:** Do NOT use local backups - they may be encrypted!

---

### 5.4 DR Contact List

| Role | Name | Phone | Email |
|------|------|-------|-------|
| **Incident Commander** | [Name] | [Phone] | [Email] |
| **SRE On-Call** | [Rotation] | [Phone] | [PagerDuty] |
| **Security Team** | [Name] | [Phone] | [Email] |
| **Infrastructure Lead** | [Name] | [Phone] | [Email] |
| **Database Admin** | [Name] | [Phone] | [Email] |

**Escalation Path:**
1. On-Call Engineer (0-15 min)
2. SRE Lead (15-30 min)
3. Engineering Manager (30-60 min)
4. VP Engineering (>60 min)

---

## 6. TESTING & VALIDATION

### 6.1 Daily Validation

Automated daily backup testing:

```bash
# Runs automatically at 04:00
# Cron: 0 4 * * * /opt/mcp-memory-server/scripts/test_backup_restore.sh

# Manual run
sudo ./scripts/test_backup_restore.sh
```

**Tests Performed:**
1.  Prometheus backup integrity
2. Prometheus restore test
3. Grafana backup integrity
4. Application backup integrity
5. Backup age check
6. S3 sync verification
7. Restore performance test
8. End-to-end backup & restore

**Success Criteria:** All 8 tests pass

---

### 6.2 DR Drills

Regular disaster recovery drills:

**Weekly (Prometheus):**
```bash
# Saturdays at 02:00
sudo ./scripts/dr_drill.sh prometheus
```

**Monthly (Grafana):**
```bash
# 1st Sunday at 02:00
sudo ./scripts/dr_drill.sh grafana
```

**Quarterly (Complete Infrastructure):**
```bash
# Manual execution required
# ⚠️ WARNING: Destructive test! 
sudo ./scripts/dr_drill.sh complete
```

---

### 6.3 Drill Checklist

**Pre-Drill:**
- [ ] Announce drill to team
- [ ] Verify backups are fresh
- [ ] Record baseline metrics
- [ ] Designate drill leader

**During Drill:**
- [ ] Record start time
- [ ] Follow playbook exactly
- [ ] Document any deviations
- [ ] Take notes on issues

**Post-Drill:**
- [ ] Record completion time
- [ ] Verify system functionality
- [ ] Generate drill report
- [ ] Identify improvements
- [ ] Update procedures

---

### 6.4 Generating Test Reports

```bash
# Generate comprehensive test report
sudo ./scripts/generate_test_report.sh

# View report
cat backup_recovery_report_$(date +%Y%m%d).md
```

---

## 7. OPERATIONAL PROCEDURES

### 7.1 Daily Operations

**Morning Checks (10 minutes):**
```bash
# Check backup health
./scripts/check_backup_health.sh

# View Grafana dashboard
# Open: http://localhost:3000/d/backup-health

# Check for failed backups
grep -i "error\|failed" /var/backups/mcp-monitoring/logs/*.log | tail -20
```

**Weekly Tasks:**
- Review backup sizes
- Check S3 storage usage
- Review DR drill results
- Update this handbook if needed

**Monthly Tasks:**
- Run comprehensive DR drill
- Review retention policies
- Audit backup access logs
- Update disaster recovery plan

---

### 7.2 Backup Size Management

**Check Current Usage:**
```bash
# Local storage
du -sh /var/backups/mcp-monitoring/*

# S3 storage
aws s3 ls --summarize --human-readable --recursive s3://mcp-backups/monitoring/
```

**Cleanup Old Backups (Manual):**
```bash
# Delete backups older than 60 days
find /var/backups/mcp-monitoring -name "*.tar.gz" -mtime +60 -delete

# Delete old S3 backups
aws s3 ls s3://mcp-backups/monitoring/prometheus/ | \
  awk '{if ($1 < "2024-11-01") print $4}' | \
  xargs -I {} aws s3 rm s3://mcp-backups/monitoring/prometheus/{}
```

---

### 7.3 Monitoring & Alerts

**Key Alerts:**

| Alert | Condition | Action |
|-------|-----------|--------|
| **BackupFailed** | Backup failed | Investigate immediately |
| **BackupOld** | No backup >3 hours | Run manual backup |
| **BackupSizeLarge** | Backup >10GB | Review retention |
| **S3UploadFailed** | S3 sync failed | Check AWS credentials |
| **LowDiskSpace** | <20GB free | Cleanup old backups |

**Alert Destinations:**
- Critical: PagerDuty + Slack #mcp-critical
- Warning: Slack #mcp-alerts
- Info: Email

---

## 8. TROUBLESHOOTING

### 8.1 Backup Failures

**Problem: Prometheus backup fails**

**Symptoms:**
- `backup_prometheus_advanced.sh` exits with error
- No new snapshot created
- Error in logs

**Diagnosis:**
```bash
# Check logs
tail -50 /var/backups/mcp-monitoring/logs/prometheus_backup.log

# Check Prometheus health
curl http://localhost:9090/-/healthy

# Check disk space
df -h /var/backups
```

**Solutions:**

1. **Disk full:**
   ```bash
   # Clean old backups
   find /var/backups/mcp-monitoring/prometheus -name "*.tar.gz" -mtime +7 -delete
   ```

2. **Prometheus not responding:**
   ```bash
   # Restart Prometheus
   docker-compose -f docker-compose.monitoring.yml restart prometheus
   ```

3. **Permission issues:**
   ```bash
   # Fix permissions
   sudo chown -R root:root /var/backups/mcp-monitoring
   sudo chmod -R 755 /var/backups/mcp-monitoring
   ```

---

**Problem: S3 upload fails**

**Symptoms:**
- Backup created locally but not in S3
- AWS CLI errors in logs

**Diagnosis:**
```bash
# Test AWS credentials
aws s3 ls s3://mcp-backups/

# Check network
ping s3.amazonaws.com
```

**Solutions:**

1. **Invalid credentials:**
   ```bash
   # Re-configure AWS CLI
   aws configure
   ```

2. **Network issues:**
   ```bash
   # Retry upload manually
   aws s3 sync /var/backups/mcp-monitoring/ s3://mcp-backups/monitoring/
   ```

3. **Bucket permissions:**
   ```bash
   # Verify bucket policy allows uploads
   aws s3api get-bucket-policy --bucket mcp-backups
   ```

---

### 8.2 Restore Failures

**Problem: Restore script fails**

**Symptoms:**
- `restore_*.sh` exits with error
- Data not restored
- Service won't start after restore

**Diagnosis:**
```bash
# Check logs
tail -50 /var/backups/mcp-monitoring/logs/*_restore.log

# Verify backup integrity
BACKUP_FILE="[path-to-backup].tar.gz"
tar -tzf $BACKUP_FILE > /dev/null
```

**Solutions:**

1. **Corrupted backup:**
   ```bash
   # Try older backup
   ls -lt /var/backups/mcp-monitoring/prometheus/
   ./scripts/restore_prometheus.sh /var/backups/mcp-monitoring/prometheus/snapshot_OLDER.tar.gz
   ```

2. **Permission issues:**
   ```bash
   # Fix Prometheus data permissions
   sudo chown -R 65534:65534 /var/mcp-data/prometheus
   ```

3. **Service won't start:**
   ```bash
   # Check logs
   docker-compose logs prometheus
   
   # Try starting manually
   docker-compose -f docker-compose.monitoring.yml up prometheus
   ```

---

### 8.3 Common Issues

**Issue: "No space left on device"**

```bash
# Check disk usage
df -h

# Clean up
sudo docker system prune -a
find /var/backups -mtime +30 -delete
```

**Issue: "Database is locked"**

```bash
# Stop application
docker-compose stop mcp-memory-server

# Try restore again
./scripts/restore_application.sh latest
```

**Issue: "Checksum mismatch"**

```bash
# Backup may be corrupted
# Download fresh copy from S3
aws s3 cp s3://mcp-backups/monitoring/prometheus/[backup-file] /var/backups/

# Try restore with fresh copy
```

---

## 9. REFERENCE

### 9.1 File Locations

```
/opt/mcp-memory-server/
├── scripts/
│   ├── backup_prometheus_advanced.sh
│   ├── backup_grafana_advanced.sh
│   ├── backup_application.sh
│   ├── restore_prometheus.sh
│   ├── restore_grafana.sh
│   ├── restore_application.sh
│   ├── restore_point_in_time.sh
│   ├── recover_database_corruption.sh
│   ├── recover_ransomware.sh
│   ├── test_backup_restore.sh
│   ├── dr_drill.sh
│   ├── check_backup_health.sh
│   └── verify_recovery.sh

/var/backups/mcp-monitoring/
├── prometheus/
├── grafana/
├── application/
└── logs/

s3://mcp-backups/monitoring/
├── prometheus/
├── grafana/
└── application/
```

### 9.2 Commands Quick Reference

```bash
# BACKUPS
./scripts/backup_prometheus_advanced.sh    # Prometheus backup
./scripts/backup_grafana_advanced.sh       # Grafana backup
./scripts/backup_application.sh            # Application backup

# RESTORE
./scripts/restore_prometheus.sh latest     # Restore Prometheus
./scripts/restore_grafana.sh latest        # Restore Grafana
./scripts/restore_application.sh latest    # Restore application
./scripts/restore_point_in_time.sh "DATE"  # Point-in-time

# DISASTER RECOVERY
./scripts/recover_database_corruption.sh   # DB corruption
./scripts/recover_ransomware.sh            # Ransomware

# TESTING
./scripts/test_backup_restore.sh           # Validate backups
./scripts/dr_drill.sh [type]              # DR drill
./scripts/check_backup_health.sh           # Health check
./scripts/verify_recovery.sh               # Verify recovery

# MONITORING
curl http://localhost:3000/d/backup-health # Backup dashboard
curl http://localhost:9090/graph           # Prometheus
```

### 9.3 Cron Schedule

```cron
# Backups
5 * * * * backup_prometheus_advanced.sh    # Hourly
10 * * * * backup_application.sh           # Hourly
0 3 * * * backup_grafana_advanced.sh       # Daily 03:00

# Testing
0 4 * * * test_backup_restore.sh           # Daily 04:00
0 * * * * check_backup_health.sh           # Every 4 hours

# DR Drills
0 2 * * 6 dr_drill.sh prometheus          # Weekly (Sat)
0 2 1-7 * 0 dr_drill.sh grafana           # Monthly (1st Sun)
```

### 9.4 Important URLs

- **Backup Dashboard:** http://localhost:3000/d/backup-health
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000
- **Application Health:** http://localhost:8080/health
- **S3 Bucket:** https://s3.console.aws.amazon.com/s3/buckets/mcp-backups

### 9.5 Support Contacts

- **Primary On-Call:** [PagerDuty rotation]
- **Backup Team Lead:** [Name] - [Email]
- **AWS Support:** [Support plan details]
- **Vendor Support:** [If applicable]

---

## APPENDICES

### Appendix A: Backup Script Reference

See individual scripts in `/opt/mcp-memory-server/scripts/` with inline documentation.

### Appendix B: Disaster Recovery Templates

- DR Drill Report Template
- Incident Response Template
- Post-Mortem Template

### Appendix C: Compliance & Audit

- Backup audit logs
- Access logs
- Retention compliance
- Encryption standards

---

**Handbook Version:** 1.0  
**Last Updated:** 2025-01-08  
**Next Review:** 2025-04-08  
**Maintained By:** DevOps Team

**Document Status:** ✅ APPROVED FOR PRODUCTION USE
