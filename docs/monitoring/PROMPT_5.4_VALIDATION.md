# VALIDATION PROMPT 5.4: Full DR Drill Validation

## 🎯 Objective
Validate the execution of the full disaster recovery drill, ensuring all procedures were followed correctly, metrics were captured, and the drill met its objectives.

## ✅ Pre-Validation Checklist

### Prerequisites
- [ ] Drill has been completed
- [ ] All drill logs collected
- [ ] Drill report drafted
- [ ] Team debrief conducted
- [ ] Issues logged

### Required Documents
- [ ] `drill_log.txt` - Complete execution log
- [ ] `verification_results.txt` - Verification output
- [ ] `instance_info.json` - Infrastructure details
- [ ] Phase timing records
- [ ] Issue log completed
- [ ] Team notes/feedback

### Evidence Required
- [ ] Start/end time photographs
- [ ] Screenshots of restored systems
- [ ] Log file archives
- [ ] Command history
- [ ] Video recordings (if available)

## 🧪 Validation Steps

### Step 1: Verify Drill Execution

#### 1.1 Check Drill Completion

```bash
# Check if drill log exists
if [ -f "drill_log.txt" ]; then
    echo "✅ Drill log found"
    
    # Check if drill completed
    if grep -q "Phase 3. 5 Complete" drill_log.txt; then
        echo "✅ All phases completed"
    else
        echo "❌ Drill incomplete"
    fi
else
    echo "❌ Drill log not found"
fi

# Check start and end times
START_TIME=$(grep "Phase 1.1 Start:" drill_log.txt | head -1 | awk '{print $4}')
END_TIME=$(grep "Phase 4.3 Complete:" drill_log.txt | tail -1 | awk '{print $4}')

echo "Start: $START_TIME"
echo "End: $END_TIME"
```

**Validation:**
- [ ] Drill log exists and is complete
- [ ] All 5 phases executed
- [ ] Start and end times recorded
- [ ] No critical phases skipped

---

#### 1.2 Verify Team Participation

**Check:**
- [ ] All required roles were filled
- [ ] Drill Commander present throughout
- [ ] Infrastructure Lead completed Phase 1
- [ ] Application Lead completed Phase 2
- [ ] Data Lead completed Phase 3
- [ ] Observer documented throughout

**Documentation:**
```
Drill Commander: _____________ [Present:  ✅/❌]
Infrastructure Lead: __________ [Present: ✅/❌]
Application Lead: _____________ [Present: ✅/❌]
Data Lead: ___________________ [Present: ✅/❌]
Observer: ____________________ [Present: ✅/❌]
```

---

### Step 2: Validate RTO/RPO Metrics

#### 2.1 Calculate RTO (Recovery Time Objective)

```bash
# Extract timestamps from drill log
cat drill_log.txt | grep "Phase.*Start:\|Phase.*Complete:" | \
    awk '{print $2, $3, $4}' > timeline.txt

# Calculate total duration
START=$(grep "Phase 1.1 Start" drill_log.txt | awk '{print $4}')
END=$(grep "Phase 4.3 Complete" drill_log. txt | awk '{print $4}')

# Calculate duration in minutes
# (Manual calculation or use script)
echo "RTO Calculation:"
echo "Start: $START"
echo "End: $END"
echo "Duration: ___ hours ___ minutes"
```

**RTO Validation:**

| Phase | Target Time | Actual Time | Variance | Status |
|-------|-------------|-------------|----------|--------|
| Phase 1: Infrastructure | 60 min | ___ min | ___ min | ⬜ |
| Phase 2: Deployment | 45 min | ___ min | ___ min | ⬜ |
| Phase 3: Data Recovery | 90 min | ___ min | ___ min | ⬜ |
| Phase 4: Verification | 30 min | ___ min | ___ min | ⬜ |
| **Total RTO** | **240 min (4 hr)** | **___ min** | **___ min** | **⬜** |

**Target:** <4 hours (240 minutes)  
**Actual:** ___ hours ___ minutes  
**Met?** ⬜ YES | ⬜ NO

