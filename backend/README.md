# Backend

FastAPI + SQLAlchemy + Alembic + PostgreSQL（正式環境是 EC2 上的 Docker 容器，見 infra/terraform/README.md）。

## 架構

```
app/
├── api/          # Router，request/response 邊界
├── service/      # 商業邏輯
├── repository/   # 資料庫存取（SQLAlchemy）
├── model/        # ORM model
├── schema/       # Pydantic request/response schema
├── core/         # 設定、DB session、共用錯誤、中文正規化
└── integration/  # 外部服務（Anthropic Claude）
```

## 測試

```bash
pip install -r requirements-dev.txt

# 只跑純邏輯測試（不需要資料庫）
python -m pytest

# 連資料庫測試一起跑：指向一個「名稱含 test」的 PostgreSQL 資料庫（測試會清空並重建所有資料表）
TEST_DATABASE_URL=postgresql+psycopg://<user>:<password>@localhost:5432/manga_record_test python -m pytest
```

測試不會呼叫 Anthropic API，AI 的部分都用假資料取代。
