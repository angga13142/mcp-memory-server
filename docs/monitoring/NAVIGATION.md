# Documentation Navigation Helper

## 🚀 I want to...

### ...get started quickly

→ README.md#quick-start

### ...deploy to production

→ operator-guide.md#installation

### ...add a new metric

→ developer-guide.md#creating-new-metrics

### ...respond to an alert

→ runbook.md#alert-response-procedures

### ...fix a problem

→ troubleshooting.md

### ...understand the design

→ architecture.md#high-level-architecture

### ...look up a metric

→ api-reference.md#metrics-reference

### ...find a specific topic

→ INDEX.md#search-index

---

## 📱 Mobile-Friendly Quick Links

**On-Call Emergency:**

1. runbook.md#alert-servicedown-🔴-critical
2. runbook.md#escalation-procedures
3. troubleshooting.md#collect-diagnostic-information

**Quick Commands:**

```bash
# Health check
curl http://localhost:8080/health

# View alerts
curl http://localhost:9090/api/v1/alerts

# Restart service
docker-compose restart mcp-memory-server
```

---

Need help navigating? Ask in #mcp-memory-docs
