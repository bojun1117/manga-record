#!/bin/bash
# EC2 主機一次性設定（可重複執行）：cron、swap、docker compose、Postgres 資料夾、備份排程。
# 新機器由 user_data 執行；既有機器透過 SSM 手動執行一次。
set -euo pipefail

COMPOSE_VERSION="v2.40.3"

# cron：Amazon Linux 2023 預設沒有
dnf install -y cronie
systemctl enable --now crond

# 1GB swap：t3.micro 只有 1GB 記憶體，避免同時跑後端和 Postgres 時被 OOM 砍掉
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap defaults 0 0' >> /etc/fstab
fi

# docker compose plugin：Amazon Linux 2023 的 docker 套件沒有附
if ! docker compose version >/dev/null 2>&1; then
  mkdir -p /usr/local/lib/docker/cli-plugins
  curl -fsSL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi

mkdir -p /opt/manga-record /var/lib/manga-record/pgdata

# 每天 UTC 17:00（台灣凌晨 1 點）備份；EC2 每天台灣 02:00–16:00 關機，備份要在關機前跑
cat > /etc/cron.d/manga-record-backup <<'CRON'
0 17 * * * root /opt/manga-record/backup.sh >> /var/log/manga-record-backup.log 2>&1
CRON
chmod 644 /etc/cron.d/manga-record-backup

echo "setup-host done: $(docker compose version)"
