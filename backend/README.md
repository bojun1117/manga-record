# Backend

FastAPI + SQLAlchemy + Alembic + PostgreSQL（RDS）。

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