**Analysis:**
```
[If target not met, explain why and what can be improved]
```

---

#### 2.2 Calculate RPO (Recovery Point Objective)

```bash
# Check backup timestamps
echo "Checking backup ages..."

# Prometheus backup age
PROM_BACKUP=$(ls -t /var/backups/mcp-monitoring/prometheus/snapshot_*.tar.gz | head -1)
PROM_AGE=$(stat -c %Y "$PROM_BACKUP")
CURRENT=$(date +%s)
PROM_DATA_LOSS=$(( (CURRENT - PROM_AGE) / 60 ))

echo "Prometheus backup age: $PROM_DATA_LOSS minutes"

# Application backup age
APP_BACKUP=$(ls -t /var/backups/mcp-monitoring/application/app_*.tar.gz | head -1)
APP_AGE=$(stat -c %Y "$APP_BACKUP")
APP_DATA_LOSS=$(( (CURRENT - APP_AGE) / 60 ))

echo "Application backup age: $APP_DATA_LOSS minutes"

# Grafana backup age
GRAFANA_BACKUP=$(ls -t /var/backups/mcp-monitoring/grafana/grafana_*.tar.gz | head -1)
GRAFANA_AGE=$(stat -c %Y "$GRAFANA_BACKUP")
GRAFANA_DATA_LOSS=$(( (CURRENT - GRAFANA_AGE) / 60 ))

echo "Grafana backup age: $GRAFANA_DATA_LOSS minutes"
```

**RPO Validation:**

| Component | Target RPO | Backup Age | Data Loss | Status |
|-----------|------------|------------|-----------|--------|
| Prometheus | <15 min | ___ min | ___ min | ⬜ |
| Application | <15 min | ___ min | ___ min | ⬜ |
| Grafana | <24 hours | ___ min | ___ min | ⬜ |

**Overall RPO Target:** <1 hour  
**Actual (worst case):** ___ minutes  
**Met?** ⬜ YES | ⬜ NO

**Analysis:**
```
[Document data loss and acceptability]
```

---

### Step 3: Validate System Recovery

#### 3.1 Infrastructure Validation

```bash
echo "🔍 Validating Infrastructure..."

# Check if server is running
if aws ec2 describe-instances --instance-ids $INSTANCE_ID \
   --query 'Reservations[0].Instances[0].State. Name' --output text | grep -q "running"; then
    echo "✅ Server is running"
else
    echo "❌ Server not running"
fi

# Check instance type
INSTANCE_TYPE=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].InstanceType' --output text)

if [ "$INSTANCE_TYPE" = "t3.xlarge" ]; then
    echo "✅ Correct instance type"
else
    echo "⚠️ Instance type:  $INSTANCE_TYPE (expected t3.xlarge)"
fi

# Check storage
VOLUME_SIZE=$(aws ec2 describe-volumes \
    --filters "Name=attachment.instance-id,Values=$INSTANCE_ID" \
    --query 'Volumes[0]. Size' --output text)

if [ "$VOLUME_SIZE" -ge 100 ]; then
    echo "✅ Sufficient storage:  ${VOLUME_SIZE}GB"
else
    echo "❌ Insufficient storage: ${VOLUME_SIZE}GB"
fi

# Check network connectivity
ssh -i dr-drill-key.pem ubuntu@$PUBLIC_IP "echo '✅ SSH connectivity OK'"
```

**Validation:**
- [ ] Server provisioned correctly
- [ ] Correct instance type
- [ ] Sufficient storage (≥100GB)
- [ ] SSH connectivity working
- [ ] All required ports open

---

#### 3.2 Application Deployment Validation

