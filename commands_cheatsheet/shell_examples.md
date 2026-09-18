# Production Shell Script Examples

> Real-world automation shell scripts for log cleanup, S3 backups, container restarts, and system health alerting.

## 1. Automated System Health & High CPU/Memory Alerting Script
**Description**: Monitors system CPU, memory, and disk usage against configurable thresholds and sends automated alert webhooks when thresholds are exceeded.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Thresholds
CPU_THRESHOLD=85
MEM_THRESHOLD=85
DISK_THRESHOLD=90
WEBHOOK_URL="${SLACK_WEBHOOK_URL:-https://hooks.slack.com/services/T00/B00/X00}"

# 1. Check CPU Usage
CPU_IDLE=$(top -b -n 1 | grep "Cpu(s)" | awk '{print $8}' | cut -d. -f1)
CPU_USAGE=$((100 - CPU_IDLE))

# 2. Check Memory Usage
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", ($3/$2) * 100)}')

# 3. Check Root Disk Usage
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')

ALERT_MSG=""
if [ "$CPU_USAGE" -ge "$CPU_THRESHOLD" ]; then
  ALERT_MSG="⚠️ High CPU: ${CPU_USAGE}% (Threshold: ${CPU_THRESHOLD}%)\n"
fi

if [ "$MEM_USAGE" -ge "$MEM_THRESHOLD" ]; then
  ALERT_MSG="${ALERT_MSG}⚠️ High Memory: ${MEM_USAGE}% (Threshold: ${MEM_THRESHOLD}%)\n"
fi

if [ "$DISK_USAGE" -ge "$DISK_THRESHOLD" ]; then
  ALERT_MSG="${ALERT_MSG}🚨 Critical Disk: ${DISK_USAGE}% (Threshold: ${DISK_THRESHOLD}%)\n"
fi

if [ -n "$ALERT_MSG" ]; then
  HOSTNAME=$(hostname -f)
  PAYLOAD="{\"text\": \"*[ALERT]* Host: ${HOSTNAME}\n${ALERT_MSG}\"}"
  curl -s -X POST -H 'Content-type: application/json' --data "$PAYLOAD" "$WEBHOOK_URL"
  echo "Alert sent: $ALERT_MSG"
else
  echo "All systems healthy: CPU=${CPU_USAGE}%, MEM=${MEM_USAGE}%, DISK=${DISK_USAGE}%"
fi
```

## 2. Automated PostgreSQL Database Backup to AWS S3 with Retention
**Description**: Dumps a PostgreSQL database, gzips the dump, uploads to an S3 bucket, and purges local backups older than 7 days.

```bash
#!/usr/bin/env bash
set -euo pipefail

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="${1:-app_production}"
DB_USER="${2:-postgres}"
S3_BUCKET="${S3_BUCKET:-s3://my-company-database-backups}"
BACKUP_DIR="/var/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup of ${DB_NAME}..."
PGPASSWORD="${PGPASSWORD}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "[$(date)] Uploading ${BACKUP_FILE} to ${S3_BUCKET}..."
aws s3 cp "$BACKUP_FILE" "${S3_BUCKET}/$(date +%Y)/$(date +%m)/" --storage-class STANDARD_IA

echo "[$(date)] Purging local backups older than 7 days..."
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +7 -delete

echo "[$(date)] Backup completed successfully."
```

## 3. Log Rotation & Purge Script for Docker Application Logs
**Description**: Truncates and compresses large application logs without restarting containers or dropping active write file descriptors.

```bash
#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="/var/log/containers"
MAX_SIZE_MB=500
DAYS_TO_KEEP=14

echo "Scanning for logs exceeding ${MAX_SIZE_MB}MB..."
find "$LOG_DIR" -type f -name "*.log" -size +"${MAX_SIZE_MB}"M | while read -r logfile; do
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  ARCHIVE="${logfile}.${TIMESTAMP}.gz"
  
  echo "Rotating $logfile -> $ARCHIVE"
  # Copy content and truncate in-place preserving file descriptor
  cp "$logfile" "${logfile}.tmp"
  : > "$logfile"
  gzip -c "${logfile}.tmp" > "$ARCHIVE"
  rm -f "${logfile}.tmp"
done

echo "Purging archives older than ${DAYS_TO_KEEP} days..."
find "$LOG_DIR" -type f -name "*.log.*.gz" -mtime +"$DAYS_TO_KEEP" -delete
echo "Log rotation finished."
```
