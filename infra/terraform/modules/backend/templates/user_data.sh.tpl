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

cat > /opt/manga-record/deploy.sh <<'DEPLOY_SCRIPT'
#!/bin/bash
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

/opt/manga-record/deploy.sh || echo "initial deploy failed (expected if no image pushed yet) — see /var/log/manga-record-deploy.log"
