#!/bin/bash
set -uo pipefail
exec >> /var/log/manga-record-init.log 2>&1
echo "=== init $(date -u +%FT%TZ) ==="

dnf install -y docker jq unzip amazon-ssm-agent
systemctl enable --now docker
systemctl enable --now amazon-ssm-agent

if ! command -v aws >/dev/null 2>&1; then
  curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp
  /tmp/aws/install
fi

mkdir -p /opt/manga-record

# 非機密設定，deploy.sh / backup.sh 都從這裡讀
cat > /opt/manga-record/config.env <<'CONFIG'
REGION="${region}"
ECR_REPO="${ecr_repo_url}"
APP_PORT="${app_port}"
DB_SECRET_ID="${db_secret_id}"
JWT_SECRET_ID="${jwt_secret_id}"
ANTHROPIC_SECRET_ID="${anthropic_secret_id}"
BACKUP_BUCKET="${backup_bucket}"
CONFIG

# 下面四個檔案的內容來自 repo 的 infra/ec2/（base64 傳入，避免跳脫問題）
echo "${setup_host_sh}" | base64 -d > /opt/manga-record/setup-host.sh
echo "${deploy_sh}" | base64 -d > /opt/manga-record/deploy.sh
echo "${backup_sh}" | base64 -d > /opt/manga-record/backup.sh
echo "${compose_yml}" | base64 -d > /opt/manga-record/compose.yml
chmod +x /opt/manga-record/setup-host.sh /opt/manga-record/deploy.sh /opt/manga-record/backup.sh

/opt/manga-record/setup-host.sh

/opt/manga-record/deploy.sh || echo "initial deploy failed (expected if no image pushed yet) — see /var/log/manga-record-deploy.log"
