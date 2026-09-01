# Terraform — Phase 1（VPC + RDS + Secrets Manager）+ Phase 6（EC2 + ECR + CI/CD）

Phase 1 只建網路骨架跟資料庫。Phase 6 在同一份 state 裡加上 EC2/ECR，並把 Phase 1 那個
暫時性的取捨收掉；後來又加了 GitHub OIDC role，讓 GitHub Actions 能自動部署後端。

## Phase 1 做過的暫時性取捨（Phase 6 已經收掉）

RDS 曾經暫時放在 **public subnet** 並開放 **你自己的 IP** 直連 5432，方便還沒建 EC2 之前
就能用 `psql` 驗收。Phase 6 起：
1. RDS 搬進 private subnet（`rds.tf` 的 `aws_db_subnet_group.main`）
2. `publicly_accessible` 關掉
3. `security_group.tf` 的 `aws_security_group.rds` 只信任 EC2 的 security group，不再對任何外部 IP 開放

---

## Phase 6 新增了什麼

- `ecr.tf`：放後端 Docker image 的 ECR repo（`aws_ecr_repository.backend`），
  外加一個生命週期規則清掉沒 tag 的舊 image
- `iam.tf`：EC2 用的 IAM role，掛了三個權限——`AmazonSSMManagedInstanceCore`（SSM
  連線用）、`AmazonEC2ContainerRegistryReadOnly`（pull image）、自訂的
  `secretsmanager:GetSecretValue`（只給兩個 secret 的 ARN，不用萬用字元）
- `ec2.tf`：一台 EC2（Amazon Linux 2023）+ 一個固定的 Elastic IP。開機時透過
  `templates/user_data.sh.tpl` 裝好 docker/aws-cli/jq，並把 `/opt/manga-record/deploy.sh`
  寫到機器上——這支腳本就是之後每次要換新版 image 時要重跑的東西
- `security_group.tf`：新增 `aws_security_group.ec2`（對外開 `var.app_port`，預設 `8000`），
  RDS 的 security group 改成只信任這個 SG
- `github_oidc.tf`：GitHub Actions 用的 OIDC provider + IAM role，權限鎖在「push 到
  `ecr.tf` 這個 repo」+「對 `ec2.tf` 這台 instance 送 SSM SendCommand」兩件事，信任範圍
  只限 `var.github_repo`（預設 `bojun1117/manga-record`）的 `main` 分支。設定步驟見
  [`backend/README.md` 的 CI/CD 段落](../../backend/README.md#4-cicdgithub-actions-自動部署)

### 維運方式：SSM，不開 22 port

這台 EC2 沒有 SSH key pair，也沒開 22 port。要連進去（部署新版 image、看 log、除錯）用
AWS 內建的 Session Manager：

```powershell
aws ssm start-session --target <ec2_instance_id> --profile terraform-deploy
```

`<ec2_instance_id>` 從 `terraform output ec2_instance_id` 拿。連進去之後：

```bash
sudo /opt/manga-record/deploy.sh
tail -f /var/log/manga-record-deploy.log   # 看上次部署的 log
```

### RDS 現在連不到本機了，這是預期行為

`my_ip_cidr` 這個變數 Phase 6 起預設留空，`aws_security_group_rule.rds_debug` 也就不會建立，
`terraform output psql_connect_hint` 印出來的指令平常連不上。真的需要用 `psql` 直連除錯時：

1. `terraform.tfvars` 取消註解 `my_ip_cidr`，填上目前的 IP（`curl -s https://checkip.amazonaws.com`）
2. `terraform plan` 看一下（應該只多一條 ingress 規則）、`apply`
3. 用完記得把 `my_ip_cidr` 註解掉、再 `apply` 一次關掉，不要一直開著

---

## 前置準備（在你自己的電腦上）

### 1. 安裝 Terraform

```powershell
winget install HashiCorp.Terraform
terraform -version   # 確認裝好，1.7+ 都可以
```

### 2. 安裝 AWS CLI（如果還沒裝）

```powershell
winget install Amazon.AWSCLI
aws --version
```

### 3. 設定一組 AWS CLI profile 給 Terraform 用

這階段先沿用你現有的 `cdk-deploy`（admin 權限，之前建 comic-vibe 時用的那組）就好，不用急著建新的最小權限身份——那件事排在 Phase 8 一起處理（見主計畫文件）。

```powershell
aws configure --profile terraform-deploy
# AWS Access Key ID / Secret Access Key：貼你 cdk-deploy 的那組
# Default region: us-east-1
```

### 4. 建立 `terraform.tfvars`

在這個資料夾（`manga-record/infra/terraform/`）複製一份：

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

這個檔案已經被 `.gitignore` 排除，不會被 commit。Phase 6 起所有變數都有預設值，
`my_ip_cidr` 平常留空（註解掉）就好，不填也能直接 apply——只有要臨時 `psql` 直連除錯時
才需要填（查法：`curl -s https://checkip.amazonaws.com`，見上面「RDS 現在連不到本機了」
那段）。

---

## 執行

都準備好之後，在這個資料夾下依序跑：

```powershell
terraform init      # 下載 provider，只有第一次或改動 provider 版本時需要
terraform plan       # 看它「打算」建什麼，仔細看一遍，確認資源數量、有沒有意外的東西
```

`plan` 的輸出貼給我看一次，我們一起確認沒問題（尤其留意有沒有出現非預期要刪除或取代既有資源的動作），沒問題再跑：

```powershell
terraform apply      # 會再問一次要不要繼續，輸入 yes
```

跑完後 Terraform 會印出 `outputs.tf` 定義的值，包含 `ecr_repository_url`、
`ec2_instance_id`、`backend_public_ip`。

---

## Phase 6 驗收：build/push image、部署、打通後端

Terraform apply 完只是把基礎設施建好，EC2 上還沒有真的能跑的 image。完整的
build → push → deploy → 驗收流程寫在 [`backend/README.md`](../../backend/README.md#phase-6-部署)。

---

## （歷史記錄）Phase 1 驗收：本機用 psql 連上 RDS

這是 Phase 1 剛建好 RDS、EC2 還不存在時的驗收方式，當時 RDS 還開在 public subnet。
Phase 6 起 RDS 預設不對外開放，下面這組指令要先照「RDS 現在連不到本機了」那段臨時打開
`my_ip_cidr` 才連得上：

密碼沒有直接印在 output 裡（避免留在 terminal 歷史紀錄），要另外從 Secrets Manager 拿：

```powershell
aws secretsmanager get-secret-value `
  --secret-id manga-record/dev/db-credentials `
  --profile terraform-deploy `
  --query SecretString --output text
```

會印出一段 JSON（`username`/`password`/`host`/`port`/`dbname`），照著 `terraform output psql_connect_hint` 給的指令格式連線（沒裝 `psql` 的話，`winget install PostgreSQL.PostgreSQL` 或用 pgAdmin 的圖形介面連也可以，把 host/port/user/password/dbname 對應填進去即可）：

```powershell
psql "host=<上面拿到的host> port=5432 dbname=manga_record user=manga_record_admin sslmode=require"
```

---

## 之後想銷毀重來

```powershell
terraform destroy
```

會把這階段建的東西全部刪掉（VPC/RDS/Secrets），重新 `apply` 就會是全新的一份。
