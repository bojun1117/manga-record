# Backend

FastAPI + SQLAlchemy + Alembic + PostgreSQL（RDS）。

## 本機設定

### 1. 建虛擬環境、裝套件

```powershell
cd manga-record\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> 如果 `Activate.ps1` 跳出「不允許執行指令碼」的錯誤，跑一次 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`（只需要設一次）。

### 2. 設定 `.env`

```powershell
Copy-Item .env.example .env
```

打開 `.env`：
- `DATABASE_URL`：host 用 `terraform output db_endpoint` 拿（在 `manga-record/infra/terraform/` 資料夾下跑），密碼從 Secrets Manager 拿（見 [`infra/terraform/README.md`](../infra/terraform/README.md#手動-psql-直連-rds-除錯)）
  ```
  DATABASE_URL=postgresql+psycopg://manga_record_admin:<密碼>@<host>:5432/manga_record?sslmode=require
  ```
- `JWT_SECRET`：`python -c "import secrets; print(secrets.token_urlsafe(48))"` 產生一組貼進去

### 3. 跑 migration

```powershell
alembic upgrade head
```

跑完用 `psql` 連進去跑 `\dt`，應該看到 `member` / `manga` / `member_manga`（外加 alembic 自己的 `alembic_version`）。

### 4. 啟動

```powershell
uvicorn app.main:app --reload
```

`http://localhost:8000/docs` 有 FastAPI 自動生成的互動文件，可以直接在網頁上測 API。`http://localhost:8000/health` 跟 `/health/db` 分別確認服務本身、資料庫連線正常，都應該回 `{"status": "ok"}`；`/health/db` 出錯通常是 `.env` 的 `DATABASE_URL` 打錯，或是 RDS 的 security group IP 規則過期（IP 換了就要回 `infra/terraform` 更新 `terraform.tfvars` 重新 apply）。

## API 使用

完整 endpoint 清單、request/response 結構、錯誤碼見 [`../docs/API.md`](../docs/API.md)；資料表結構見 [`../docs/DATA_MODEL.md`](../docs/DATA_MODEL.md)；認證機制見 [`../docs/AUTH.md`](../docs/AUTH.md)。

## 部署

後端 Docker 化，跑在 Terraform（見 [`infra/terraform`](../infra/terraform/README.md)）建好的 EC2 上。這個資料夾下有 `Dockerfile` / `.dockerignore`。

### 1. build + push image 到 ECR

```powershell
cd manga-record\infra\terraform
$ECR_REPO = terraform output -raw ecr_repository_url   # 格式: <account>.dkr.ecr.<region>.amazonaws.com/manga-record-dev-backend
$ECR_REGISTRY = $ECR_REPO.Split('/')[0]

cd ..\..\backend
aws ecr get-login-password --region us-east-1 --profile terraform-deploy | docker login --username AWS --password-stdin $ECR_REGISTRY
docker build -t "${ECR_REPO}:latest" .
docker push "${ECR_REPO}:latest"
```

（`--region` 對應 `infra/terraform/variables.tf` 的 `aws_region`，預設 `us-east-1`，改過的話這裡也要跟著改。）

### 2. 部署（第一次或之後每次要換新版 image）

用 SSM 連進 EC2（不用 SSH key）：

```powershell
$InstanceId = (terraform output -raw ec2_instance_id)  # 在 infra/terraform 資料夾下跑
aws ssm start-session --target $InstanceId --profile terraform-deploy
```

連進去之後（在 EC2 上，是 bash 不是 PowerShell）：

```bash
sudo /opt/manga-record/deploy.sh
tail -f /var/log/manga-record-deploy.log
```

腳本會自動：登入 ECR → 從 Secrets Manager 撈 `DATABASE_URL`/`JWT_SECRET` → pull 最新 image
→ 跑一次 `alembic upgrade head` → 換掉正在跑的 container。

### 3. 驗收

```powershell
$IP = terraform output -raw backend_public_ip   # infra/terraform 資料夾下
curl "http://${IP}:8000/health"
curl "http://${IP}:8000/health/db"
```

兩個都要回 `{"status":"ok"}`。

前端要接這個遠端後端測試的話，暫時把 `frontend/.env.development` 的
`VITE_API_BASE_URL` 改成 `http://<backend_public_ip>:8000` 就好（後端 CORS 已經是
`allow_origins=["*"]`，不用另外處理）。

### 4. CI/CD（GitHub Actions 自動部署）

上面 1、2 兩步已經自動化成 [`.github/workflows/deploy-backend.yml`](../.github/workflows/deploy-backend.yml)：
push 到 `main` 且改到 `backend/**`，就會自動 build image → push 到 ECR → 用 SSM 觸發
EC2 上的 `deploy.sh`（跟手動流程是同一支腳本，一樣會自動跑 migration）。也可以在
GitHub 的 Actions 分頁手動 `workflow_dispatch` 重跑一次。

換憑證用 GitHub OIDC（`infra/terraform/github_oidc.tf`），不用在 GitHub 存長期 AWS
access key。啟用步驟：

**a. apply 新增的 IAM 資源**

```powershell
cd manga-record\infra\terraform
terraform apply
terraform output -raw github_actions_role_arn
```

**b. 在 GitHub repo 設定 4 個 secrets**（Settings → Secrets and variables → Actions → New repository secret）：

| Secret 名稱 | 值 |
| --- | --- |
| `AWS_GITHUB_ACTIONS_ROLE_ARN` | 上一步 `terraform output -raw github_actions_role_arn` 的結果 |
| `AWS_REGION` | 對應 `variables.tf` 的 `aws_region`，預設 `us-east-1` |
| `ECR_REPOSITORY_URL` | `terraform output -raw ecr_repository_url` |
| `EC2_INSTANCE_ID` | `terraform output -raw ec2_instance_id` |

設定好之後，改 `backend/` 底下的程式碼、push 到 `main`，就會自動部署。想看部署結果去 repo 的 Actions 分頁看
`Deploy backend to EC2` 這個 workflow 的 log（`deploy.sh` 的 stdout/stderr 印在
`Trigger deploy on EC2 via SSM` 這個 step 裡）。
