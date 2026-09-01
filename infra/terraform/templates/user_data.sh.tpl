#!/bin/bash
# EC2 開機執行一次(cloud-init)。裝好 docker/aws cli/jq,把 deploy.sh 寫到機器上,
# 然後嘗試跑一次。之後要換新版 image,SSM 連進來重跑 /opt/manga-record/deploy.sh 就好,
# 不用重開機、不用重新 apply。
set -uo pipefail
exec >> /var/log/manga-record-init.log 2>&1
echo "=== init $(date -u +%FT%TZ) ==="

# 故意不做 `dnf update -y`(全套件更新),只裝真正需要的套件,降低對系統既有服務的干擾。
#
# amazon-ssm-agent 特地手動裝、手動啟用——踩過的坑:這個 AMI 實際上沒有預裝
# amazon-ssm-agent(跟一般認知的「AL2023 內建 SSM Agent」不一樣,實測用
# AWSSupport-TroubleshootManagedInstance 診斷過,網路/security group/NACL/IAM 全部
# PASS,但 instance 一直不是 managed instance;SSH 進去用 rpm -q 查才發現套件根本沒裝),
# 拿掉這個假設、自己確保裝好啟用,SSM 才會真的能連。
dnf install -y docker jq unzip amazon-ssm-agent
systemctl enable --now docker
systemctl enable --now amazon-ssm-agent

# AL2023 base image 沒內建 aws cli v2,用官方 zip 裝,不依賴套件庫是否有這個包。
if ! command -v aws >/dev/null 2>&1; then
  curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp
  /tmp/aws/install
fi

mkdir -p /opt/manga-record

# 用單引號 heredoc(<<'DEPLOY_SCRIPT'),避免這裡的 bash 在「寫檔當下」就展開裡面的變數——
# 那些變數(DB_USER/DATABASE_URL 等)要等 deploy.sh 之後「真的執行時」才該被展開。
cat > /opt/manga-record/deploy.sh <<'DEPLOY_SCRIPT'
#!/bin/bash
# -e：任何一步失敗（pull 失敗、migration 失敗…）立刻中止，不要繼續往下跑到
# 「換上新 container」那步——CI 會看這支腳本的 exit code 判斷部署成不成功，
# 半途而廢卻印出 exit 0 只會讓 CI 誤判成功。docker stop/rm 兩行本來就用 `|| true`
# 包起來（container 不存在是正常情況，不該讓腳本中止），這裡沒有影響。
set -euo pipefail
exec >> /var/log/manga-record-deploy.log 2>&1
echo "=== deploy $(date -u +%FT%TZ) ==="

REGION="${region}"
ECR_REPO="${ecr_repo_url}"
ECR_REGISTRY="$${ECR_REPO%%/*}"
DB_SECRET_ID="${db_secret_id}"
JWT_SECRET_ID="${jwt_secret_id}"
APP_PORT="${app_port}"
CONTAINER_NAME="manga-record-backend"

aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"

DB_JSON=$(aws secretsmanager get-secret-value --region "$REGION" --secret-id "$DB_SECRET_ID" --query SecretString --output text)
DB_USER=$(echo "$DB_JSON" | jq -r .username)
DB_PASS=$(echo "$DB_JSON" | jq -r .password)
DB_HOST=$(echo "$DB_JSON" | jq -r .host)
DB_PORT=$(echo "$DB_JSON" | jq -r .port)
DB_NAME=$(echo "$DB_JSON" | jq -r .dbname)
DATABASE_URL="postgresql+psycopg://$${DB_USER}:$${DB_PASS}@$${DB_HOST}:$${DB_PORT}/$${DB_NAME}?sslmode=require"

JWT_SECRET=$(aws secretsmanager get-secret-value --region "$REGION" --secret-id "$JWT_SECRET_ID" --query SecretString --output text)

docker pull "$${ECR_REPO}:latest"

echo "running migration..."
# JWT_SECRET 這裡用不到(migration 只碰 DB)，但一定要傳——app/core/config.py 的 Settings
# 是 pydantic model，少一個必填欄位整個 import 就炸掉(alembic/env.py 會呼叫到
# get_settings())，不會是「沒用到就沒差」。踩坑記錄：一開始漏了這行，migration 直接
# ValidationError 收場，deploy.sh 卡在這步。
docker run --rm \
  --env DATABASE_URL="$DATABASE_URL" \
  --env JWT_SECRET="$JWT_SECRET" \
  "$${ECR_REPO}:latest" alembic upgrade head

echo "swapping container..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER_NAME" --restart unless-stopped \
  -p "$${APP_PORT}:8000" \
  --env DATABASE_URL="$DATABASE_URL" \
  --env JWT_SECRET="$JWT_SECRET" \
  --env ENVIRONMENT=prod \
  "$${ECR_REPO}:latest"

echo "deploy done"
DEPLOY_SCRIPT

chmod +x /opt/manga-record/deploy.sh

# 第一次 apply 時 ECR 通常還沒有 image,這裡失敗是預期的,不影響 EC2 開機。
# push 完 image 之後用 SSM 連進來重跑 /opt/manga-record/deploy.sh。
/opt/manga-record/deploy.sh || echo "initial deploy failed (expected if no image pushed yet) — see /var/log/manga-record-deploy.log"
