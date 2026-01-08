#!/bin/bash
# Point-in-time recovery across Prometheus, application, and Grafana

set -euo pipefail

TARGET_TS=${1:-}
[ -n "$TARGET_TS" ] || { echo "Usage: $0 'YYYY-MM-DD HH:MM:SS'"; exit 1; }

TARGET_EPOCH=$(date -d "$TARGET_TS" +%s 2>/dev/null || echo "")
[ -n "$TARGET_EPOCH" ] || { echo "Invalid timestamp"; exit 1; }

echo "🕐 Point-in-time recovery to $TARGET_TS"

target_backup() {
  local dir=$1 pattern=$2
  local best="" best_diff=999999999
  while IFS= read -r file; do
    ts=$(echo "$file" | grep -oE '[0-9]{8}_[0-9]{6}' | head -1)
    [ -n "$ts" ] || continue
    ts_fmt=$(echo "$ts" | sed 's/_/ /')
    ts_fmt=$(echo "$ts_fmt" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\) \([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')
    epoch=$(date -d "$ts_fmt" +%s 2>/dev/null || echo 0)
    [ "$epoch" -gt 0 ] || continue
    diff=$((TARGET_EPOCH - epoch))
    diff=${diff#-}
    if [ "$diff" -lt "$best_diff" ]; then
      best_diff=$diff
      best=$file
    fi
  done < <(find "$dir" -name "$pattern" -type f)
  echo "$best"
}

PROM_BKP=$(target_backup "/var/backups/mcp-monitoring/prometheus" "snapshot_*.tar.gz")
APP_BKP=$(target_backup "/var/backups/mcp-monitoring/application" "app_*.tar.gz")
GRAF_BKP=$(target_backup "/var/backups/mcp-monitoring/grafana" "grafana_*.tar.gz")

echo "Selected backups:"
echo "  Prometheus: ${PROM_BKP:-none}"
echo "  Application: ${APP_BKP:-none}"
echo "  Grafana: ${GRAF_BKP:-none}"

read -r -p "Proceed with restore? [y/N]: " CONFIRM
[[ $CONFIRM =~ ^[Yy]$ ]] || { echo "Cancelled"; exit 0; }

[ -n "$PROM_BKP" ] && ./scripts/restore_prometheus.sh "$PROM_BKP"
[ -n "$APP_BKP" ] && ./scripts/restore_application.sh "$APP_BKP"
[ -n "$GRAF_BKP" ] && ./scripts/restore_grafana.sh "$GRAF_BKP"

echo "✅ Point-in-time recovery complete"
