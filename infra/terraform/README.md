# Terraform — 網路 / RDS / EC2 / CI 基礎設施

管理 manga-record 後端的 AWS 基礎設施：VPC、RDS（Postgres）、Secrets Manager、EC2、ECR、GitHub OIDC、CloudFront。

## 架構重點

- **RDS 在 private subnet**，`publicly_accessible` 關閉，security group 只信任 EC2 的 SG
- **EC2 維運走 AWS Session Manager**，不開 22 port
- DB 密碼、JWT secret、Anthropic API key 都存 **Secrets Manager**，EC2 用 IAM instance profile 讀取

## 模組結構

Root module（`main.tf`）只負責接線，實際資源分在 7 個 child module（`modules/`）。依賴方向無循環：`network`（VPC + 兩個 security group）→ `database` → `secrets` → `backend` → `{cicd, cdn}`。

- `modules/network`：VPC、subnet、route table、`aws_security_group.ec2`（對外開 `var.app_port`）、`aws_security_group.rds`（只信任 ec2 的 SG）
- `modules/database`：RDS Postgres instance
- `modules/secrets`：Secrets Manager（DB 連線字串、JWT secret、Anthropic API key）
- `modules/ecr`：後端 Docker image 的 ECR repo
- `modules/backend`：EC2 的 IAM role + 一台 EC2（Amazon Linux 2023）+ Elastic IP。開機時透過 `modules/backend/templates/user_data.sh.tpl` 裝好 docker/aws-cli/jq，並把 `/opt/manga-record/deploy.sh` 寫到機器上（換版時重跑的腳本；**只在機器第一次開機時寫入**，之後改 `user_data.sh.tpl` 不會自動同步到已存在的機器上，要手動重寫或換掉整台機器）
- `modules/cicd`：GitHub Actions 用的 OIDC provider + IAM role，權限鎖在「push 到 ECR」+「對 EC2 送 SSM SendCommand」
- `modules/cdn`：CloudFront，把 EC2 的裸 HTTP 包成 HTTPS

## 執行

```powershell
terraform init
terraform plan
terraform apply
```
