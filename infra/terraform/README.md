# Terraform — 網路 / RDS / EC2 / CI 基礎設施

管理 manga-record 後端的 AWS 基礎設施：VPC、RDS（Postgres）、Secrets Manager、EC2、ECR、GitHub OIDC。

## 架構重點

- **RDS 在 private subnet**，`publicly_accessible` 關閉，security group 只信任 EC2 的 SG——不對外開放，只能透過 EC2 或臨時開放的方式連線
- **EC2 維運主要走 AWS Session Manager**，平常不開 22 port（見下方「連線維運」）。有留一把本機產生的 SSH key pair（`ec2-ssh-key` / `ec2-ssh-key.pub`，`.gitignore` 排除、不進版控）當 SSM 之外的備援管道，ingress 一樣預設關閉，只在臨時除錯時開
- 資料庫密碼、JWT secret 都存 **Secrets Manager**，EC2 用 IAM instance profile 讀取，不寫死在程式碼或 Terraform 檔案裡

## 模組結構

Root module（`main.tf`）只負責接線，實際資源分在 7 個 child module（`modules/`）。依賴方向刻意排成無循環：`network`（VPC + 兩個 security group）→ `database` → `secrets` → `backend` → `{cicd, cdn}`。RDS 的 security group 需要引用 EC2 的 security group id，所以兩個 security group 一起放在 `network`，避免 `backend` 跟 `database` 兩個 module 互相依賴。

- `modules/network`：VPC、subnet、route table，以及 `aws_security_group.ec2`（對外開 `var.app_port`，預設 `8000`）、`aws_security_group.rds`（只信任 ec2 的 SG）
- `modules/database`：RDS Postgres instance，`aws_db_subnet_group.main` 放在 private subnet
- `modules/secrets`：Secrets Manager（DB 連線字串、JWT secret）
- `modules/ecr`：後端 Docker image 的 ECR repo（`aws_ecr_repository.backend`），附一個清掉沒 tag 舊 image 的生命週期規則
- `modules/backend`：EC2 的 IAM role（`AmazonSSMManagedInstanceCore`、`AmazonEC2ContainerRegistryReadOnly`、自訂的 `secretsmanager:GetSecretValue`，只給兩個 secret 的 ARN）+ 一台 EC2（Amazon Linux 2023）+ 固定 Elastic IP。開機時透過 `modules/backend/templates/user_data.sh.tpl` 裝好 docker/aws-cli/jq，並把 `/opt/manga-record/deploy.sh` 寫到機器上（換新版 image 時要重跑的腳本）
- `modules/cicd`：GitHub Actions 用的 OIDC provider + IAM role，權限鎖在「push 到 ECR 的 backend repo」+「對 backend 那台 EC2 送 SSM SendCommand」兩件事，信任範圍只限 `var.github_repo`（預設 `bojun1117/manga-record`）的 `main` 分支。設定步驟見 [`backend/README.md` 的 CI/CD 段落](../../backend/README.md)
- `modules/cdn`：CloudFront，把 EC2 的裸 HTTP 包成 HTTPS 給前端呼叫

## 連線維運（SSM，不開 22 port）

```powershell
aws ssm start-session --target <ec2_instance_id> --profile terraform-deploy
```

`<ec2_instance_id>` 從 `terraform output ec2_instance_id` 拿。連進去之後（在 EC2 上，是 bash 不是 PowerShell）：

```bash
sudo /opt/manga-record/deploy.sh
tail -f /var/log/manga-record-deploy.log   # 看上次部署的 log
```

## 手動 psql 直連 RDS 除錯

RDS 預設不對外開放。`my_ip_cidr` 這個變數留空時，`aws_security_group_rule.rds_debug` 不會建立，`terraform output psql_connect_hint` 印出來的指令平常連不上。真的需要直連時：

1. `terraform.tfvars` 取消註解 `my_ip_cidr`，填上目前的 IP（`curl -s https://checkip.amazonaws.com`）
2. `terraform plan` 看一下（應該只多一條 ingress 規則）、`terraform apply`
3. 密碼不會直接印在 output 裡（避免留在 terminal 歷史紀錄），從 Secrets Manager 拿：
   ```powershell
   aws secretsmanager get-secret-value `
     --secret-id manga-record/dev/db-credentials `
     --profile terraform-deploy `
     --query SecretString --output text
   ```
   會印出一段 JSON（`username`/`password`/`host`/`port`/`dbname`），照 `terraform output psql_connect_hint` 給的格式連線：
   ```powershell
   psql "host=<host> port=5432 dbname=manga_record user=manga_record_admin sslmode=require"
   ```
   （沒裝 `psql` 的話，`winget install PostgreSQL.PostgreSQL` 或用 pgAdmin 圖形介面連也可以）
4. 用完記得把 `my_ip_cidr` 註解掉、再 `apply` 一次關掉，不要一直開著

## 前置準備

### 1. 安裝 Terraform / AWS CLI

```powershell
winget install HashiCorp.Terraform
winget install Amazon.AWSCLI
terraform -version   # 1.7+ 都可以
```

### 2. 設定 AWS CLI profile

```powershell
aws configure --profile terraform-deploy
# Default region: us-east-1
```

### 3. 建立 `terraform.tfvars`

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

這個檔案已被 `.gitignore` 排除，不會被 commit。所有變數都有預設值，`my_ip_cidr` 平常留空（註解掉）即可，只有要臨時 `psql` 直連除錯時才需要填（見上方「手動 psql 直連 RDS 除錯」）。

## 執行

```powershell
terraform init       # 只有第一次或改動 provider 版本時需要
terraform plan        # 仔細看一遍要建什麼，尤其留意有沒有非預期的刪除/取代動作
terraform apply        # 確認沒問題後執行，會再問一次要不要繼續，輸入 yes
```

跑完會印出 `outputs.tf` 定義的值，包含 `ecr_repository_url`、`ec2_instance_id`、`backend_public_ip`。

基礎設施建好後，build/push image、部署、驗收流程見 [`backend/README.md`](../../backend/README.md#部署)。

## 銷毀重來

```powershell
terraform destroy
```

會把這裡管理的資源全部刪掉（VPC/RDS/EC2/Secrets/ECR/...），重新 `apply` 會是全新的一份。