```bash
echo "🔍 Validating Application Deployment..."

# Check Docker
ssh -i dr-drill-key. pem ubuntu@$PUBLIC_IP "docker --version"

# Check containers running
CONTAINERS=$(ssh -i dr-drill-key. pem ubuntu@$PUBLIC_IP "docker ps --format '{{. Names}}'")

echo "Running containers:"
echo "$CONTAINERS"

# Expected containers
EXPECTED_CONTAINERS=(
    "mcp-memory-server"
    "prometheus"
    "grafana"
    "redis"
    "alertmanager"
)

for container in "${EXPECTED_CONTAINERS[@]}"; do
    if echo "$CONTAINERS" | grep -q "$container"; then
        echo "✅ $container running"
    else
        echo "❌ $container not running"
    fi
done

# Check container health
ssh -i dr-drill-key. pem ubuntu@$PUBLIC_IP \
    "docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

**Validation:**
- [ ] Docker installed and running
- [ ] All 5 containers running
- [ ] All containers healthy
- [ ] No container restart loops

---

#### 3.3 Data Recovery Validation

```bash
echo "🔍 Validating Data Recovery..."

# Prometheus data validation
echo "Checking Prometheus..."
PROM_DATA_POINTS=$(curl -s 'http://'$PUBLIC_IP':9090/api/v1/query? query=up' | \
    jq '. data.result | length')

if [ "$PROM_DATA_POINTS" -gt 0 ]; then
    echo "✅ Prometheus has data:  $PROM_DATA_POINTS time series"
else
    echo "❌ Prometheus has no data"
fi

# Check data time range
OLDEST_DATA=$(curl -s 'http://'$PUBLIC_IP':9090/api/v1/query? query=up' | \
    jq -r '.data.result[0].value[0]')
OLDEST_DATE=$(date -d "@$OLDEST_DATA" '+%Y-%m-%d %H:%M:%S')
echo "Oldest data point: $OLDEST_DATE"

