# Backend

FastAPI + SQLAlchemy + Alembic + PostgreSQL(RDS)。以下依 Phase 順序記錄本機設定與驗收步驟。

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

打開 `.env`，把 `DATABASE_URL` 換成真的值——host 用 `terraform output db_endpoint` 拿（在 `manga-record/infra/terraform/` 資料夾下跑），密碼用 Phase 1 那組從 Secrets Manager 拿到的密碼：

```
DATABASE_URL=postgresql+psycopg://manga_record_admin:<密碼>@<host>:5432/manga_record?sslmode=require
```

### 3. 跑 migration 建表

```powershell
alembic upgrade head
```

跑完之後回去用 `psql` 連進去跑 `\dt`，應該會看到 `member` / `manga` / `member_manga` 三張表（外加 alembic 自己用來記錄版本的 `alembic_version` 表）。

### 4. 啟動 FastAPI

```powershell
uvicorn app.main:app --reload
```

開瀏覽器打 `http://localhost:8000/health`，應該回：
```json
{"status": "ok"}
```

再打 `http://localhost:8000/health/db`，這個會真的透過 SQLAlchemy 對 RDS 送一個 `SELECT 1`：
```json
{"status": "ok"}
```

如果 `/health/db` 出錯，通常是 `.env` 裡的 `DATABASE_URL` 打錯（host/密碼/sslmode），或是 Phase 1 那個 security group 的 IP 規則過期了（你的 IP 換了，回 `infra/terraform` 更新 `terraform.tfvars` 重新 apply）。

## Phase 2 驗收：手動寫入一筆資料

打開 FastAPI 自動生成的文件 `http://localhost:8000/docs`，或直接用 `psql` 手動測試 insert：

```sql
INSERT INTO member (username, password_hash)
VALUES ('test_user', 'placeholder_not_a_real_hash');

SELECT * FROM member;
```

`id` 不用自己填，`bigserial` 會自動遞增。看到這筆資料能寫進去、查得出來，Phase 2 就算驗收通過。

## Phase 3（Auth）驗收

### 1. 補 `.env` 的 `JWT_SECRET`

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

貼進 `.env` 的 `JWT_SECRET`。

### 2. 裝新加的套件

```powershell
pip install -r requirements.txt
```

（多了 `bcrypt`、`pyjwt`）

### 3. 啟動、依序測試三個 endpoint

```powershell
uvicorn app.main:app --reload
```

開 `http://localhost:8000/docs`，會看到 FastAPI 自動生成的互動文件，可以直接在網頁上測，或用 `curl`：

> PowerShell 下 curl 的 `-d` 參數用**單引號**包 JSON，裡面的雙引號不用跳脫（跳脫寫法在 PowerShell 呼叫外部程式時常常被搞亂，見踩坑記錄）。

```powershell
# 註冊
curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" -d '{"username":"bojun","password":"at-least-8-chars"}'

# 登入，拿 token
curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"bojun","password":"at-least-8-chars"}'

# 帶 token 打受保護的 endpoint（把上一步拿到的 token 貼進去）
curl http://localhost:8000/auth/me -H "Authorization: Bearer <token>"
```

看到 `/auth/me` 正確回傳剛剛註冊的帳號資訊，Phase 3 就算驗收通過。也可以試著故意帶錯密碼登入（應該回 401）、不帶 token 打 `/auth/me`（應該回 401）確認錯誤處理正常。

## Phase 4（Manga + Collection CRUD）驗收

### 1. 裝新加的套件

```powershell
pip install -r requirements.txt
```

（多了 `opencc-python-reimplemented`，繁簡正規化用）

### 2. 完整流程測試

先登入拿一個 token（沿用上面 Phase 3 的帳號），下面把 `<token>` 換成實際值：

```powershell
$token = "<token>"
$q = [uri]::EscapeDataString("咒術迴戰")   # 中文查詢字串一定要 URL 編碼，見前面踩坑記錄

# 搜尋一部還沒人建過的漫畫，應該回空陣列 []（這不是錯誤，代表要新建）
curl "http://localhost:8000/manga/search?q=$q" -H "Authorization: Bearer $token"

# 新增收藏：mangaName 沒對應到現有 manga，後端會自動新建一筆
curl -X POST http://localhost:8000/collections -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d '{"mangaName":"咒術迴戰","category":"hot_blooded","status":"reading","currentChapter":50}'

# 再搜尋一次同一個名字，這次應該查得到剛剛建的那筆
curl "http://localhost:8000/manga/search?q=$q" -H "Authorization: Bearer $token"

# 列出我的收藏
curl http://localhost:8000/collections -H "Authorization: Bearer $token"

# PATCH 更新進度（把上面回傳的 collection id 換進網址）
curl -X PATCH http://localhost:8000/collections/1 -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d '{"currentChapter":51}'

# 刪除
curl -X DELETE http://localhost:8000/collections/1 -H "Authorization: Bearer $token"
```

### 3. 驗證繁簡通用

用「进击」（簡體）搜尋用「進擊」（繁體）新增的漫畫，應該也查得到——這是 `normalize_chinese` 在起作用。

### 4. 驗證重複收藏會擋下來

對同一個 `mangaName` 呼叫兩次 `POST /collections`，第二次應該回 `409 ALREADY_IN_COLLECTION`，不是建出第二筆重複資料。

全部測完沒問題，Phase 4 就算驗收通過。

## 下一步 Phase 5 才會做的事

前端（Vue3）還沒開始寫，目前只能用 curl / `/docs` 測後端。

## Phase 6 部署

把後端 Docker 化、上 ECR、跑在 Terraform（見 [`infra/terraform`](../infra/terraform/README.md)）
建好的 EC2 上。這個資料夾下已經有 `Dockerfile` / `.dockerignore`。

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

### 2. 第一次部署(或之後每次要換新版 image)

用 SSM 連進 EC2(不用 SSH key)：

```powershell
$InstanceId = (terraform output -raw ec2_instance_id)  # 在 infra/terraform 資料夾下跑
aws ssm start-session --target $InstanceId --profile terraform-deploy
```

連進去之後(在 EC2 上，是 bash 不是 PowerShell)：

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

兩個都要回 `{"status":"ok"}`——`/health/db` 這個確認的是 EC2 上的 container 真的連得到
現在搬進 private subnet 的 RDS。

前端要接這個遠端後端測試的話，暫時把 `frontend/.env.development` 的
`VITE_API_BASE_URL` 改成 `http://<backend_public_ip>:8000` 就好（後端 CORS 已經是
`allow_origins=["*"]`,不用另外處理）。
