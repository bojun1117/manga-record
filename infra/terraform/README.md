# Terraform — 網路 / EC2 / CI 基礎設施

管理 manga-record 後端的 AWS 基礎設施：VPC、EC2（後端 + Postgres 容器）、S3（資料庫備份）、Secrets Manager、ECR、GitHub OIDC、CloudFront。

## 架構重點

- **後端和 Postgres 都跑在同一台 EC2 上**，用 docker compose 管理（`infra/ec2/compose.yml`）。Postgres 不對外開 port，只有同一個 Docker 網路裡的後端連得到
- **每天台灣凌晨 1 點備份**：cron 跑 `pg_dump` 上傳到 S3，S3 保留 14 天
- **夜間關機省錢**：EventBridge Scheduler 每天台灣 02:00 關機、16:00 開機（`modules/backend` 的 `ec2_stop_schedule` / `ec2_start_schedule`）。關機期間網站無法使用，GitHub Actions 的部署也會失敗，開機後重跑即可。開機後 Docker 與兩個容器會自動啟動
- **EC2 維運走 AWS Session Manager**，不開 22 port
- DB 密碼、JWT secret、Anthropic API key 都存 **Secrets Manager**，EC2 用 IAM instance profile 讀取

## 模組結構

Root module（`main.tf`）只負責接線，實際資源分在 7 個 child module（`modules/`）。依賴方向無循環：`network` → `database` → `secrets` → `backend` → `{cicd, cdn}`。

- `modules/network`：VPC、public subnet、route table、`aws_security_group.ec2`（對外開 `var.app_port`）
- `modules/database`：只有資料庫密碼（`random_password`）。**這個資源若被重建會產生新密碼，但既有的 Postgres 不會跟著改，後端會連不上**——不要搬動或改它的參數
- `modules/secrets`：Secrets Manager（DB 帳號密碼、JWT secret、Anthropic API key）
- `modules/ecr`：後端 Docker image 的 ECR repo
- `modules/backend`：EC2 的 IAM role + 一台 EC2（Amazon Linux 2023）+ Elastic IP + 資料庫備份的 S3 bucket + 開關機排程。開機時透過 `modules/backend/templates/user_data.sh.tpl` 裝好 docker/aws-cli/jq，把 `infra/ec2/` 的檔案寫到 `/opt/manga-record/`，再跑 `setup-host.sh` 和 `deploy.sh`
- `modules/cicd`：GitHub Actions 用的 OIDC provider + IAM role，權限鎖在「push 到 ECR」+「對 EC2 送 SSM SendCommand」
- `modules/cdn`：CloudFront，把 EC2 的裸 HTTP 包成 HTTPS

EC2 忽略 `ami` 和 `user_data` 的變更：`user_data` 只在第一次開機執行，改了不會套用到既有機器；不忽略的話，AWS 發新 AMI 或改模板都會讓 Terraform 重建或重開 EC2。**改了 `infra/ec2/` 的檔案，要另外手動同步到既有機器上。**

## EC2 上的檔案（`/opt/manga-record/`）

| 檔案 | 來源 | 用途 |
|---|---|---|
| `compose.yml` | `infra/ec2/compose.yml` | Postgres + 後端容器 |
| `deploy.sh` | `infra/ec2/deploy.sh` | 換版（GitHub Actions 透過 SSM 執行） |
| `backup.sh` | `infra/ec2/backup.sh` | 每日備份到 S3（`/etc/cron.d/manga-record-backup` 呼叫） |
| `setup-host.sh` | `infra/ec2/setup-host.sh` | cron、swap、compose plugin、備份排程 |
| `config.env` | `user_data` 產生 | 非機密設定（region、ECR、secret ID、備份 bucket） |
| `.env` | `deploy.sh` 從 Secrets Manager 產生（權限 600） | 密碼等機密設定 |

Postgres 資料放在 `/var/lib/manga-record/pgdata`（EC2 根磁碟）。

## 執行

```powershell
# anthropic_api_key 沒有預設值，從 Secrets Manager 讀進環境變數（不會顯示在畫面上）
$env:TF_VAR_anthropic_api_key = aws secretsmanager get-secret-value --secret-id manga-record/dev/anthropic-api-key --profile terraform-deploy --query SecretString --output text

terraform init
terraform plan
terraform apply
```

## 連進資料庫

```bash
aws ssm start-session --target <ec2_instance_id>
sudo docker exec -it manga-record-postgres psql -U manga_record_admin -d manga_record
```

## 從備份還原

```bash
# 在 EC2 上（Session Manager）
source /opt/manga-record/config.env && source /opt/manga-record/.env
aws s3 ls "s3://$BACKUP_BUCKET/db/" --region "$REGION"                       # 找要還原的檔案
aws s3 cp "s3://$BACKUP_BUCKET/db/<檔名>.dump" /tmp/restore.dump --region "$REGION"

sudo docker compose -f /opt/manga-record/compose.yml stop backend            # 停機開始
sudo docker cp /tmp/restore.dump manga-record-postgres:/tmp/restore.dump
sudo docker exec manga-record-postgres pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner --no-acl /tmp/restore.dump
sudo docker compose -f /opt/manga-record/compose.yml start backend           # 停機結束
```

## 重建 EC2

資料庫在 EC2 的根磁碟上，**重建 EC2 會連資料庫一起刪掉**，要靠 S3 備份還原。

1. 先手動備份一次：`sudo /opt/manga-record/backup.sh`，確認 S3 有最新檔案
2. `terraform apply -replace=module.backend.aws_instance.backend`
3. 新機器開機後 `user_data` 會自動裝好環境、啟動空的 Postgres 和後端
4. 照上面「從備份還原」把資料還原回去
5. 更新 GitHub repo secret `EC2_INSTANCE_ID` 為新機器的 ID（`terraform output ec2_instance_id`），否則之後的部署會失敗