# Grafana dashboards validation
echo "Checking Grafana..."
DASHBOARD_COUNT=$(curl -s -u admin:$GRAFANA_PASSWORD \
    http://$PUBLIC_IP:3000/api/search | jq '. | length')

if [ "$DASHBOARD_COUNT" -gt 0 ]; then
    echo "✅ Grafana has $DASHBOARD_COUNT dashboards"
else
    echo "❌ Grafana has no dashboards"
fi

# Application database validation
echo "Checking Application Database..."
TABLE_COUNT=$(ssh -i dr-drill-key. pem ubuntu@$PUBLIC_IP \
    "docker exec mcp-memory-server sqlite3 /app/data/memory.db \
    'SELECT COUNT(*) FROM sqlite_master WHERE type=\"table\";'")

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "✅ Database has $TABLE_COUNT tables"
else
    echo "❌ Database has no tables"
fi

# Database integrity check
INTEGRITY=$(ssh -i dr-drill-key.pem ubuntu@$PUBLIC_IP \
    "docker exec mcp-memory-server sqlite3 /app/data/memory.db 'PRAGMA integrity_check;'")

if [ "$INTEGRITY" = "ok" ]; then
    echo "✅ Database integrity OK"
else
    echo "❌ Database integrity check failed"
fi
```

**Validation:**
- [ ] Prometheus has data (>0 time series)
- [ ] Data age matches backup age
- [ ] Grafana dashboards restored
- [ ] Application database restored
- [ ] Database integrity verified
- [ ] ChromaDB data present

---

### Step 4: Validate Functional Testing

#### 4.1 Service Health Checks

```bash
echo "🔍 Running Service Health Checks..."

# Application health
APP_HEALTH=$(curl -s http://$PUBLIC_IP:8080/health | jq -r '.status')
if [ "$APP_HEALTH" = "healthy" ]; then
    echo "✅ Application healthy"
else
    echo "❌ Application unhealthy:  $APP_HEALTH"
fi

# Prometheus health
if curl -sf http://$PUBLIC_IP:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus healthy"
else
    echo "❌ Prometheus unhealthy"
fi

# Grafana health
GRAFANA_HEALTH=$(curl -s http://$PUBLIC_IP:3000/api/health | jq -r '. database')
if [ "$GRAFANA_HEALTH" = "ok" ]; then
    echo "✅ Grafana healthy"
else
    echo "❌ Grafana unhealthy"
fi

# Redis health
if ssh -i dr-drill-key. pem ubuntu@$PUBLIC_IP "docker exec redis redis-cli ping" | grep -q "PONG"; then
    echo "✅ Redis healthy"
else
    echo "❌ Redis unhealthy"
fi

# Alertmanager health
if curl -sf http://$PUBLIC_IP:9093/-/healthy > /dev/null; then
    echo "✅ Alertmanager healthy"
else
    echo "❌ Alertmanager unhealthy"
fi
```

**Validation:**
- [ ] Application health check passes
- [ ] Prometheus health check passes
- [ ] Grafana health check passes
- [ ] Redis health check passes
- [ ] Alertmanager health check passes

---

#### 4.2 Metrics Collection Validation

```bash
echo "🔍 Validating Metrics Collection..."

# Check metrics endpoint
METRICS=$(curl -s http://$PUBLIC_IP:8080/metrics)

# Check for key metrics
REQUIRED_METRICS=(
    "mcp_journal_sessions_total"
    "mcp_journal_sessions_active"
    "mcp_db_connections_active"
    "mcp_vector_memory_count"
    "mcp_system_memory_usage_bytes"
)

for metric in "${REQUIRED_METRICS[@]}"; do
    if echo "$METRICS" | grep -q "$metric"; then
        VALUE=$(echo "$METRICS" | grep "^$metric" | awk '{print $2}')
        echo "✅ $metric: $VALUE"
    else
        echo "❌ $metric:  NOT FOUND"
    fi
done

# Check Prometheus is scraping
TARGETS=$(curl -s http://$PUBLIC_IP:9090/api/v1/targets | \
    jq '. data. activeTargets[] | {job: .labels.job, health: .health}')

echo "Prometheus targets:"
echo "$TARGETS"
```

**Validation:**
- [ ] Metrics endpoint responding
- [ ] All key metrics present
- [ ] Metric values are reasonable
- [ ] Prometheus scraping successfully
- [ ] No scrape errors

---

#### 4.3 Dashboard Validation

```bash
echo "🔍 Validating Grafana Dashboards..."

# List all dashboards
DASHBOARDS=$(curl -s -u admin:$GRAFANA_PASSWORD \
    http://$PUBLIC_IP:3000/api/search | \
    jq -r '.[] | "\(.title) (uid: \(.uid))"')

echo "Restored dashboards:"
echo "$DASHBOARDS"

# Check specific dashboard loads
DASHBOARD_UID="journal-overview"
DASHBOARD_DATA=$(curl -s -u admin: $GRAFANA_PASSWORD \
    http://$PUBLIC_IP:3000/api/dashboards/uid/$DASHBOARD_UID)

if echo "$DASHBOARD_DATA" | jq -e '.dashboard.title' > /dev/null; then
    TITLE=$(echo "$DASHBOARD_DATA" | jq -r '.dashboard. title')
    PANEL_COUNT=$(echo "$DASHBOARD_DATA" | jq '. dashboard.panels | length')
    echo "✅ Dashboard '$TITLE' loaded with $PANEL_COUNT panels"
else
    echo "❌ Dashboard not found"
fi

# Check datasource
DATASOURCES=$(curl -s -u admin: $GRAFANA_PASSWORD \
    http://$PUBLIC_IP:3000/api/datasources | \
    jq -r '. [] | "\(.name) (\(.type))"')

echo "Configured datasources:"
echo "$DATASOURCES"
```

**Validation:**
- [ ] Expected number of dashboards restored
- [ ] Key dashboards load successfully
- [ ] Dashboards show data (not "No Data")
- [ ] Datasources configured correctly
- [ ] Prometheus datasource working

---

### Step 5: Validate Documentation

#### 5.1 Check Drill Documentation

```bash
echo "🔍 Validating Drill Documentation..."

# Check required files exist
REQUIRED_FILES=(
    "drill_log.txt"
    "verification_results.txt"
    "instance_info.json"
    "timeline.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(du -h "$file" | cut -f1)
        echo "✅ $file ($SIZE)"
    else
        echo "❌ $file NOT FOUND"
    fi
done

# Check log completeness
if grep -q "Phase 1.1 Start" drill_log.txt && \
   grep -q "Phase 4.3 Complete" drill_log.txt; then
    echo "✅ Drill log complete"
else
    echo "❌ Drill log incomplete"
fi

# Count log entries
LOG_ENTRIES=$(grep -c "Phase.*Start:\|Phase.*Complete:" drill_log.txt)
echo "Log entries: $LOG_ENTRIES (expected: ~30)"
```

**Validation:**
- [ ] All required files present
- [ ] Drill log complete
- [ ] Verification results captured
- [ ] Infrastructure details documented
- [ ] Timeline extracted

---

#### 5.2 Check Issue Documentation

```bash
echo "🔍 Checking Issue Documentation..."

# Count issues logged
if [ -f "dr-drill-plan.md" ]; then
    ISSUES=$(grep -c "^| [0-9]" dr-drill-plan.md)
    echo "Issues documented: $ISSUES"
    
    # List issues
    grep "^| [0-9]" dr-drill-plan.md
else
    echo "⚠️ Drill plan not found"
fi
```

**Validation:**
- [ ] Issues log section filled out
- [ ] Each issue has description
- [ ] Impact assessed
- [ ] Resolution status documented
- [ ] Notes provided

---

### Step 6: Validate Playbook Accuracy

#### 6.1 Compare Actual vs Planned

```bash
echo "🔍 Validating Playbook Accuracy..."

# Check if steps matched playbook
echo "Comparing executed steps to playbook..."

# List deviations (manual review)
echo "Deviations from playbook:"
echo "1. [List any steps not in playbook]"
echo "2. [List any steps that didn't work as documented]"
echo "3. [List any additional steps required]"
```

**Validation Questions:**
- [ ] Were all playbook steps executable?
- [ ] Were there any missing steps?
- [ ] Were any steps unclear?
- [ ] Were any steps incorrect?
- [ ] Did team need external help?

**Playbook Accuracy Score:**
- Steps followed exactly: ___ / ___
- Steps needing clarification: ___
- Steps needing changes: ___
- Missing steps: ___

**Overall Playbook Rating:** ⬜ Excellent | ⬜ Good | ⬜ Needs Improvement | ⬜ Major Revisions Needed

---

### Step 7: Automated Validation Script

**File:** `scripts/validate_dr_drill.sh`

```bash
#!/bin/bash
#
# Automated DR Drill Validation
#

set -e

echo "🔍 Validating DR Drill Results"
echo "=============================="
echo ""

FAILED=0

# Test 1: Check drill completion
echo "Test 1: Drill Completion"
if [ -f "drill_log.txt" ]; then
    if grep -q "Phase 4.3 Complete" drill_log.txt; then
        echo "✅ Drill completed all phases"
    else
        echo "❌ Drill incomplete"
        ((FAILED++))
    fi
else
    echo "❌ Drill log not found"
    ((FAILED++))
fi
echo ""

# Test 2: Check RTO
echo "Test 2: RTO Validation"
if [ -f "drill_log.txt" ]; then
    START=$(grep "Phase 1.1 Start:" drill_log.txt | head -1 | awk '{print $4}')
    END=$(grep "Phase 4.3 Complete:" drill_log.txt | tail -1 | awk '{print $4}')
    
    # Calculate duration (manual or script)
    echo "Start: $START"
    echo "End: $END"
    echo "⚠️ Manual RTO calculation required"
    echo "Target: <4 hours"
fi
echo ""

# Test 3: Check services
echo "Test 3: Service Health"
if [ -n "$PUBLIC_IP" ]; then
    if curl -sf http://$PUBLIC_IP:8080/health > /dev/null; then
        echo "✅ Application healthy"
    else
        echo "❌ Application unhealthy"
        ((FAILED++))
    fi
    
    if curl -sf http://$PUBLIC_IP:9090/-/healthy > /dev/null; then
        echo "✅ Prometheus healthy"
    else
        echo "❌ Prometheus unhealthy"
        ((FAILED++))
    fi
else
    echo "⚠️ PUBLIC_IP not set, skipping service checks"
fi
echo ""

# Test 4: Check data restoration
echo "Test 4: Data Validation"
if [ -n "$PUBLIC_IP" ]; then
    DATA_POINTS=$(curl -s "http://$PUBLIC_IP:9090/api/v1/query?query=up" | \
        jq '.data.result | length' 2>/dev/null || echo 0)
    
    if [ "$DATA_POINTS" -gt 0 ]; then
        echo "✅ Prometheus has data: $DATA_POINTS time series"
    else
        echo "❌ Prometheus has no data"
        ((FAILED++))
    fi
fi
echo ""

# Test 5: Check documentation
echo "Test 5: Documentation"
REQUIRED_FILES=(
    "drill_log.txt"
    "verification_results.txt"
    "instance_info.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file present"
    else
        echo "❌ $file missing"
        ((FAILED++))
    fi
done
echo ""

echo "=============================="

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL VALIDATIONS PASSED"
    exit 0
else
    echo "❌ $FAILED VALIDATIONS FAILED"
    exit 1
fi
```

Make executable:
```bash
chmod +x scripts/validate_dr_drill. sh
```

---

## 📊 Validation Checklist

### Drill Execution
- [ ] All phases completed
- [ ] All team members participated
- [ ] Official times recorded
- [ ] All steps documented

### RTO/RPO Metrics
- [ ] RTO calculated accurately
- [ ] RTO target met (<4 hours)
- [ ] RPO calculated for all components
- [ ] RPO target met (<1 hour)
- [ ] Variances explained

### System Recovery
- [ ] Infrastructure provisioned correctly
- [ ] All services deployed
- [ ] All containers running
- [ ] All data restored
- [ ] Database integrity verified

### Functional Validation
- [ ] All health checks pass
- [ ] Metrics collecting
- [ ] Prometheus has data
- [ ] Grafana dashboards work
- [ ] Application functional

### Documentation
- [ ] Drill log complete
- [ ] Verification results captured
- [ ] Issues documented
- [ ] Evidence collected
- [ ] Playbook accuracy assessed

### Team Feedback
- [ ] Debrief conducted
- [ ] Feedback documented
- [ ] Lessons learned captured
- [ ] Improvements identified

---

## 📈 Validation Report Template

```markdown
# DR Drill Validation Report

**Drill Date:** [DATE]
**Validator:** [NAME]
**Validation Date:** [DATE]

## Executive Summary

- Drill Status: ⬜ PASSED | ⬜ PASSED WITH ISSUES | ⬜ FAILED
- RTO Target Met: ⬜ YES | ⬜ NO
- RPO Target Met: ⬜ YES | ⬜ NO
- System Recovered: ⬜ FULLY | ⬜ PARTIALLY | ⬜ NOT RECOVERED

## Metrics

- **RTO:** ___ hours ___ minutes (Target: <4 hours)
- **RPO:** ___ minutes (Target: <60 minutes)
- **Success Rate:** ___%

## Validation Results

| Category | Status | Notes |
|----------|--------|-------|
| Drill Execution | ⬜ PASS ⬜ FAIL | |
| RTO/RPO | ⬜ PASS ⬜ FAIL | |
| System Recovery | ⬜ PASS ⬜ FAIL | |
| Functional Tests | ⬜ PASS ⬜ FAIL | |
| Documentation | ⬜ PASS ⬜ FAIL | |

## Issues Found

[List all issues with severity]

## Recommendations

[List improvements needed]

## Sign-Off

**Validated By:** _______________ Date: _______
**Approved By:** _______________ Date: _______
```

---

## ✅ Sign-Off

**Validation Status:** ⬜ Complete | ⬜ Issues Found

**Validation Results:**
```
Drill Execution:      [✅/❌]
RTO Met:            [✅/❌]
RPO Met:            [✅/❌]
System Recovery:     [✅/❌]
Functional Tests:   [✅/❌]
Documentation:       [✅/❌]
```

**Overall Assessment:** ⬜ PASSED | ⬜ PASSED WITH ISSUES | ⬜ FAILED

**Validated By:** ________________  
**Date:** ________________  
**Approved:** ⬜ YES | ⬜ NO
```

---
