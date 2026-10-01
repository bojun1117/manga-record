#!/bin/bash
# 每日備份：pg_dump（custom 格式，已壓縮）直接串流上傳到 S3。由 /etc/cron.d/manga-record-backup 呼叫。
set -euo pipefail

# shellcheck source=/dev/null
source /opt/manga-record/config.env
KEY="db/manga_record-$(date -u +%Y-%m-%dT%H%M%SZ).dump"

echo "=== backup $(date -u +%FT%TZ) → s3://$BACKUP_BUCKET/$KEY ==="
docker exec manga-record-postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  | aws s3 cp --region "$REGION" - "s3://$BACKUP_BUCKET/$KEY"

SIZE=$(aws s3api head-object --region "$REGION" --bucket "$BACKUP_BUCKET" --key "$KEY" --query ContentLength --output text)
if [ "$SIZE" -lt 100 ]; then
  echo "backup looks empty ($SIZE bytes)" >&2
  exit 1
fi
echo "backup done ($SIZE bytes)"
