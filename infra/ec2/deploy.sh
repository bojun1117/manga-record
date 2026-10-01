#!/bin/bash
# 換版：從 Secrets Manager 產生 .env，拉最新後端 image，跑 migration，用 compose 重建後端容器。
# Postgres 容器不會因為換版而重啟。GitHub Actions 透過 SSM 執行：sudo /opt/manga-record/deploy.sh
set -euo pipefail
exec >> /var/log/manga-record-deploy.log 2>&1
echo "=== deploy $(date -u +%FT%TZ) ==="

DIR=/opt/manga-record
# shellcheck source=/dev/null
source "$DIR/config.env"
cd "$DIR"

aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${ECR_REPO%%/*}"

DB_JSON=$(aws secretsmanager get-secret-value --region "$REGION" --secret-id "$DB_SECRET_ID" --query SecretString --output text)
JWT_SECRET=$(aws secretsmanager get-secret-value --region "$REGION" --secret-id "$JWT_SECRET_ID" --query SecretString --output text)
ANTHROPIC_API_KEY=$(aws secretsmanager get-secret-value --region "$REGION" --secret-id "$ANTHROPIC_SECRET_ID" --query SecretString --output text)

umask 077
cat > "$DIR/.env" <<ENV
DB_USER=$(echo "$DB_JSON" | jq -r .username)
DB_PASS=$(echo "$DB_JSON" | jq -r .password)
DB_NAME=$(echo "$DB_JSON" | jq -r .dbname)
ECR_REPO=$ECR_REPO
APP_PORT=$APP_PORT
JWT_SECRET=$JWT_SECRET
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
ENV
umask 022

# 舊版 deploy.sh 用 docker run 建的後端容器沒有 compose 標籤，要先移除，compose 才能用同名容器
if docker inspect manga-record-backend >/dev/null 2>&1 \
  && [ -z "$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' manga-record-backend)" ]; then
  echo "removing legacy backend container..."
  docker rm -f manga-record-backend
fi

docker compose pull backend
docker compose up -d --wait postgres

echo "running migration..."
docker compose run --rm --no-deps backend alembic upgrade head

echo "starting backend..."
docker compose up -d --no-deps backend
docker image prune -f >/dev/null

echo "deploy done"
